use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
use workflow_harness::contract::{OptionPlan, Usage};
use workflow_harness::control::{Adapter, Message, Recovery};
use workflow_harness::control::{Cancellation, Capabilities, Continuation, Event, EventKind};
use workflow_harness::session::{ProcessAdapter, Session};
use workflow_harness::stream::StreamAdapter;
use workflow_harness::{Decision, Invocation, Response, Role, Runtime, Task};

static NEXT: AtomicUsize = AtomicUsize::new(0);

struct RecoveryOnly(Response);

struct RejectedBeforeStart;
impl Adapter for RejectedBeforeStart {
    fn capabilities(&self) -> Capabilities {
        capabilities()
    }
    fn invoke(&mut self, _: &Invocation) -> Result<(), String> {
        Err("capacity rejected before start".into())
    }
    fn next(&mut self) -> Result<Message, String> {
        panic!("no backend started")
    }
    fn continue_work(&mut self, _: &Continuation) -> Result<(), String> {
        panic!("no backend started")
    }
    fn cancel(&mut self, _: usize) -> Result<Cancellation, String> {
        Ok(Cancellation::Unsupported)
    }
    fn recover(&mut self, invocation_id: usize) -> Result<Recovery, String> {
        Ok(Recovery::NotStartedConfirmed {
            invocation_id,
            evidence: "Host rejected this exact attempt before start".into(),
        })
    }
}

#[test]
fn not_started_recovery_can_preserve_and_retry_same_work() {
    let d = Directory::new();
    let mut s = Session::create(d.task(), &d.0.join("run")).unwrap();
    let owner = s.request().unwrap();
    s.begin_execution(capabilities()).unwrap();
    s.event(event(
        owner.invocation_id,
        1,
        EventKind::Usage {
            total: Usage {
                model_tokens: Some(3),
                ..Default::default()
            },
        },
    ))
    .unwrap();
    s.event(event(
        owner.invocation_id,
        2,
        EventKind::Stopped {
            effects_settled: true,
        },
    ))
    .unwrap();
    s.accept(d.response(&owner, Decision::Work)).unwrap();
    let original = s.request().unwrap();
    assert!(s.drive(&mut RejectedBeforeStart).is_err());
    assert!(matches!(
        s.recover_backend(&mut RejectedBeforeStart).unwrap(),
        Recovery::NotStartedConfirmed { .. }
    ));
    let before = serde_json::to_value(&s.runtime).unwrap();
    let usage = s.runtime.cumulative_usage().unwrap();
    drop(s);
    let mut s = Session::open(&d.0.join("run")).unwrap();
    let retry = s
        .retry_not_started(original.invocation_id)
        .expect("confirmed unstarted work needs a recovery path");
    assert_ne!(retry.invocation_id, original.invocation_id);
    assert_eq!(s.retry_origin(), Some(original.invocation_id));
    assert_eq!(s.runtime.cumulative_usage().unwrap(), usage);
    let after = serde_json::to_value(&s.runtime).unwrap();
    for key in [
        "task",
        "assignment",
        "actual_use",
        "history",
        "segment",
        "executions",
    ] {
        assert_eq!(before[key], after[key], "{key}");
    }
    assert!(s.retry_not_started(original.invocation_id).is_err());
    s.verify_queued_context(&retry).unwrap();
}

struct ReplyAdapter {
    recovery: Recovery,
    accepted: bool,
}
impl Adapter for ReplyAdapter {
    fn capabilities(&self) -> Capabilities {
        capabilities()
    }
    fn invoke(&mut self, _: &Invocation) -> Result<(), String> {
        if self.accepted {
            Ok(())
        } else {
            Err("rejected".into())
        }
    }
    fn next(&mut self) -> Result<Message, String> {
        Err("response lost".into())
    }
    fn continue_work(&mut self, _: &Continuation) -> Result<(), String> {
        panic!("must not continue")
    }
    fn cancel(&mut self, _: usize) -> Result<Cancellation, String> {
        Ok(Cancellation::Unsupported)
    }
    fn recover(&mut self, _: usize) -> Result<Recovery, String> {
        Ok(self.recovery.clone())
    }
}

fn queued_worker(d: &Directory) -> (Session, Invocation) {
    let mut s = Session::create(d.task(), &d.0.join("run")).unwrap();
    let owner = s.request().unwrap();
    s.accept(d.response(&owner, Decision::Work)).unwrap();
    let worker = s.request().unwrap();
    (s, worker)
}

