//! Mechanical adapter coverage. Native host delivery and research value need live evidence.
use serde_json::{Value, json};
use std::fs;
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicUsize, Ordering};
use workflow_harness::control::{Cancellation, Capabilities, Continuation, Event, EventKind};
use workflow_harness::session::{HostBinding, Session};
use workflow_harness::{Decision, Invocation, Response, Role, Task};

static NEXT: AtomicUsize = AtomicUsize::new(0);
const SESSION: &str = "fixture-parent";
const AGENT: &str = "fixture-worker";
const TURN: &str = "fixture-turn";
const METHOD: &str = "Supplied method for a mechanical adapter test.\n";

struct Fixture(PathBuf);
impl Fixture {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "workflow-hook-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).unwrap();
        fs::write(path.join("method.txt"), METHOD).unwrap();
        Self(path)
    }
    fn run(&self) -> PathBuf {
        self.0.join("run")
    }
    fn task(&self) -> Task {
        serde_json::from_value(json!({
            "objective":"Verify dispatch control", "workspace":self.0,
            "constraints":"Temporary files only", "invocation_limit":20,
            "sources":[{"path":"method.txt","first_line":1,"last_line":1,"purpose":"method","roles":["coordinator","resolver","worker"]}],
            "research":{"question":"Does dispatch honor retained conditions?", "missing_observation":"Actual control outcome", "rationale":"Prevent continued work after its return point",
                "remaining_work":[{"work":"Inspect dispatch outcome","estimate":{},"condition":""}],
                "roles":[
                    {"role":"coordinator","method_source":0,"required_purposes":["method"],"write_scope":"Adoption","fresh_context":true},
                    {"role":"resolver","method_source":0,"required_purposes":["method"],"write_scope":"Recommendation","fresh_context":true},
                    {"role":"worker","method_source":0,"required_purposes":["method"],"write_scope":"Temporary observation","fresh_context":true}
                ]}
        })).unwrap()
    }
    fn response(&self, request: &Invocation, decision: Decision) -> Response {
        serde_json::from_value(json!({
            "invocation_id":request.invocation_id,"role":request.role,"decision":decision,
            "summary":"Mechanical test evidence, no optimization claim", "assignment":"Read the selected source once",
            "evidence":[self.0.join("method.txt")],
            "update":{"remaining_work":[],"interpretation":"The result supports the next bounded check",
                "rationale":"Verify the specific control transition", "reverse_when":"A new observation changes the selected work",
                "segment":{"observation":"One dispatch observation", "return_when":"Before expanding support work",
                    "return_on_change":[self.0.join("observation.json")]}}
        })).unwrap()
    }
    fn worker(&self) -> Invocation {
        let mut session = Session::create(self.task(), &self.run()).unwrap();
        let coordinator = session.request().unwrap();
        session
            .accept(self.response(&coordinator, Decision::Work))
            .unwrap();
        let worker = session.request().unwrap();
        session.begin_execution(capabilities()).unwrap();
        session
            .bind_host(HostBinding {
                invocation_id: worker.invocation_id,
                backend_handle: AGENT.into(),
            })
            .unwrap();
        fs::write(self.run().join("hook-enabled.json"), "true\n").unwrap();
        worker
    }
    fn event(&self, kind: &str) -> Value {
        json!({"hook_event_name":kind,"cwd":self.0,"session_id":SESSION,"agent_id":AGENT,
            "turn_id":TURN,"tool_name":"Bash","tool_use_id":"fixture-tool-call",
            "tool_input":{"command":"private command content must not enter receipts"}})
    }
    fn call(&self, event: Value) -> Value {
        let mut child = Command::new(env!("CARGO_BIN_EXE_workflow-codex-hook"))
            .args([
                self.0.to_str().unwrap(),
                SESSION,
                AGENT,
                self.run().to_str().unwrap(),
            ])
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        child
            .stdin
            .take()
            .unwrap()
            .write_all(serde_json::to_string(&event).unwrap().as_bytes())
            .unwrap();
        let output = child.wait_with_output().unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        serde_json::from_slice(&output.stdout).unwrap()
    }
    fn enroll(&self) {
        assert_eq!(self.call(self.event("SubagentStart")), json!({}));
    }
    fn check(&self) -> Value {
        self.call(self.event("PreToolUse"))
    }
}
impl Drop for Fixture {
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
        isolation: "Temporary mechanical fixture".into(),
    }
}
fn denied(value: &Value) {
    assert_eq!(
        value["hookSpecificOutput"]["permissionDecision"], "deny",
        "{value}"
    );
    assert!(
        value["hookSpecificOutput"]["permissionDecisionReason"]
            .as_str()
            .unwrap()
            .contains("Coordinator")
    );
}
fn event(id: usize, sequence: u64, event: EventKind) -> Event {
    Event {
        invocation_id: id,
        sequence,
        event,
    }
}

