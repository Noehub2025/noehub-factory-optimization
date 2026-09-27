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