#[test]
fn unknown_unscoped_and_stale_recoveries_never_authorize_retry() {
    let d = Directory::new();
    let (mut s, first) = queued_worker(&d);
    assert!(s.drive(&mut RejectedBeforeStart).is_err());
    for recovery in [
        Recovery::Unknown,
        Recovery::Unsupported,
        Recovery::NotStarted,
    ] {
        s.recover_backend(&mut ReplyAdapter {
            recovery,
            accepted: false,
        })
        .unwrap();
        assert!(s.retry_not_started(first.invocation_id).is_err());
    }
    s.recover_backend(&mut RejectedBeforeStart).unwrap();
    let second = s.retry_not_started(first.invocation_id).unwrap();
    assert!(s.drive(&mut RejectedBeforeStart).is_err());
    let stale = Recovery::NotStartedConfirmed {
        invocation_id: first.invocation_id,
        evidence: "Old call failed".into(),
    };
    assert!(
        s.recover_backend(&mut ReplyAdapter {
            recovery: stale,
            accepted: false
        })
        .is_err()
    );
    assert!(s.retry_not_started(second.invocation_id).is_err());
    s.recover_backend(&mut RejectedBeforeStart).unwrap();
    let third = s.retry_not_started(second.invocation_id).unwrap();
    assert!(third.invocation_id > second.invocation_id);
    assert_eq!(s.retry_origin(), Some(first.invocation_id));
}

#[test]
fn accepted_running_or_event_evidence_rejects_not_started_and_transport_switches() {
    for proof in ["accepted", "running", "event"] {
        let d = Directory::new();
        let (mut s, request) = queued_worker(&d);
        let mut adapter = ReplyAdapter {
            recovery: Recovery::Running,
            accepted: proof == "accepted",
        };
        assert!(s.drive(&mut adapter).is_err());
        if proof == "running" {
            s.recover_backend(&mut adapter).unwrap();
        }
        if proof == "event" {
            s.event(event(
                request.invocation_id,
                1,
                EventKind::Progress {
                    summary: "Work ran".into(),
                    evidence: vec![],
                },
            ))
            .unwrap();
        }
        assert!(s.recover_backend(&mut RejectedBeforeStart).is_err());
        assert!(s.retry_not_started(request.invocation_id).is_err());
        assert!(
            s.bind_host(workflow_harness::session::HostBinding {
                invocation_id: request.invocation_id,
                backend_handle: "another-transport".into()
            })
            .is_err()
        );
        assert!(
            s.prepare_host_dispatch(request.invocation_id, "other-call".into())
                .is_err()
        );
        assert!(
            s.invoke(&ProcessAdapter {
                program: "/bin/false".into(),
                args: vec![]
            })
            .is_err()
        );
        drop(s);
        let mut s = Session::open(&d.0.join("run")).unwrap();
        assert!(s.recover_backend(&mut RejectedBeforeStart).is_err());
    }
}

fn host_report(
    id: usize,
    call: &str,
    outcome: workflow_harness::control::HostDispatchOutcome,
) -> workflow_harness::control::HostDispatch {
    workflow_harness::control::HostDispatch {
        invocation_id: id,
        call_id: call.into(),
        outcome,
    }
}