#[test]
fn unrelated_scope_does_not_open_or_lock_a_corrupt_run() {
    let f = Fixture::new();
    fs::create_dir(f.run()).unwrap();
    fs::write(f.run().join("state.json"), "broken").unwrap();
    for (key, value) in [
        ("cwd", json!(std::env::temp_dir())),
        ("session_id", json!("sibling-session")),
        ("agent_id", json!("sibling-worker")),
        ("agent_id", Value::Null),
    ] {
        let mut input = f.event("PreToolUse");
        input[key] = value;
        assert_eq!(f.call(input), json!({}));
    }
    assert!(!f.run().join("writer.lock").exists());
    assert!(!f.run().join("hook-enabled.json").exists());
    fs::write(f.run().join("hook-enabled.json"), "true").unwrap();
    let child = f.0.join("nested");
    fs::create_dir(&child).unwrap();
    let mut input = f.event("PreToolUse");
    input["cwd"] = json!(child);
    denied(&f.call(input));
}

#[test]
fn explicit_disable_retires_cached_definition_even_when_state_is_broken() {
    let f = Fixture::new();
    fs::create_dir(f.run()).unwrap();
    fs::write(f.run().join("state.json"), "broken").unwrap();
    fs::write(f.run().join("hook-enabled.json"), "false").unwrap();
    assert_eq!(f.check(), json!({}));
    assert_eq!(f.call(f.event("SubagentStart")), json!({}));
    assert!(!f.run().join("writer.lock").exists());
    fs::write(f.run().join("hook-enabled.json"), "broken").unwrap();
    denied(&f.check());
}

#[test]
fn first_tool_enrolls_without_lifecycle_but_requires_complete_native_identity() {
    let f = Fixture::new();
    let worker = f.worker();
    let mut missing = f.event("SubagentStart");
    missing.as_object_mut().unwrap().remove("turn_id");
    assert!(f.call(missing)["systemMessage"].is_string());
    assert!(
        !f.run()
            .join(format!("native-turn-{}.json", worker.invocation_id))
            .exists()
    );
    let turn_path = f
        .run()
        .join(format!("native-turn-{}.json", worker.invocation_id));
    for key in ["turn_id", "tool_use_id", "tool_name"] {
        let mut missing = f.event("PreToolUse");
        missing.as_object_mut().unwrap().remove(key);
        denied(&f.call(missing));
        assert!(!turn_path.exists(), "invalid first event must not enroll");
    }
    assert_eq!(f.check(), json!({}));
    let enrolled: Value = serde_json::from_slice(&fs::read(&turn_path).unwrap()).unwrap();
    assert_eq!(enrolled["turn_id"], TURN);
    assert_eq!(enrolled["invocation_id"], worker.invocation_id);
    f.enroll();
    assert_eq!(f.check(), json!({}));
    for key in ["turn_id", "tool_use_id", "tool_name"] {
        let mut missing = f.event("PreToolUse");
        missing.as_object_mut().unwrap().remove(key);
        denied(&f.call(missing));
    }
    let mut another = f.event("PreToolUse");
    another["turn_id"] = json!("another-turn");
    denied(&f.call(another));
    let mut another = f.event("SubagentStart");
    another["turn_id"] = json!("another-turn");
    assert!(f.call(another)["systemMessage"].is_string());
    assert_eq!(f.check(), json!({}));
}

