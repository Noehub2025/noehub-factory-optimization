//! Decision-state regressions, not evidence of improved research quality.
use serde_json::json;
use std::{
    fs,
    path::PathBuf,
    sync::atomic::{AtomicUsize, Ordering},
};
use workflow_harness::decision::{
    CheckReturn, Config, Disposition, Finding, Guard, Mode, OwnerReturn, Verdict,
};
use workflow_harness::session::Session;
use workflow_harness::{Response, Role, Task};

static NEXT: AtomicUsize = AtomicUsize::new(0);
struct Fixture(PathBuf);
impl Fixture {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "workflow-decision-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).unwrap();
        fs::write(
            path.join("method.txt"),
            "Actual role method for mechanical verification.\n",
        )
        .unwrap();
        fs::write(
            path.join("policy.md"),
            "Do not require incumbent failure before developing a different mechanism.\n",
        )
        .unwrap();
        Self(path)
    }
    fn run(&self) -> PathBuf {
        self.0.join("run")
    }
    fn config(&self, mode: Mode) -> Config {
        Config {
            mode,
            policy: self.0.join("policy.md"),
            timeout_ms: 60000,
            publication: Some(self.0.join("selection.md")),
        }
    }
    fn task(&self) -> Task {
        serde_json::from_value(json!({"objective":"Verify consequential decision handling", "workspace":self.0,
            "constraints":"Temporary files only", "invocation_limit":20,
            "sources":[{"path":"method.txt","first_line":1,"last_line":1,"purpose":"method","roles":["coordinator","resolver","worker"]}],
            "research":{"question":"Does the selected mechanism survive adoption?","missing_observation":"Correlated dispatch", "rationale":"Avoid silent narrowing", "remaining_work":[],
                "roles":[{"role":"coordinator","method_source":0,"required_purposes":["method"],"write_scope":"Adoption","fresh_context":true},
                    {"role":"resolver","method_source":0,"required_purposes":["method"],"write_scope":"Recommendation","fresh_context":true},
                    {"role":"worker","method_source":0,"required_purposes":["method"],"write_scope":"Temporary evidence","fresh_context":true}]}
        })).unwrap()
    }
    fn start(&self, mode: Mode) -> (Session, Response) {
        let mut session = Session::create(self.task(), &self.run()).unwrap();
        session.configure_decisions(self.config(mode)).unwrap();
        let request = session.request().unwrap();
        let response = serde_json::from_value(json!({"invocation_id":request.invocation_id,"role":"coordinator","decision":"work",
            "summary":"Mechanical test only", "assignment":"Develop the complete mechanism", "evidence":[self.0.join("method.txt")],
            "update":{"remaining_work":[],"interpretation":"No optimization claim", "selected":"joint allocation",
                "options":[{"name":"joint allocation","question":"Can joint choices improve the objective?","mechanism":"Replan coupled decisions", "useful_result":"Objective-related comparison", "work":[{"work":"Develop integrated behavior","estimate":{},"condition":""}],"prerequisites":[]}],
                "rationale":"Test a substantive alternative", "reverse_when":"Evidence undermines its remaining value",
                "segment":{"observation":"Integrated behavior", "return_when":"Before new investment"}}
        })).unwrap();
        (session, response)
    }
    fn submit(&self, mode: Mode) -> (Session, Response) {
        let (mut session, response) = self.start(mode);
        session.accept(response.clone()).unwrap();
        session.bind_decision(1, "actual-checker".into()).unwrap();
        (session, response)
    }
    fn result(&self, verdict: Verdict) -> CheckReturn {
        CheckReturn {
            check_id: 1,
            backend_handle: "actual-checker".into(),
            verdict,
            reason: "Specific mechanical fixture".into(),
            findings: if verdict == Verdict::Revise {
                vec![Finding {
                    policy_excerpt: "Do not require incumbent failure".into(),
                    decision_excerpt: "Develop the complete mechanism".into(),
                    correction: "Mechanical finding for owner-path verification only".into(),
                }]
            } else {
                vec![]
            },
            model_tokens: None,
        }
    }
    fn publish(&self, session: &Session) {
        let p = session.decisions.publication.as_ref().unwrap();
        fs::write(&p.path,format!("# Existing owner record\n<!-- workflow-current-decision:begin -->\n{}\n<!-- workflow-current-decision:end -->\n",json!({"check_id":p.check_id,"proposal":p.proposal}))).unwrap();
    }
    fn owner(&self, disposition: Disposition, proposal: Option<Response>) -> OwnerReturn {
        OwnerReturn {
            check_id: 1,
            disposition,
            reason: "Owner's supported correction or boundary and recovery condition".into(),
            evidence: vec![self.0.join("method.txt")],
            proposal,
        }
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn context(f: &Fixture, event: serde_json::Value) -> serde_json::Value {
    context_mode(f, event, false)
}

fn context_mode(f: &Fixture, event: serde_json::Value, record: bool) -> serde_json::Value {
    use std::{
        io::Write,
        process::{Command, Stdio},
    };
    let mut command = Command::new(env!("CARGO_BIN_EXE_workflow-codex-hook"));
    if record {
        command.args(["--record-context", f.0.to_str().unwrap()]);
    } else {
        command.args([
            "--decision-context",
            f.0.to_str().unwrap(),
            "native-session",
            "-",
            f.run().to_str().unwrap(),
        ]);
    }
    let mut child = command
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(event.to_string().as_bytes())
        .unwrap();
    let output = child.wait_with_output().unwrap();
    assert!(output.status.success());
    serde_json::from_slice(&output.stdout).unwrap()
}

#[test]
fn native_owner_record_tracks_actual_decision_changes_without_an_installation_run() {
    let f = Fixture::new();
    let root = fs::canonicalize(&f.0).unwrap();
    let directory = root.join(".frontier/hook-context");
    fs::create_dir_all(&directory).unwrap();
    let record = root.join("resolution.json");
    fs::write(
        &record,
        json!({"pending_decision":"Choose the next whole mechanism",
        "policy_coverage":{"judgment_status":"addressed"}})
        .to_string(),
    )
    .unwrap();
    fs::write(
        directory.join("research-task.json"),
        json!({"workspace":root,
        "session_id":"research-task","record":record,"phase":"bind-resolution"})
        .to_string(),
    )
    .unwrap();
    let event = json!({"hook_event_name":"PreToolUse","session_id":"research-task","cwd":root,"tool_use_id":"real-call-shape"});
    let output = context_mode(&f, event.clone(), true);
    let message = output["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap();
    assert!(message.contains("Choose the next whole mechanism"));
    assert!(message.contains("addressed"));
    assert!(output["hookSpecificOutput"]["permissionDecision"].is_null());
    assert_eq!(context_mode(&f, event.clone(), true), json!({}));
    fs::write(
        &record,
        json!({"pending_decision":"Develop the selected mechanism"}).to_string(),
    )
    .unwrap();
    let changed = context_mode(&f, event.clone(), true);
    let message = changed["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap();
    assert!(message.contains("Develop the selected mechanism"));
    assert!(message.contains("not_reported"));
    let mut resume = event;
    resume["hook_event_name"] = json!("SessionStart");
    assert!(context_mode(&f, resume, true)["hookSpecificOutput"]["additionalContext"].is_string());
    let receipt: serde_json::Value = serde_json::from_slice(
        &fs::read(directory.join("research-task-PreToolUse-delivery.json")).unwrap(),
    )
    .unwrap();
    assert_eq!(receipt["record"], record.to_str().unwrap());
    assert_eq!(receipt["mode"], "observe");
}

#[test]
fn owner_record_observer_does_not_borrow_another_task_or_block_missing_state() {
    let f = Fixture::new();
    let root = fs::canonicalize(&f.0).unwrap();
    let directory = root.join(".frontier/hook-context");
    fs::create_dir_all(&directory).unwrap();
    let event = json!({"hook_event_name":"PreToolUse","session_id":"research-task","cwd":root});
    assert_eq!(context_mode(&f, event.clone(), true), json!({}));
    fs::write(directory.join("research-task.json"), "corrupt").unwrap();
    assert_eq!(context_mode(&f, event.clone(), true), json!({}));
    let mut child = event.clone();
    child["agent_id"] = json!("child");
    assert_eq!(context_mode(&f, child, true), json!({}));
    let other = Fixture::new();
    fs::write(
        directory.join("research-task.json"),
        json!({"workspace":root,"session_id":"research-task",
        "record":other.0.join("policy.md"),"phase":"bind-resolution"})
        .to_string(),
    )
    .unwrap();
    assert_eq!(context_mode(&f, event.clone(), true), json!({}));
    let mut unrelated = event.clone();
    unrelated["session_id"] = json!("another-task");
    assert_eq!(context_mode(&f, unrelated, true), json!({}));
    let mut stop = event;
    stop["hook_event_name"] = json!("Stop");
    assert_eq!(context_mode(&f, stop, true), json!({}));
    assert!(
        !directory
            .join("research-task-PreToolUse-delivery.json")
            .exists()
    );
}

fn adopted_fixture(f: &Fixture) -> (PathBuf, serde_json::Value) {
    let root = fs::canonicalize(&f.0).unwrap();
    let directory = root.join(".frontier/hook-context");
    fs::create_dir_all(&directory).unwrap();
    let selection = root.join("selection.md");
    fs::write(&selection, "hello").unwrap();
    let binding = json!({"kind":"adopted_work","workspace":root,"session_id":"owner",
        "selection":{"path":selection,"fingerprint":"a430d84680aabd0b"},"work":null,
        "current_state":{"campaign_status":"running","primary_work":"Develop joint allocation"},
        "work_status":"active"});
    fs::write(directory.join("owner.json"), binding.to_string()).unwrap();
    let event = json!({"hook_event_name":"PreToolUse","session_id":"owner","cwd":root,
        "tool_use_id":"call1","tool_name":"spawn_agent", "turn_id":"turn1",
        "tool_input":{"task_name":"designer","message":"Only repair one isolated decision; unchanged"}});
    (directory, event)
}

#[test]
fn actual_task_is_retained_even_when_ids_and_self_report_hide_narrowing() {
    let f = Fixture::new();
    let (directory, event) = adopted_fixture(&f);
    let output = context_mode(&f, event.clone(), true);
    let context = output["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap();
    assert!(context.contains("equal IDs"));
    assert!(output["hookSpecificOutput"]["permissionDecision"].is_null());
    let attempt: serde_json::Value =
        serde_json::from_slice(&fs::read(directory.join("owner-call-call1.json")).unwrap())
            .unwrap();
    assert_eq!(attempt["tool_input"], event["tool_input"]);
    assert_eq!(attempt["association"], "current");
    assert_eq!(attempt["status"], "attempted_dispatch");
    assert!(!directory.join("owner-call-call1-post.json").exists());
    let mut duplicate = event;
    duplicate["tool_input"]["message"] = json!("Different duplicate input");
    context_mode(&f, duplicate, true);
    let preserved: serde_json::Value =
        serde_json::from_slice(&fs::read(directory.join("owner-call-call1.json")).unwrap())
            .unwrap();
    assert_eq!(attempt, preserved);
}

#[test]
fn response_stays_with_original_work_and_does_not_claim_worker_completion() {
    let f = Fixture::new();
    let (directory, mut event) = adopted_fixture(&f);
    context_mode(&f, event.clone(), true);
    fs::write(
        f.0.join("selection.md"),
        "paused or replaced after dispatch",
    )
    .unwrap();
    event["hook_event_name"] = json!("PostToolUse");
    event["tool_response"] = json!({"task_name":"/root/designer"});
    let output = context_mode(&f, event.clone(), true);
    assert!(
        output["hookSpecificOutput"]["additionalContext"]
            .as_str()
            .unwrap()
            .contains("not worker completion")
    );
    let post = directory.join("owner-call-call1-post.json");
    let original = fs::read(&post).unwrap();
    let response: serde_json::Value = serde_json::from_slice(&original).unwrap();
    assert_eq!(response["status"], "confirmed_dispatch");
    assert_eq!(response["worker_handle"], "/root/designer");
    event["tool_response"] = json!({"error":"duplicate late failure"});
    context_mode(&f, event, true);
    assert_eq!(original, fs::read(post).unwrap());
    let mut recovery = json!({"hook_event_name":"SessionStart","session_id":"owner","cwd":f.0});
    assert!(
        context_mode(&f, recovery.clone(), true)["hookSpecificOutput"]["additionalContext"]
            .as_str()
            .unwrap()
            .contains("stale")
    );
    recovery["agent_id"] = json!("child");
    assert_eq!(context_mode(&f, recovery, true), json!({}));
}

#[test]
fn retained_serialized_dispatch_shape_confirms_only_dispatch_and_preserves_opaque_task() {
    let f = Fixture::new();
    let (directory, mut event) = adopted_fixture(&f);
    // Retained x1081 response shape; the task body remains a synthetic opaque value.
    event["tool_name"] = json!("collaborationspawn_agent");
    event["tool_input"] =
        json!({"task_name":"x1081_resolver","message":"gAAAAopaque-host-payload"});
    context_mode(&f, event.clone(), true);
    event["hook_event_name"] = json!("PostToolUse");
    event["tool_response"] = json!(r#"{"task_name":"/root/x1081_resolver"}"#);
    let mut mismatched = event.clone();
    mismatched["tool_input"]["task_name"] = json!("different_resolver");
    assert_eq!(context_mode(&f, mismatched, true), json!({}));
    let post_path = directory.join("owner-call-call1-post.json");
    assert!(!post_path.exists());

    let output = context_mode(&f, event.clone(), true);
    let message = output["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap();
    assert!(message.contains("confirmed_dispatch"));
    assert!(message.contains("not worker completion or semantic acceptance"));
    let original = fs::read(&post_path).unwrap();
    let post: serde_json::Value = serde_json::from_slice(&original).unwrap();
    assert_eq!(post["status"], "confirmed_dispatch");
    assert_eq!(post["worker_handle"], "/root/x1081_resolver");
    assert_eq!(post["tool_response"], event["tool_response"]);
    let attempt: serde_json::Value =
        serde_json::from_slice(&fs::read(directory.join("owner-call-call1.json")).unwrap())
            .unwrap();
    assert_eq!(attempt["tool_input"], event["tool_input"]);
    assert_eq!(attempt["task_visibility"], "opaque_or_unavailable");
    event["tool_response"] = json!(r#"{"error":"late duplicate"}"#);
    context_mode(&f, event, true);
    assert_eq!(fs::read(post_path).unwrap(), original);
}

#[test]
fn serialized_dispatch_responses_decode_only_one_object_level() {
    let f = Fixture::new();
    let (directory, mut event) = adopted_fixture(&f);
    let object = json!({"task_name":"/root/x1081_resolver"});
    for (index, (response, expected)) in [
        (object.clone(), "confirmed_dispatch"),
        (json!(object.to_string()), "confirmed_dispatch"),
        (json!(json!(object.to_string()).to_string()), "uncertain"),
        (json!(r#"{"task_name":"/root/x1081_resolver""#), "uncertain"),
        (json!(format!("{object} trailing data")), "uncertain"),
        (json!("{}"), "uncertain"),
        (json!("null"), "uncertain"),
        (json!("true"), "uncertain"),
        (json!("42"), "uncertain"),
        (json!(format!("[{object}]")), "uncertain"),
        (json!(json!({"response":object}).to_string()), "uncertain"),
        (json!(r#"{"queued":true}"#), "uncertain"),
        (json!(r#"{"task_name":""}"#), "uncertain"),
    ]
    .into_iter()
    .enumerate()
    {
        let call = format!("shape-{index}");
        event["tool_use_id"] = json!(call);
        event["hook_event_name"] = json!("PreToolUse");
        context_mode(&f, event.clone(), true);
        event["hook_event_name"] = json!("PostToolUse");
        event["tool_response"] = response;
        context_mode(&f, event.clone(), true);
        let post: serde_json::Value = serde_json::from_slice(
            &fs::read(directory.join(format!("owner-call-{call}-post.json"))).unwrap(),
        )
        .unwrap();
        assert_eq!(post["status"], expected, "{call}");
        assert_eq!(post["tool_response"], event["tool_response"], "{call}");
        if expected == "uncertain" {
            assert!(post["worker_handle"].is_null(), "{call}");
        }
    }
}

#[test]
fn explicit_outer_and_inner_errors_override_serialized_dispatch_handles() {
    for failure in [
        json!({"isError":true}),
        json!({"success":false}),
        json!({"error":"reported failure"}),
        json!({"status":"failed"}),
        json!({"status":"cancelled"}),
        json!({"status":"canceled"}),
        json!({"status":"rejected"}),
        json!({"status":"error"}),
        json!({"status":"aborted"}),
        json!({"status":"timeout"}),
        json!({"status":"unavailable"}),
    ] {
        for location in ["event", "object", "serialized_object"] {
            let f = Fixture::new();
            let (directory, mut event) = adopted_fixture(&f);
            context_mode(&f, event.clone(), true);
            event["hook_event_name"] = json!("PostToolUse");
            let mut response = json!({"task_name":"/root/x1081_resolver"});
            if location == "event" {
                event
                    .as_object_mut()
                    .unwrap()
                    .extend(failure.as_object().unwrap().clone());
            } else {
                response
                    .as_object_mut()
                    .unwrap()
                    .extend(failure.as_object().unwrap().clone());
            }
            event["tool_response"] = if location == "object" {
                response
            } else {
                json!(response.to_string())
            };
            context_mode(&f, event, true);
            let post: serde_json::Value = serde_json::from_slice(
                &fs::read(directory.join("owner-call-call1-post.json")).unwrap(),
            )
            .unwrap();
            assert_eq!(post["status"], "failed", "{location}: {failure}");
            assert!(post["worker_handle"].is_null(), "{location}: {failure}");
        }
    }
}

#[test]
fn oversized_serialized_dispatch_response_does_not_bypass_observation_limit() {
    let f = Fixture::new();
    let (directory, mut event) = adopted_fixture(&f);
    context_mode(&f, event.clone(), true);
    event["hook_event_name"] = json!("PostToolUse");
    event["tool_response"] = json!(
        json!({"task_name":"/root/x1081_resolver","padding":"x".repeat(262_144)}).to_string()
    );
    assert_eq!(context_mode(&f, event, true), json!({}));
    assert!(directory.join("owner-call-call1.json").exists());
    assert!(!directory.join("owner-call-call1-post.json").exists());
}

#[test]
fn followups_use_distinct_calls_and_unknown_or_failed_responses_are_not_confirmed() {
    let f = Fixture::new();
    let (directory, mut event) = adopted_fixture(&f);
    event["tool_name"] = json!("collaborationfollowup_task");
    event["tool_input"] = json!({"target":"/root/designer","message":"Continue integrated design"});
    for (call, response, expected) in [
        ("first", json!({"status":"success"}), "confirmed_dispatch"),
        ("second", json!({"queued":true}), "uncertain"),
        (
            "cancelled",
            json!({"status":"cancelled","agent_id":"old-handle"}),
            "failed",
        ),
        (
            "third",
            json!({"isError":true,"task_name":"old-handle"}),
            "failed",
        ),
    ] {
        event["tool_use_id"] = json!(call);
        event["hook_event_name"] = json!("PreToolUse");
        context_mode(&f, event.clone(), true);
        event["hook_event_name"] = json!("PostToolUse");
        event["tool_response"] = response;
        context_mode(&f, event.clone(), true);
        let post: serde_json::Value = serde_json::from_slice(
            &fs::read(directory.join(format!("owner-call-{call}-post.json"))).unwrap(),
        )
        .unwrap();
        assert_eq!(post["status"], expected);
    }
}

#[test]
fn orphan_or_mismatched_posts_do_not_manufacture_dispatch_success() {
    let f = Fixture::new();
    let (directory, mut event) = adopted_fixture(&f);
    event["hook_event_name"] = json!("PostToolUse");
    event["tool_response"] = json!({"task_name":"/root/designer"});
    assert_eq!(context_mode(&f, event.clone(), true), json!({}));
    event["hook_event_name"] = json!("PreToolUse");
    context_mode(&f, event.clone(), true);
    event["hook_event_name"] = json!("PostToolUse");
    event["tool_input"]["message"] = json!("Not the original input");
    assert_eq!(context_mode(&f, event, true), json!({}));
    assert!(!directory.join("owner-call-call1-post.json").exists());
}

#[test]
fn opaque_native_task_payload_is_not_claimed_as_readable_assignment() {
    let f = Fixture::new();
    let (directory, mut event) = adopted_fixture(&f);
    event["tool_input"]["message"] = json!("gAAAAopaque-host-payload");
    let output = context_mode(&f, event, true);
    assert!(
        output["hookSpecificOutput"]["additionalContext"]
            .as_str()
            .unwrap()
            .contains("does not capture readable assignment")
    );
    let attempt: serde_json::Value =
        serde_json::from_slice(&fs::read(directory.join("owner-call-call1.json")).unwrap())
            .unwrap();
    assert_eq!(attempt["task_visibility"], "opaque_or_unavailable");
}

fn host(f: &Fixture, command: &str, input: serde_json::Value) -> serde_json::Value {
    use std::{
        io::Write,
        process::{Command, Stdio},
    };
    let mut child = Command::new(env!("CARGO_BIN_EXE_workflow-harness"))
        .args(["host", command, f.run().to_str().unwrap()])
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
    let output = child.wait_with_output().unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    serde_json::from_slice(&output.stdout).unwrap()
}

#[test]
fn actual_host_return_path_emits_no_worker_until_check_and_writeback_are_consumed() {
    let f = Fixture::new();
    let (s, p) = f.start(Mode::Enforce);
    s.bind_host(workflow_harness::session::HostBinding {
        invocation_id: p.invocation_id,
        backend_handle: "actual-owner".into(),
    })
    .unwrap();
    drop(s);
    let held = host(
        &f,
        "return",
        json!({"backend_handle":"actual-owner","response":p}),
    );
    assert_eq!(held["event"], "decision_pending");
    host(
        &f,
        "decision-bind",
        json!({"check_id":1,"backend_handle":"actual-checker"}),
    );
    host(
        &f,
        "decision-result",
        serde_json::to_value(f.result(Verdict::NoFinding)).unwrap(),
    );
    let held = host(&f, "next", json!(null));
    assert_eq!(held["event"], "decision_pending");
    let s = Session::open(&f.run()).unwrap();
    f.publish(&s);
    drop(s);
    let invocation = host(&f, "decision-publish", json!(1));
    assert_eq!(invocation["role"], "worker");
    assert_ne!(invocation["invocation_id"], p.invocation_id);
}

#[test]
fn native_context_is_scoped_advisory_deduplicated_and_never_restarts_stop() {
    let f = Fixture::new();
    let (s, _) = f.submit(Mode::Enforce);
    drop(s);
    let event = json!({"hook_event_name":"PreToolUse","session_id":"native-session","cwd":f.0});
    let mut other = event.clone();
    other["agent_id"] = json!("unrelated-child");
    assert_eq!(context(&f, other), json!({}));
    let output = context(&f, event.clone());
    assert!(
        output["hookSpecificOutput"]["additionalContext"]
            .as_str()
            .unwrap()
            .contains("pending")
    );
    assert!(output["hookSpecificOutput"]["permissionDecision"].is_null());
    assert_eq!(context(&f, event), json!({}));
    for kind in ["Stop", "UserPromptSubmit"] {
        assert_eq!(
            context(
                &f,
                json!({"hook_event_name":kind,"session_id":"native-session","cwd":f.0})
            ),
            json!({})
        );
    }
    let resume = context(
        &f,
        json!({"hook_event_name":"SessionStart","source":"compact","session_id":"native-session","cwd":f.0}),
    );
    assert!(resume["hookSpecificOutput"]["additionalContext"].is_string());
}

#[test]
fn explicit_disable_returns_pending_to_owner_and_native_errors_fail_open() {
    let f = Fixture::new();
    let (mut s, _) = f.submit(Mode::Enforce);
    s.configure_decisions(f.config(Mode::Disabled)).unwrap();
    assert!(!s.decisions.holds());
    assert_eq!(s.runtime.outstanding().unwrap().role, Role::Coordinator);
    drop(s);
    let event = json!({"hook_event_name":"SessionStart","session_id":"native-session","cwd":f.0});
    assert_eq!(context(&f, event.clone()), json!({}));
    fs::write(f.run().join("state.json"), "corrupt").unwrap();
    assert_eq!(context(&f, event), json!({}));
}

#[test]
fn ordinary_observer_records_delivery_once_without_context_or_command_data() {
    let f = Fixture::new();
    let (s, _) = f.start(Mode::Observe);
    drop(s);
    let mut event = json!({"hook_event_name":"PreToolUse","session_id":"native-session",
        "cwd":f.0,"tool_name":"Bash","tool_use_id":"first", "tool_input":{"command":"private argument"}});
    assert_eq!(context(&f, event.clone()), json!({}));
    let path = f.run().join("native-context-first-PreToolUse.json");
    let before = fs::read_to_string(&path).unwrap();
    assert!(!before.contains("private argument"));
    let receipt: serde_json::Value = serde_json::from_str(&before).unwrap();
    assert_eq!(receipt["tool_use_id"], "first");
    assert_eq!(receipt["mode"], "observe");
    event["tool_use_id"] = json!("second");
    assert_eq!(context(&f, event), json!({}));
    assert_eq!(before, fs::read_to_string(path).unwrap());
}

#[test]
fn held_proposal_survives_restart_then_requires_current_publication() {
    let f = Fixture::new();
    let (mut s, proposal) = f.submit(Mode::Enforce);
    assert_eq!(s.runtime.outstanding().unwrap().role, Role::Coordinator);
    assert!(s.request().is_err());
    drop(s);
    let mut s = Session::open(&f.run()).unwrap();
    assert_eq!(
        s.decisions.pending.as_ref().unwrap().proposal.assignment,
        proposal.assignment
    );
    s.decision_result(f.result(Verdict::NoFinding)).unwrap();
    assert!(s.request().is_err());
    fs::write(
        f.0.join("selection.md"),
        format!("Historical mention: {}", proposal.assignment),
    )
    .unwrap();
    assert!(s.confirm_publication(1).is_err());
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    // A later edit cannot silently replace the cleared decision before dispatch.
    fs::write(f.0.join("selection.md"), "Changed current selection").unwrap();
    assert!(s.request().is_err());
    f.publish(&s);
    assert_eq!(s.request().unwrap().role, Role::Worker);
}

#[test]
fn unbound_malformed_and_duplicate_returns_do_not_adopt() {
    let f = Fixture::new();
    let (mut s, _) = f.submit(Mode::Enforce);
    let mut wrong = f.result(Verdict::NoFinding);
    wrong.backend_handle = "another-call".into();
    assert!(s.decision_result(wrong).is_err());
    let mut wrong = f.result(Verdict::Revise);
    wrong.findings[0].policy_excerpt = "invented rule".into();
    assert!(s.decision_result(wrong).is_err());
    assert!(s.decisions.holds());
    s.decision_result(f.result(Verdict::NoFinding)).unwrap();
    assert!(s.decision_result(f.result(Verdict::NoFinding)).is_err());
}

#[test]
fn expiry_retains_late_reply_without_creating_a_finding_hold() {
    let f = Fixture::new();
    let (mut s, _) = f.submit(Mode::Enforce);
    s.decisions.pending.as_mut().unwrap().deadline_ms = 0;
    s.decision_result(f.result(Verdict::Revise)).unwrap();
    assert!(s.decisions.pending.is_none());
    let receipt = &s.decisions.receipts[0];
    assert_eq!(
        receipt.result.as_ref().unwrap().verdict,
        Verdict::Unavailable
    );
    assert_eq!(receipt.late_returns.len(), 1);
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    assert_eq!(s.request().unwrap().role, Role::Worker);
}

#[test]
fn concrete_finding_requires_owner_and_cannot_expire_or_be_disabled() {
    let f = Fixture::new();
    let (mut s, _) = f.submit(Mode::Enforce);
    s.decision_result(f.result(Verdict::Revise)).unwrap();
    s.decisions.pending.as_mut().unwrap().deadline_ms = 0;
    s.expire_decision().unwrap();
    assert!(s.decisions.holds());
    assert!(s.configure_decisions(f.config(Mode::Disabled)).is_err());
    assert!(s.abandon_decision("drop critique".into()).is_err());
    s.resolve_decision(f.owner(Disposition::Contested, None))
        .unwrap();
    assert_eq!(
        s.decisions.receipts[0].result.as_ref().unwrap().verdict,
        Verdict::Revise
    );
    assert_eq!(
        s.decisions.receipts[0].owner.as_ref().unwrap().disposition,
        Disposition::Contested
    );
    assert!(s.decisions.pending.is_none());
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    assert_eq!(s.request().unwrap().role, Role::Worker);
}

#[test]
fn revised_content_is_published_without_a_second_check() {
    let f = Fixture::new();
    let (mut s, mut p) = f.submit(Mode::Enforce);
    s.decision_result(f.result(Verdict::Revise)).unwrap();
    p.assignment = "Corrected complete mechanism and interactions".into();
    s.resolve_decision(f.owner(Disposition::Revised, Some(p.clone())))
        .unwrap();
    assert_eq!(s.decisions.next_id, 1);
    assert_eq!(
        s.decisions.publication.as_ref().unwrap().proposal["assignment"],
        p.assignment
    );
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    assert_eq!(s.request().unwrap().role, Role::Worker);
}

#[test]
fn missing_policy_returns_stale_proposal_to_owner_and_allows_disablement() {
    let f = Fixture::new();
    let (mut s, _) = f.submit(Mode::Enforce);
    fs::remove_file(f.0.join("policy.md")).unwrap();
    s.decisions.pending.as_mut().unwrap().deadline_ms = 0;
    s.expire_decision().unwrap();
    assert!(!s.decisions.holds());
    assert_eq!(s.runtime.outstanding().unwrap().role, Role::Coordinator);
    s.configure_decisions(f.config(Mode::Disabled)).unwrap();
}

#[test]
fn changed_sources_never_adopt_the_previously_checked_proposal() {
    let f = Fixture::new();
    let (mut s, _) = f.submit(Mode::Enforce);
    fs::write(f.0.join("method.txt"), "Materially changed owner input\n").unwrap();
    s.decision_result(f.result(Verdict::NoFinding)).unwrap();
    assert_eq!(s.runtime.outstanding().unwrap().role, Role::Coordinator);
    assert!(s.decisions.publication.is_none());
    assert!(s.decisions.pending.is_none());
}

#[test]
fn observation_mode_never_blocks_work_even_when_checker_disagrees() {
    let f = Fixture::new();
    let (mut s, _) = f.submit(Mode::Observe);
    assert_eq!(s.request().unwrap().role, Role::Worker);
    s.decision_result(f.result(Verdict::Revise)).unwrap();
    assert!(!s.decisions.holds());
    assert!(s.decisions.receipts[0].observed_only);
}

#[test]
fn prose_and_progress_reuse_judgment_but_material_investment_changes_do_not() {
    let f = Fixture::new();
    let (_s, mut p) = f.start(Mode::Observe);
    let mut g = Guard {
        config: Some(f.config(Mode::Observe)),
        ..Guard::default()
    };
    assert!(!g.consider(&p, vec![], "role evidence".into()).unwrap());
    g.pending = None;
    p.assignment = "Implement the next internal step".into();
    p.update.as_mut().unwrap().remaining_work.clear();
    p.update.as_mut().unwrap().rationale = "Restated reasoning without a new investment".into();
    p.update.as_mut().unwrap().reverse_when = "Clarified wording of the same switch".into();
    p.update.as_mut().unwrap().options[0].work[0].work = "Clarified internal work".into();
    assert!(!g.consider(&p, vec![], "role evidence".into()).unwrap());
    assert_eq!(g.next_id, 1);
    assert!(g.pending.is_none());
    p.update.as_mut().unwrap().options[0].prerequisites.push(
        workflow_harness::contract::Prerequisite {
            reason: "Wait for incumbent failure".into(),
            source: 0,
        },
    );
    p.update.as_mut().unwrap().investment_changed = true;
    assert!(!g.consider(&p, vec![], "role evidence".into()).unwrap());
    assert_eq!(g.next_id, 2);
    assert!(g.pending.is_some());
}

#[test]
fn accepted_resolver_judgment_is_reused_without_a_second_model_check() {
    let f = Fixture::new();
    let (mut s, mut p) = f.start(Mode::Enforce);
    p.decision = workflow_harness::Decision::Reconsider;
    s.accept(p.clone()).unwrap();
    let resolver = s.request().unwrap();
    assert_eq!(resolver.role, Role::Resolver);
    assert!(resolver.prompt.contains("Do not require incumbent failure"));
    let mut r = p.clone();
    r.invocation_id = resolver.invocation_id;
    r.role = Role::Resolver;
    r.decision = workflow_harness::Decision::Work;
    s.accept(r).unwrap();
    let owner = s.request().unwrap();
    p.invocation_id = owner.invocation_id;
    p.decision = workflow_harness::Decision::Work;
    p.update.as_mut().unwrap().resolved_invocation = Some(resolver.invocation_id);
    s.accept(p).unwrap();
    assert!(s.decisions.pending.is_none());
    let receipt = &s.decisions.receipts[0];
    assert_eq!(receipt.reused_invocation, Some(resolver.invocation_id));
    assert!(receipt.result.is_none()); // Reuse is not a fabricated no_finding verdict.
    assert!(receipt.backend_handle.is_none());
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    assert_eq!(s.request().unwrap().role, Role::Worker);
}

#[test]
fn external_judgment_reuse_needs_delivered_sources_and_survives_restart() {
    let f = Fixture::new();
    let (mut s, mut p) = f.start(Mode::Observe);
    p.update.as_mut().unwrap().resolved_by = vec![99];
    assert!(s.accept(p.clone()).is_err());
    p.update.as_mut().unwrap().resolved_by = vec![0];
    s.accept(p).unwrap();
    drop(s);
    let mut s = Session::open(&f.run()).unwrap();
    assert!(s.decisions.pending.is_none());
    assert_eq!(s.decisions.receipts[0].reused_sources, vec![0]);
    assert!(s.decisions.receipts[0].result.is_none());
    assert_eq!(s.request().unwrap().role, Role::Worker);
}

#[test]
fn an_unaccepted_invocation_cannot_stand_in_for_independent_judgment() {
    let f = Fixture::new();
    let (mut s, mut p) = f.start(Mode::Observe);
    p.update.as_mut().unwrap().resolved_invocation = Some(p.invocation_id);
    assert!(s.accept(p).is_err());
    assert!(s.decisions.receipts.is_empty());
}

#[test]
fn owner_boundary_uses_existing_pause_without_stranding_original_return() {
    let f = Fixture::new();
    let (mut s, _) = f.submit(Mode::Enforce);
    s.decision_result(f.result(Verdict::Revise)).unwrap();
    s.resolve_decision(f.owner(Disposition::Boundary, None))
        .unwrap();
    assert!(s.decisions.pending.is_none());
    assert!(s.runtime.outstanding().is_none());
    assert!(s.request().is_err());
    s.runtime.unpause().unwrap();
    assert_ne!(s.request().unwrap().role, Role::Worker);
}