#[test]
fn prepared_native_call_survives_lost_response_and_blocks_duplicate_transports() {
    use workflow_harness::control::HostDispatchOutcome as Outcome;
    let d = Directory::new();
    let (mut s, request) = queued_worker(&d);
    s.prepare_host_dispatch(request.invocation_id, "host-request-1".into())
        .unwrap();
    assert!(
        s.prepare_host_dispatch(request.invocation_id, "host-request-2".into())
            .is_err()
    );
    assert!(s.drive(&mut RejectedBeforeStart).is_err());
    assert!(
        s.invoke(&ProcessAdapter {
            program: "/bin/false".into(),
            args: vec![]
        })
        .is_err()
    );
    assert!(s.begin_execution(capabilities()).is_err());
    assert!(
        s.bind_host(workflow_harness::session::HostBinding {
            invocation_id: request.invocation_id,
            backend_handle: "invented".into()
        })
        .is_err()
    );
    assert!(s.accept(d.response(&request, Decision::Observed)).is_err());
    assert!(
        s.replace_queued_work("Bypass uncertain work".into())
            .is_err()
    );
    assert!(s.retry_not_started(request.invocation_id).is_err());
    drop(s);
    let mut s = Session::open(&d.0.join("run")).unwrap();
    assert_eq!(s.host_dispatch().unwrap().call_id, "host-request-1");
    s.reconcile_host_dispatch(host_report(
        request.invocation_id,
        "host-request-1",
        Outcome::Unknown {
            evidence: "Host lookup inconclusive".into(),
        },
    ))
    .unwrap();
    assert!(s.retry_not_started(request.invocation_id).is_err());
    // The host later finds the original handle; no new Agent is created.
    let accepted = host_report(
        request.invocation_id,
        "host-request-1",
        Outcome::Accepted {
            backend_handle: "original-agent".into(),
        },
    );
    s.reconcile_host_dispatch(accepted.clone()).unwrap();
    s.reconcile_host_dispatch(accepted).unwrap();
    assert!(
        s.reconcile_host_dispatch(host_report(
            request.invocation_id,
            "host-request-1",
            Outcome::NotStarted {
                evidence: "Contradictory stale report".into()
            }
        ))
        .is_err()
    );
    assert!(
        s.accept_host_return("different-agent", d.response(&request, Decision::Observed))
            .is_err()
    );
    drop(s);
    let mut s = Session::open(&d.0.join("run")).unwrap();
    assert_eq!(
        s.host_binding().unwrap().unwrap().backend_handle,
        "original-agent"
    );
    s.begin_execution(capabilities()).unwrap();
    s.event(event(
        request.invocation_id,
        1,
        EventKind::Stopped {
            effects_settled: true,
        },
    ))
    .unwrap();
    s.accept_host_return("original-agent", d.response(&request, Decision::Observed))
        .unwrap();
    assert_eq!(s.request().unwrap().role, Role::Coordinator);
    assert_eq!(s.host_dispatch_history().len(), 1);
}

#[test]
fn native_not_started_is_final_for_one_attempt_and_cannot_clear_the_next() {
    use workflow_harness::control::HostDispatchOutcome as Outcome;
    let d = Directory::new();
    let (mut s, request) = queued_worker(&d);
    s.prepare_host_dispatch(request.invocation_id, "first".into())
        .unwrap();
    let rejected = host_report(
        request.invocation_id,
        "first",
        Outcome::NotStarted {
            evidence: "Host confirms rejection before creation".into(),
        },
    );
    s.reconcile_host_dispatch(rejected.clone()).unwrap();
    assert!(
        s.reconcile_host_dispatch(host_report(
            request.invocation_id,
            "first",
            Outcome::Accepted {
                backend_handle: "contradiction".into()
            }
        ))
        .is_err()
    );
    drop(s);
    let mut s = Session::open(&d.0.join("run")).unwrap();
    let next = s.retry_not_started(request.invocation_id).unwrap();
    assert_eq!(s.retry_origin(), Some(request.invocation_id));
    assert!(
        s.prepare_host_dispatch(next.invocation_id, "first".into())
            .is_err()
    );
    s.prepare_host_dispatch(next.invocation_id, "second".into())
        .unwrap();
    assert!(s.reconcile_host_dispatch(rejected).is_err());
    assert!(s.retry_not_started(next.invocation_id).is_err());
    assert_eq!(s.host_dispatch_history().len(), 2);
}

#[test]
fn dispatch_checkpoint_and_journal_failures_do_not_create_replay_permission() {
    use workflow_harness::control::HostDispatchOutcome as Outcome;
    let d = Directory::new();
    let run = d.0.join("run");
    let (mut s, request) = queued_worker(&d);
    fs::create_dir(run.join("state.next.json")).unwrap();
    assert!(
        s.prepare_host_dispatch(request.invocation_id, "not-published".into())
            .is_err()
    );
    assert!(s.host_dispatch().is_none());
    fs::remove_dir(run.join("state.next.json")).unwrap();
    fs::rename(run.join("events.jsonl"), run.join("events.saved")).unwrap();
    fs::create_dir(run.join("events.jsonl")).unwrap();
    assert!(
        s.prepare_host_dispatch(request.invocation_id, "published".into())
            .is_err()
    );
    assert_eq!(s.host_dispatch().unwrap().call_id, "published");
    drop(s);
    let mut s = Session::open(&run).unwrap();
    assert!(
        s.prepare_host_dispatch(request.invocation_id, "repeated".into())
            .is_err()
    );
    let report = host_report(
        request.invocation_id,
        "published",
        Outcome::Accepted {
            backend_handle: "already-created".into(),
        },
    );
    assert!(s.reconcile_host_dispatch(report.clone()).is_err());
    drop(s);
    let mut s = Session::open(&run).unwrap();
    assert_eq!(
        s.host_binding().unwrap().unwrap().backend_handle,
        "already-created"
    );
    s.reconcile_host_dispatch(report).unwrap();
    assert!(s.retry_not_started(request.invocation_id).is_err());
}