#[test]
fn ordinary_dispatch_does_not_claim_stoppage_or_settled_effects() {
    let f = Fixture::new();
    let worker = f.worker();
    f.enroll();
    for _ in 0..3 {
        assert_eq!(f.check(), json!({}));
    }
    let child = f.0.join("nested");
    fs::create_dir(&child).unwrap();
    let mut input = f.event("PreToolUse");
    input["cwd"] = json!(child);
    assert_eq!(f.call(input), json!({}));
    let mut session = Session::open(&f.run()).unwrap();
    assert_eq!(session.check_action().unwrap(), Continuation::Continue);
    let execution = session.runtime.execution().unwrap();
    assert!(!execution.effects_settled);
    assert!(!execution.stopped);
    assert!(!execution.awaiting_continuation);
    assert!(
        session
            .accept_host_return(AGENT, f.response(&worker, Decision::Observed))
            .is_err()
    );
    for entry in fs::read_dir(f.run()).unwrap() {
        let path = entry.unwrap().path();
        if path
            .file_name()
            .unwrap()
            .to_string_lossy()
            .starts_with("native-")
        {
            assert!(
                !fs::read_to_string(path)
                    .unwrap()
                    .contains("private command content")
            );
        }
    }
}

#[test]
fn first_call_without_lifecycle_still_checks_and_latches_every_return_condition() {
    for trigger in ["output", "source", "pause", "challenge"] {
        let f = Fixture::new();
        let worker = f.worker();
        match trigger {
            "output" => fs::write(f.0.join("observation.json"), "new observation").unwrap(),
            "source" => fs::write(f.0.join("method.txt"), "Changed selected source\n").unwrap(),
            "pause" => {
                Session::request_pause(&f.run(), "Review accumulated support cost".into()).unwrap()
            }
            "challenge" => {
                Session::open(&f.run())
                    .unwrap()
                    .event(event(
                        worker.invocation_id,
                        1,
                        EventKind::Challenge {
                            reason: "Support work no longer discriminates live routes".into(),
                        },
                    ))
                    .unwrap();
            }
            _ => unreachable!(),
        }
        denied(&f.check());
        if trigger == "output" {
            fs::remove_file(f.0.join("observation.json")).unwrap();
        }
        if trigger == "source" {
            fs::write(f.0.join("method.txt"), METHOD).unwrap();
        }
        if trigger == "pause" {
            fs::remove_file(f.run().join("pause-request.json")).unwrap();
        }
        denied(&f.check());
        let mut session = Session::open(&f.run()).unwrap();
        assert!(matches!(
            session.check_action().unwrap(),
            Continuation::Return { .. }
        ));
        assert!(session.runtime.execution().unwrap().continuation_withheld);
        assert!(!session.runtime.execution().unwrap().effects_settled);
    }
}

#[test]
fn stopped_or_pending_stream_handshake_cannot_be_bypassed_by_dispatch_check() {
    for stopped in [false, true] {
        let f = Fixture::new();
        let worker = f.worker();
        f.enroll();
        {
            let mut session = Session::open(&f.run()).unwrap();
            let kind = if stopped {
                EventKind::Stopped {
                    effects_settled: true,
                }
            } else {
                EventKind::Boundary {
                    reason: "Stream idle handshake".into(),
                    return_due: false,
                    effects_settled: true,
                }
            };
            session.event(event(worker.invocation_id, 1, kind)).unwrap();
            assert!(session.check_action().is_err());
        }
        denied(&f.check());
        let session = Session::open(&f.run()).unwrap();
        assert_eq!(
            session.runtime.execution().unwrap().awaiting_continuation,
            !stopped
        );
    }
}