#[test]
fn failed_retry_publication_preserves_confirmed_attempt_for_cold_recovery() {
    let d = Directory::new();
    let run = d.0.join("run");
    let (mut s, request) = queued_worker(&d);
    assert!(s.drive(&mut RejectedBeforeStart).is_err());
    s.recover_backend(&mut RejectedBeforeStart).unwrap();
    let before = fs::read(run.join("state.json")).unwrap();
    fs::rename(run.join("events.jsonl"), run.join("events.saved")).unwrap();
    fs::create_dir(run.join("events.jsonl")).unwrap();
    assert!(s.retry_not_started(request.invocation_id).is_err());
    assert_eq!(fs::read(run.join("state.json")).unwrap(), before);
    drop(s);
    let mut s = Session::open(&run).unwrap();
    assert_eq!(
        s.runtime.outstanding().unwrap().invocation_id,
        request.invocation_id
    );
    fs::remove_dir(run.join("events.jsonl")).unwrap();
    fs::rename(run.join("events.saved"), run.join("events.jsonl")).unwrap();
    assert!(s.retry_not_started(request.invocation_id).is_ok());
}

fn host_cli(d: &Directory, command: &str, input: serde_json::Value) -> std::process::Output {
    use std::io::Write;
    use std::process::{Command, Stdio};
    let mut child = Command::new(env!("CARGO_BIN_EXE_workflow-harness"))
        .args(["host", command])
        .arg(d.0.join("run"))
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(input.to_string().as_bytes())
        .unwrap();
    child.wait_with_output().unwrap()
}

#[test]
fn host_cli_stream_spawn_failure_recovery_and_explicit_retry_complete_once() {
    let d = Directory::new();
    let (s, original) = queued_worker(&d);
    drop(s);
    let invalid = d.0.join("not-executable");
    fs::write(&invalid, "This fixture cannot start a process").unwrap();
    let config = serde_json::json!({"process":{"program":invalid}, "capabilities":capabilities()});
    assert!(!host_cli(&d, "drive", config.clone()).status.success());
    let recovered = host_cli(&d, "recover", config);
    assert!(
        recovered.status.success(),
        "{}",
        String::from_utf8_lossy(&recovered.stderr)
    );
    let output: serde_json::Value = serde_json::from_slice(&recovered.stdout).unwrap();
    assert_eq!(output["recovery"]["status"], "not_started_confirmed");
    assert_eq!(output["recovery"]["invocation_id"], original.invocation_id);
    let retried = host_cli(
        &d,
        "retry-not-started",
        serde_json::json!(original.invocation_id),
    );
    assert!(
        retried.status.success(),
        "{}",
        String::from_utf8_lossy(&retried.stderr)
    );
    let retry: Invocation = serde_json::from_slice(&retried.stdout).unwrap();
    let messages = d.0.join("backend-messages.jsonl");
    fs::write(&messages, format!("{}\n{}\n",
        serde_json::json!({"message":"event","event":event(retry.invocation_id, 1, EventKind::Stopped { effects_settled:true })}),
        serde_json::json!({"message":"return","response":d.response(&retry, Decision::Observed)})
    )).unwrap();
    let working = serde_json::json!({"process":{"program":"/bin/sh","args":["-c","read -r invocation; cat \"$1\"","fixture",messages]}, "capabilities":capabilities()});
    let completed = host_cli(&d, "drive", working);
    assert!(
        completed.status.success(),
        "{}",
        String::from_utf8_lossy(&completed.stderr)
    );
    let next: Invocation = serde_json::from_slice(&completed.stdout).unwrap();
    assert_eq!(next.role, Role::Coordinator);
    assert!(
        !host_cli(
            &d,
            "retry-not-started",
            serde_json::json!(original.invocation_id)
        )
        .status
        .success()
    );
    assert!(
        d.0.join(format!(
            "run/stream-{}/not-started.json",
            original.invocation_id
        ))
        .is_file()
    );
    assert!(
        d.0.join(format!("run/stream-{}/terminal.json", retry.invocation_id))
            .is_file()
    );
}

#[test]
fn host_cli_native_prepare_lookup_and_bound_return_use_original_call() {
    let d = Directory::new();
    let (s, request) = queued_worker(&d);
    drop(s);
    let prepared = host_cli(
        &d,
        "prepare-dispatch",
        serde_json::json!({"invocation_id":request.invocation_id,"call_id":"host-supported-key"}),
    );
    assert!(prepared.status.success());
    let status = host_cli(&d, "status", serde_json::Value::Null);
    let state: serde_json::Value = serde_json::from_slice(&status.stdout).unwrap();
    assert_eq!(state["host_dispatch"]["outcome"]["status"], "unknown");
    let report = serde_json::json!({"invocation_id":request.invocation_id,"call_id":"host-supported-key", "outcome":{"status":"accepted","backend_handle":"original-handle"}});
    assert!(host_cli(&d, "reconcile-dispatch", report).status.success());
    assert!(
        host_cli(&d, "begin", serde_json::to_value(capabilities()).unwrap())
            .status
            .success()
    );
    assert!(host_cli(&d, "event", serde_json::json!({"backend_handle":"original-handle", "event":event(request.invocation_id, 1, EventKind::Stopped { effects_settled:true })})).status.success());
    let returned = host_cli(
        &d,
        "return",
        serde_json::json!({"backend_handle":"original-handle","response":d.response(&request, Decision::Observed)}),
    );
    assert!(
        returned.status.success(),
        "{}",
        String::from_utf8_lossy(&returned.stderr)
    );
    assert_eq!(
        serde_json::from_slice::<Invocation>(&returned.stdout)
            .unwrap()
            .role,
        Role::Coordinator
    );
}
impl Adapter for RecoveryOnly {
    fn capabilities(&self) -> Capabilities {
        capabilities()
    }
    fn invoke(&mut self, _: &Invocation) -> Result<(), String> {
        panic!("recovery must not invoke")
    }
    fn next(&mut self) -> Result<Message, String> {
        panic!("recovery must not poll")
    }
    fn continue_work(&mut self, _: &Continuation) -> Result<(), String> {
        panic!("recovery must not continue")
    }
    fn cancel(&mut self, _: usize) -> Result<Cancellation, String> {
        Ok(Cancellation::Unsupported)
    }
    fn recover(&mut self, _: usize) -> Result<Recovery, String> {
        Ok(Recovery::Terminal {
            response: Box::new(self.0.clone()),
            effects_settled: true,
        })
    }
}

#[test]
fn wrong_recovered_terminal_cannot_settle_another_pending_invocation() {
    let d = Directory::new();
    let path = d.0.join("run");
    let mut session = Session::create(d.task(), &path).unwrap();
    let coordinator = session.request().unwrap();
    session
        .accept(d.response(&coordinator, Decision::Work))
        .unwrap();
    let worker = session.request().unwrap();
    session.begin_execution(capabilities()).unwrap();
    let before = fs::read(path.join("state.json")).unwrap();
    for wrong_role in [false, true] {
        let mut response = d.response(&worker, Decision::Observed);
        if wrong_role {
            response.role = Role::Coordinator;
        } else {
            response.invocation_id += 1;
        }
        assert!(
            session
                .recover_backend(&mut RecoveryOnly(response))
                .is_err()
        );
        assert_eq!(before, fs::read(path.join("state.json")).unwrap());
        assert!(!session.runtime.execution().unwrap().stopped);
    }
}
struct Directory(PathBuf);
impl Directory {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "workflow-control-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).unwrap();
        fs::write(
            path.join("method.txt"),
            "Actual supplied role method for a mechanical test.\n",
        )
        .unwrap();
        Self(path)
    }
    fn task(&self) -> Task {
        serde_json::from_value(serde_json::json!({
            "objective":"Mechanical contract verification", "workspace":self.0,
            "constraints":"No external effects", "invocation_limit":20,
            "sources":[{"path":"method.txt","first_line":1,"last_line":1,"purpose":"method","roles":["coordinator","resolver","worker"]}],
            "research":{"question":"Does control preserve the selected commitment?", "missing_observation":"actual boundary behavior", "rationale":"Avoid hidden repeated support",
                "remaining_work":[{"work":"Obtain one bounded observation","estimate":{},"condition":""}],
                "roles":[
                    {"role":"coordinator","method_source":0,"required_purposes":["method"],"write_scope":"Adoption only","fresh_context":true},
                    {"role":"resolver","method_source":0,"required_purposes":["method"],"write_scope":"Recommendation only","fresh_context":true},
                    {"role":"worker","method_source":0,"required_purposes":["method"],"write_scope":"Temporary test outputs","fresh_context":true}
                ]}
        })).unwrap()
    }
    fn response(&self, request: &Invocation, decision: Decision) -> Response {
        serde_json::from_value(serde_json::json!({"invocation_id":request.invocation_id,"role":request.role,"decision":decision,
            "summary":"Mechanical evidence only", "assignment":"Read one source and return before expansion", "evidence":[self.0.join("method.txt")],
            "update":{"remaining_work":[],"interpretation":"The preceding result supports this bounded choice; no optimization claim",
                "rationale":"The selected next observation still distinguishes the possibilities", "reverse_when":"A new required dependency changes the remaining path",
                "segment":{"observation":"One native observation", "return_when":"Before expanding beyond that observation","model_tokens":10}}
        })).unwrap()
    }
    fn worker(&self) -> (Runtime, Invocation) {
        let mut runtime = Runtime::new(self.task()).unwrap();
        let request = runtime.request().unwrap();
        runtime
            .accept(self.response(&request, Decision::Work))
            .unwrap();
        let request = runtime.request().unwrap();
        assert_eq!(request.role, Role::Worker);
        runtime.begin_execution(capabilities()).unwrap();
        (runtime, request)
    }
}
impl Drop for Directory {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.0).unwrap();
    }
}