#[test]
fn coordinator_must_adopt_retained_return_before_a_new_worker_can_resume() {
    let f = Fixture::new();
    let worker = f.worker();
    f.enroll();
    fs::write(f.0.join("observation.json"), "bounded observation").unwrap();
    denied(&f.check());
    {
        let mut session = Session::open(&f.run()).unwrap();
        session
            .event(event(
                worker.invocation_id,
                1,
                EventKind::Stopped {
                    effects_settled: false,
                },
            ))
            .unwrap();
        assert!(
            session
                .accept_host_return(AGENT, f.response(&worker, Decision::Observed))
                .is_err()
        );
        session
            .event(event(
                worker.invocation_id,
                2,
                EventKind::Reconciled {
                    summary: "No running effects; retained local observation verified".into(),
                    evidence: vec![f.0.join("observation.json")],
                },
            ))
            .unwrap();
        session
            .accept_host_return(AGENT, f.response(&worker, Decision::Observed))
            .unwrap();
        assert_eq!(session.request().unwrap().role, Role::Coordinator);
    }
    denied(&f.check());
    let next_worker;
    {
        let mut session = Session::open(&f.run()).unwrap();
        let coordinator = session.runtime.outstanding().unwrap().clone();
        let mut adoption = f.response(&coordinator, Decision::Work);
        assert!(session.accept(adoption.clone()).is_err());
        adoption.update.as_mut().unwrap().addresses = vec![worker.invocation_id];
        session.accept(adoption).unwrap();
        next_worker = session.request().unwrap();
        assert_eq!(next_worker.role, Role::Worker);
        assert_ne!(next_worker.invocation_id, worker.invocation_id);
        session.begin_execution(capabilities()).unwrap();
        session
            .bind_host(HostBinding {
                invocation_id: next_worker.invocation_id,
                backend_handle: AGENT.into(),
            })
            .unwrap();
    }
    let mut next = f.event("PreToolUse");
    next["turn_id"] = json!("next-worker-turn");
    assert_eq!(f.call(next.clone()), json!({}));
    denied(&f.check());
    assert_eq!(f.call(next), json!({}));
}

#[test]
fn matching_scope_cannot_borrow_another_workspace_or_worker_binding() {
    let f = Fixture::new();
    let worker = f.worker();
    f.enroll();
    let checkpoint = fs::read(f.run().join("state.json")).unwrap();
    let other = Fixture::new();
    other.worker();
    fs::copy(other.run().join("state.json"), f.run().join("state.json")).unwrap();
    denied(&f.check());
    fs::write(f.run().join("state.json"), checkpoint).unwrap();
    let binding = f.run().join(format!("host-{}.json", worker.invocation_id));
    fs::write(
        &binding,
        serde_json::to_vec(&json!({
            "invocation_id":worker.invocation_id,"backend_handle":"another-worker"
        }))
        .unwrap(),
    )
    .unwrap();
    denied(&f.check());
    fs::remove_file(binding).unwrap();
    denied(&f.check());
}

#[test]
fn cancellation_cannot_restore_discretionary_dispatch_or_hide_unsettled_effects() {
    for cancellation in [
        Cancellation::Unsupported,
        Cancellation::Pending,
        Cancellation::Unknown,
        Cancellation::Confirmed {
            effects_settled: false,
        },
        Cancellation::Confirmed {
            effects_settled: true,
        },
    ] {
        let f = Fixture::new();
        f.worker();
        let mut session = Session::open(&f.run()).unwrap();
        session.runtime.cancellation(cancellation.clone()).unwrap();
        let decision = session.runtime.check_action();
        if matches!(cancellation, Cancellation::Confirmed { .. }) {
            assert!(decision.is_err());
            assert!(session.runtime.execution().unwrap().stopped);
        } else {
            assert!(matches!(decision.unwrap(), Continuation::Return { .. }));
            assert!(!session.runtime.execution().unwrap().stopped);
        }
        assert_eq!(
            session.runtime.execution().unwrap().effects_settled,
            matches!(
                cancellation,
                Cancellation::Confirmed {
                    effects_settled: true
                }
            )
        );
    }
}