fn capabilities() -> Capabilities {
    Capabilities {
        events: true,
        controlled_continuation: true,
        cooperative_cancel: false,
        recovery: true,
        fresh_context: true,
        isolation: "Mechanical fixture; no isolation claim".into(),
    }
}
fn event(id: usize, sequence: u64, event: EventKind) -> Event {
    Event {
        invocation_id: id,
        sequence,
        event,
    }
}
fn boundary(due: bool) -> EventKind {
    EventKind::Boundary {
        reason: "Selected observation reached".into(),
        return_due: due,
        effects_settled: true,
    }
}

#[test]
fn missing_role_input_and_unsupported_backend_fail_before_dispatch() {
    let d = Directory::new();
    let mut task = d.task();
    task.research.as_mut().unwrap().roles[2]
        .required_purposes
        .push("missing observation".into());
    assert!(Runtime::new(task).is_err());
    let mut runtime = Runtime::new(d.task()).unwrap();
    let request = runtime.request().unwrap();
    assert!(
        request
            .prompt
            .contains("Current role method; source index 0")
    );
    assert!(request.prompt.contains("Actual supplied role method"));
    runtime
        .accept(d.response(&request, Decision::Work))
        .unwrap();
    runtime.request().unwrap();
    let mut caps = capabilities();
    caps.controlled_continuation = false;
    assert!(runtime.begin_execution(caps).is_err());
    assert!(runtime.execution().is_none());
}

#[test]
fn ordinary_step_continues_without_an_extra_role_but_return_due_survives_recovery() {
    let d = Directory::new();
    let (mut runtime, worker) = d.worker();
    runtime
        .event(event(worker.invocation_id, 1, boundary(false)))
        .unwrap();
    assert_eq!(runtime.continuation().unwrap(), Continuation::Continue);
    runtime
        .event(event(worker.invocation_id, 2, boundary(true)))
        .unwrap();
    assert!(matches!(
        runtime.continuation().unwrap(),
        Continuation::Return { .. }
    ));
    runtime
        .event(event(
            worker.invocation_id,
            3,
            EventKind::Stopped {
                effects_settled: true,
            },
        ))
        .unwrap();
    runtime
        .accept(d.response(&worker, Decision::Observed))
        .unwrap();
    let bytes = serde_json::to_vec(&runtime).unwrap();
    let mut runtime: Runtime = serde_json::from_slice(&bytes).unwrap();
    runtime.recover_for_adoption().unwrap();
    let coordinator = runtime.request().unwrap();
    let mut continuation = d.response(&coordinator, Decision::Work);
    assert!(runtime.accept(continuation.clone()).is_err());
    continuation.update.as_mut().unwrap().addresses = vec![worker.invocation_id];
    runtime.accept(continuation).unwrap();
    assert_eq!(runtime.request().unwrap().role, Role::Worker);
}

#[test]
fn usage_is_deduplicated_and_does_not_mix_unknowns_or_conditional_development() {
    let d = Directory::new();
    let (mut runtime, worker) = d.worker();
    let usage = event(
        worker.invocation_id,
        1,
        EventKind::Usage {
            total: Usage {
                model_tokens: Some(10),
                ..Usage::default()
            },
        },
    );
    assert!(runtime.event(usage.clone()).unwrap());
    assert!(!runtime.event(usage).unwrap());
    assert_eq!(runtime.execution().unwrap().usage.model_tokens, Some(10));
    assert!(
        runtime
            .event(event(
                worker.invocation_id,
                2,
                EventKind::Usage {
                    total: Usage {
                        model_tokens: Some(9),
                        ..Usage::default()
                    }
                }
            ))
            .is_err()
    );
    runtime
        .event(event(worker.invocation_id, 2, boundary(false)))
        .unwrap();
    assert!(matches!(
        runtime.continuation().unwrap(),
        Continuation::Return { .. }
    ));
    let plan:OptionPlan=serde_json::from_value(serde_json::json!({"name":"probe","question":"one fact","mechanism":"source trace","useful_result":"reject premise", "work":[
        {"work":"probe","condition":"","estimate":{"model_tokens":3}},
        {"work":"full development","condition":"only if probe supports it","estimate":{"model_tokens":1000}}
    ]})).unwrap();
    assert_eq!(
        plan.immediate_cost().unwrap().unwrap().model_tokens,
        Some(3)
    );
    assert_eq!(
        Usage {
            model_tokens: Some(3),
            ..Usage::default()
        }
        .plus(&Usage::default())
        .unwrap()
        .model_tokens,
        None
    );
}

#[test]
fn cancellation_cannot_clear_unsettled_effects_but_evidence_can_reconcile_them() {
    let d = Directory::new();
    let (mut runtime, worker) = d.worker();
    runtime
        .event(event(
            worker.invocation_id,
            1,
            EventKind::Stopped {
                effects_settled: false,
            },
        ))
        .unwrap();
    assert!(
        runtime
            .accept(d.response(&worker, Decision::Observed))
            .is_err()
    );
    assert!(
        runtime
            .cancellation(Cancellation::Confirmed {
                effects_settled: true
            })
            .is_err()
    );
    runtime
        .event(event(
            worker.invocation_id,
            2,
            EventKind::Reconciled {
                summary: "Native operation receipt inspected".into(),
                evidence: vec![d.0.join("method.txt")],
            },
        ))
        .unwrap();
    runtime
        .accept(d.response(&worker, Decision::Observed))
        .unwrap();
    assert_eq!(runtime.request().unwrap().role, Role::Coordinator);
}

#[test]
fn prospective_research_is_validated_before_adoption_and_stale_assignment_is_not_promoted() {
    let d = Directory::new();
    let mut task = d.task();
    let mut source = task.sources[0].clone();
    source.roles = vec![Role::Coordinator];
    task.sources.push(source);
    let mut runtime = Runtime::new(task).unwrap();
    let request = runtime.request().unwrap();
    let mut response = d.response(&request, Decision::Work);
    response.update.as_mut().unwrap().options=serde_json::from_value(serde_json::json!([{"name":"probe","question":"fact","mechanism":"trace","useful_result":"result","work":[{"work":"read","estimate":{},"condition":""}],"prerequisites":[{"reason":"required evidence","source":1}]}])).unwrap();
    response.update.as_mut().unwrap().selected = "probe".into();
    let before = serde_json::to_vec(&runtime).unwrap();
    assert!(runtime.accept(response).is_err());
    assert_eq!(before, serde_json::to_vec(&runtime).unwrap());
    let mut response = d.response(&request, Decision::Work);
    response.assignment = "STALE_NEXT_ACTION".into();
    fs::write(d.0.join("method.txt"), "Changed method and evidence\n").unwrap();
    runtime.accept(response).unwrap();
    let next = runtime.request().unwrap();
    assert_eq!(next.role, Role::Coordinator);
    assert!(next.prompt.contains("Current assignment: \n"));
}

#[test]
fn selected_output_change_and_external_pause_withhold_further_work() {
    let d = Directory::new();
    let path = d.0.join("run");
    let mut session = Session::create(d.task(), &path).unwrap();
    let coordinator = session.request().unwrap();
    let mut response = d.response(&coordinator, Decision::Work);
    response
        .update
        .as_mut()
        .unwrap()
        .segment
        .as_mut()
        .unwrap()
        .return_on_change = vec![d.0.join("observation.json")];
    session.accept(response).unwrap();
    let worker = session.request().unwrap();
    session.begin_execution(capabilities()).unwrap();
    fs::write(d.0.join("observation.json"), "new native observation").unwrap();
    Session::request_pause(&path, "User requested pause".into()).unwrap();
    session
        .event(event(worker.invocation_id, 1, boundary(false)))
        .unwrap();
    assert!(matches!(
        session.continuation().unwrap(),
        Continuation::Return { .. }
    ));
    assert!(session.unpause().is_err());
    session
        .event(event(
            worker.invocation_id,
            2,
            EventKind::Stopped {
                effects_settled: true,
            },
        ))
        .unwrap();
    session
        .accept(d.response(&worker, Decision::Observed))
        .unwrap();
    assert!(session.request().is_err());
    session.unpause().unwrap();
    assert_eq!(session.request().unwrap().role, Role::Coordinator);
}

#[test]
#[cfg(unix)]
fn actual_stream_process_cannot_receive_a_continue_after_its_selected_boundary() {
    let d = Directory::new();
    let path = d.0.join("run");
    let mut session = Session::create(d.task(), &path).unwrap();
    let coordinator = session.request().unwrap();
    session
        .accept(d.response(&coordinator, Decision::Work))
        .unwrap();
    let worker = session.request().unwrap();
    let script = d.0.join("backend.sh");
    let response = d.response(&worker, Decision::Observed);
    fs::write(
        d.0.join("return.json"),
        serde_json::json!({"message":"return","response":response}).to_string(),
    )
    .unwrap();
    fs::write(&script,r#"read -r invocation
printf '%s\n' '{"message":"event","event":{"invocation_id":2,"sequence":1,"event":{"kind":"boundary","reason":"Existing observation reached","return_due":true,"effects_settled":true}}}'
read -r continuation
printf '%s\n' "$continuation" > decision.json
case "$continuation" in
  *'"decision":"continue"'*) printf 'unexpected expansion' > forbidden-expansion.txt ;;
esac
printf '%s\n' '{"message":"event","event":{"invocation_id":2,"sequence":2,"event":{"kind":"stopped","effects_settled":true}}}'
cat return.json
"#).unwrap();
    let config = ProcessAdapter {
        program: "/bin/sh".into(),
        args: vec![script.to_string_lossy().into_owned()],
    };
    let mut backend = StreamAdapter::new(config, capabilities(), &path.join("stream-2"), &d.0);
    session.drive(&mut backend).unwrap();
    assert!(!d.0.join("forbidden-expansion.txt").exists());
    assert!(
        fs::read_to_string(d.0.join("decision.json"))
            .unwrap()
            .contains("\"decision\":\"return\"")
    );
    assert_eq!(session.request().unwrap().role, Role::Coordinator);
}

#[cfg(unix)]
#[test]
fn published_recovery_survives_directory_sync_failure_in_hot_and_cold_sessions() {
    use std::os::unix::fs::PermissionsExt;
    for running in [true, false] {
        let d = Directory::new();
        let (mut s, request) = queued_worker(&d);
        assert!(s.drive(&mut RejectedBeforeStart).is_err());
        let not_started = Recovery::NotStartedConfirmed {
            invocation_id: request.invocation_id,
            evidence: "Host confirms no work started".into(),
        };
        let (published, contrary) = if running {
            (Recovery::Running, not_started)
        } else {
            (not_started, Recovery::Running)
        };
        let run = d.0.join("run");
        // Write and search allow checkpoint rename; lack of read access makes
        // opening the directory for synchronization fail after publication.
        fs::set_permissions(&run, fs::Permissions::from_mode(0o300)).unwrap();
        let fault_supported = fs::File::open(&run).is_err();
        let result = s.recover_backend(&mut ReplyAdapter {
            recovery: published,
            accepted: false,
        });
        fs::set_permissions(&run, fs::Permissions::from_mode(0o700)).unwrap();
        if !fault_supported {
            eprintln!("Directory permission fault is unavailable for this user (for example root)");
            return;
        }
        assert!(
            result.is_err(),
            "expected failure after checkpoint publication"
        );
        let disk: serde_json::Value =
            serde_json::from_slice(&fs::read(run.join("state.json")).unwrap()).unwrap();
        let execution = disk["runtime"]["executions"]
            .as_array()
            .unwrap()
            .iter()
            .find(|e| e["invocation_id"] == request.invocation_id)
            .unwrap();
        assert_eq!(execution["start_confirmed"], running);
        assert_eq!(execution["not_started"].is_string(), !running);
        assert!(
            s.recover_backend(&mut ReplyAdapter {
                recovery: contrary.clone(),
                accepted: false
            })
            .is_err(),
            "hot Session must preserve the published receipt"
        );
        drop(s);
        let mut s = Session::open(&run).unwrap();
        assert!(
            s.recover_backend(&mut ReplyAdapter {
                recovery: contrary,
                accepted: false
            })
            .is_err(),
            "cold Session must preserve the published receipt"
        );
    }
}
