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
            "summary":"Mechanical test only", "assignment":"Develop the complete mechanism", "actual_use":[self.0.join("method.txt")], "evidence":[self.0.join("method.txt")],
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
    let previous = workflow_harness::decision::projection(&p, &[]).unwrap();
    p.assignment = "Implement the next internal step".into();
    p.update.as_mut().unwrap().remaining_work.clear();
    p.update.as_mut().unwrap().rationale = "Restated reasoning without a new investment".into();
    p.update.as_mut().unwrap().reverse_when = "Clarified wording of the same switch".into();
    p.update.as_mut().unwrap().options[0].work[0].work = "Clarified internal work".into();
    p.update.as_mut().unwrap().judgment_reuse = Some(workflow_harness::decision::JudgmentReuse {
        previous: workflow_harness::decision::projection_identity(&previous).unwrap(),
        current: workflow_harness::decision::projection_identity(
            &workflow_harness::decision::projection(&p, &[]).unwrap(),
        )
        .unwrap(),
        reason: "The internal step and wording preserve the selected consequence".into(),
    });
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

fn read_policy_link_from_delivered_source(input: &str) {
    let locator = input
        .lines()
        .find_map(|line| line.strip_prefix("Policy source (JSON path): "))
        .unwrap();
    let source: PathBuf = serde_json::from_str(locator).unwrap();
    let policy = fs::read_to_string(&source).unwrap();
    assert!(input.contains(&policy));
    let target = policy
        .split_once("](")
        .unwrap()
        .1
        .split_once(')')
        .unwrap()
        .0;
    let linked = source
        .parent()
        .unwrap()
        .join(target.split('#').next().unwrap());
    assert!(!fs::read_to_string(linked).unwrap().trim().is_empty());
}

#[test]
fn installed_policy_reaches_coordinator_and_resolver_unchanged() {
    let f = Fixture::new();
    let policy_path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("decision-policy.md");
    let policy = fs::read_to_string(&policy_path).unwrap();
    let mut session = Session::create(f.task(), &f.run()).unwrap();
    let mut config = f.config(Mode::Observe);
    config.policy = policy_path;
    session.configure_decisions(config).unwrap();
    let coordinator = session.request().unwrap();
    assert_eq!(coordinator.role, Role::Coordinator);
    assert!(coordinator.prompt.contains(&format!(
        "\nParticipating investment policy:\n{policy}\nApply this in the existing investment judgment once."
    )));
    read_policy_link_from_delivered_source(&coordinator.prompt);
    let response = serde_json::from_value(json!({
        "invocation_id": coordinator.invocation_id,
        "role": "coordinator", "decision": "reconsider",
        "summary": "Check installed policy delivery", "assignment": "Compare the current alternatives",
        "update": {"remaining_work": [], "interpretation": "Delivery check only"}
    })).unwrap();
    session.accept(response).unwrap();
    let resolver = session.request().unwrap();
    assert_eq!(resolver.role, Role::Resolver);
    assert!(resolver.prompt.contains(&format!(
        "\nParticipating investment policy:\n{policy}\nApply this in the existing investment judgment once."
    )));
    read_policy_link_from_delivered_source(&resolver.prompt);
}

#[test]
fn independent_check_delivers_the_configured_policy_location() {
    let f = Fixture::new();
    let (_, proposal) = f.start(Mode::Disabled);
    let mut config = f.config(Mode::Observe);
    config.policy = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("decision-policy.md");
    let mut guard = Guard {
        config: Some(config),
        ..Guard::default()
    };
    guard
        .consider(&proposal, vec![], "Existing role input".into())
        .unwrap();
    read_policy_link_from_delivered_source(&guard.pending.as_ref().unwrap().input);
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
fn supplied_but_unassociated_judgment_cannot_silently_skip_the_checker() {
    let f = Fixture::new();
    let (mut s, mut p) = f.start(Mode::Observe);
    p.update.as_mut().unwrap().resolved_by = vec![99];
    assert!(s.accept(p.clone()).is_err());
    p.update.as_mut().unwrap().resolved_by = vec![0];
    s.accept(p).unwrap();
    drop(s);
    let mut s = Session::open(&f.run()).unwrap();
    assert!(s.decisions.pending.is_some());
    assert!(s.decisions.receipts.is_empty());
    // Observe mode records the coverage gap without becoming an enforcement path.
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

fn current_use(f: &Fixture, blocked: bool) -> workflow_harness::current_use::CurrentUse {
    workflow_harness::current_use::CurrentUse::capture(
        f.0.join("policy.md"),
        vec![f.0.join("method.txt")],
        vec!["confirmed-restriction".into()],
        if blocked {
            vec!["confirmed-restriction".into()]
        } else {
            vec![]
        },
    )
    .unwrap()
}

#[test]
fn current_use_survives_restart_omission_and_owner_transfer() {
    let f = Fixture::new();
    let (mut session, response) = f.start(Mode::Disabled);
    session.adopt_current_use(current_use(&f, true)).unwrap();
    drop(session);
    let mut session = Session::open(&f.run()).unwrap();
    assert!(
        session
            .accept(response.clone())
            .unwrap_err()
            .contains("unresolved")
    );
    let mut omitted = current_use(&f, false);
    omitted.correction_ids.clear();
    assert!(
        session
            .adopt_current_use(omitted)
            .unwrap_err()
            .contains("dropped")
    );
    let mut transfer = current_use(&f, true);
    transfer.owner = f.0.join("successor.md");
    fs::write(&transfer.owner, "Successor owns the same affected work").unwrap();
    transfer
        .files
        .push(workflow_harness::current_use::SavedFile {
            path: transfer.owner.clone(),
            contents: fs::read_to_string(&transfer.owner).unwrap(),
        });
    session.adopt_current_use(transfer).unwrap();
    assert!(
        session
            .accept(response.clone())
            .unwrap_err()
            .contains("unresolved")
    );
    // A scoped advisory/unrelated binding carries the association without a hold.
    session.adopt_current_use(current_use(&f, false)).unwrap();
    session.accept(response).unwrap();
    assert_eq!(session.request().unwrap().role, Role::Worker);
}

#[test]
fn current_use_rejects_stale_queue_at_consumption_and_owner_can_replace_it() {
    let f = Fixture::new();
    let (mut session, response) = f.start(Mode::Disabled);
    session.adopt_current_use(current_use(&f, false)).unwrap();
    session.accept(response).unwrap();
    let old = session.request().unwrap();
    assert!(
        old.prompt
            .contains(f.0.join("method.txt").to_str().unwrap())
    );
    assert!(old.prompt.contains("Retained correction references"));
    fs::write(f.0.join("unrelated.txt"), "Unrelated progress").unwrap();
    session.verify_current_use_consumption().unwrap();
    fs::write(
        f.0.join("method.txt"),
        "Saved corrected assignment, not committed\n",
    )
    .unwrap();
    assert!(
        session
            .begin_execution(Default::default())
            .unwrap_err()
            .contains("changed")
    );
    assert!(session.check_action().unwrap_err().contains("changed"));
    assert!(session.continuation().unwrap_err().contains("changed"));
    session.adopt_current_use(current_use(&f, false)).unwrap();
    // Updating only the native/owner pointer cannot authorize the stale queued task.
    assert!(
        session
            .verify_current_use_consumption()
            .unwrap_err()
            .contains("older")
    );
    assert!(session.request().is_err());
    drop(session);
    let mut session = Session::open(&f.run()).unwrap();
    assert!(session.verify_current_use_consumption().is_err());
    let replacement = session
        .replace_queued_work(
            "Investigate the unrestricted objective using the saved corrected task".into(),
        )
        .unwrap();
    assert_ne!(old.invocation_id, replacement.invocation_id);
    assert!(replacement.prompt.contains("supersedes"));
    assert!(
        session
            .verify_queued_current_use(&old)
            .unwrap_err()
            .contains("obsolete")
    );
    session.verify_queued_current_use(&replacement).unwrap();
    session.verify_current_use_consumption().unwrap();
    session
        .begin_execution(workflow_harness::control::Capabilities {
            fresh_context: true,
            events: true,
            controlled_continuation: true,
            ..Default::default()
        })
        .unwrap();
    assert!(
        session
            .replace_queued_work("Do not duplicate started work".into())
            .is_err()
    );
}

#[test]
fn current_use_cannot_be_released_by_revised_or_contested_owner_labels() {
    for disposition in [Disposition::Revised, Disposition::Contested] {
        let f = Fixture::new();
        let (mut session, response) = f.submit(Mode::Enforce);
        session.decision_result(f.result(Verdict::Revise)).unwrap();
        session.adopt_current_use(current_use(&f, true)).unwrap();
        let proposal = (disposition == Disposition::Revised).then_some(response);
        assert!(
            session
                .resolve_decision(f.owner(disposition, proposal))
                .unwrap_err()
                .contains("unresolved")
        );
        assert!(session.decisions.pending.is_some());
    }
}

#[test]
fn current_use_bypasses_no_new_investment_flag_without_an_extra_checker() {
    let f = Fixture::new();
    let (mut session, mut response) = cleared_session(&f);
    response.invocation_id = complete_worker(&mut session, &response);
    assert!(!response.update.as_ref().unwrap().investment_changed);
    session.adopt_current_use(current_use(&f, true)).unwrap();
    assert!(
        session
            .accept(response.clone())
            .unwrap_err()
            .contains("unresolved")
    );
    assert!(session.decisions.pending.is_none());
    session.adopt_current_use(current_use(&f, false)).unwrap();
    session.accept(response).unwrap();
    assert!(session.decisions.pending.is_none());
    assert_eq!(session.request().unwrap().role, Role::Worker);
}

#[test]
fn current_use_legacy_process_consumption_checks_before_creating_dispatch_files() {
    let f = Fixture::new();
    let mut task = f.task();
    task.research = None;
    let mut session = Session::create(task, &f.run()).unwrap();
    let coordinator = session.request().unwrap();
    let response = Response {
        invocation_id: coordinator.invocation_id,
        role: Role::Coordinator,
        decision: workflow_harness::Decision::Work,
        summary: "Owner selected bounded work".into(),
        assignment: "Use the saved adopted assignment".into(),
        actual_use: vec![f.0.join("method.txt")],
        evidence: vec![],
        update: None,
    };
    session.adopt_current_use(current_use(&f, false)).unwrap();
    session.accept(response).unwrap();
    let request = session.request().unwrap();
    assert_eq!(request.protocol, "workflow-invocation/1");
    fs::write(
        f.0.join("policy.md"),
        "Correction superseded the saved owner record",
    )
    .unwrap();
    let adapter = workflow_harness::session::ProcessAdapter {
        program: "/nonexistent".into(),
        args: vec![],
    };
    assert!(session.invoke(&adapter).unwrap_err().contains("changed"));
    assert!(
        !f.run()
            .join(format!("stdout-{}.json", request.invocation_id))
            .exists()
    );
}

#[test]
fn native_current_use_pointer_is_advisory_even_for_known_blocking_findings() {
    let f = Fixture::new();
    let (directory, event) = adopted_fixture(&f);
    let path = directory.join("owner.json");
    let mut binding: serde_json::Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
    binding["current_use"] =
        json!({"correction_ids":["known-restriction"], "blocked_ids":["known-restriction"]});
    fs::write(path, binding.to_string()).unwrap();
    let output = context_mode(&f, event, true);
    let message = output["hookSpecificOutput"]["additionalContext"]
        .as_str()
        .unwrap();
    assert!(message.contains("known-restriction"));
    assert!(message.contains("check-current-use"));
    assert!(message.contains("neither validates"));
    assert!(output["hookSpecificOutput"]["permissionDecision"].is_null());
}

fn current_use_cli(f: &Fixture, command: &str, file: &std::path::Path) -> std::process::Output {
    std::process::Command::new(env!("CARGO_BIN_EXE_workflow-harness"))
        .args(["host", command])
        .arg(f.run())
        .arg(file)
        .output()
        .unwrap()
}

#[test]
fn host_cli_imports_owner_report_and_replaces_only_unstarted_current_request() {
    let f = Fixture::new();
    let (mut session, response) = f.start(Mode::Disabled);
    session.accept(response).unwrap();
    let old = session.request().unwrap();
    let old_file = f.0.join("old-request.json");
    fs::write(&old_file, serde_json::to_vec(&old).unwrap()).unwrap();
    drop(session);
    let report = f.0.join("owner-report.json");
    fs::write(
        &report,
        json!({"current_use":current_use(&f, false), "scope":"existing owner validation"})
            .to_string(),
    )
    .unwrap();
    assert!(
        current_use_cli(&f, "current-use-adopt", &report)
            .status
            .success()
    );
    // Attaching a new current binding does not silently update a queued request.
    assert!(
        !current_use_cli(&f, "current-use-check", &old_file)
            .status
            .success()
    );
    let assignment = f.0.join("corrected-assignment.txt");
    fs::write(
        &assignment,
        "Inspect the corrected saved task and acquire the selected observation",
    )
    .unwrap();
    let replacement = current_use_cli(&f, "current-use-replace", &assignment);
    assert!(
        replacement.status.success(),
        "{}",
        String::from_utf8_lossy(&replacement.stderr)
    );
    let request: workflow_harness::Invocation =
        serde_json::from_slice(&replacement.stdout).unwrap();
    assert_ne!(request.invocation_id, old.invocation_id);
    assert!(request.prompt.contains("supersedes"));
    let replacement_file = f.0.join("replacement-request.json");
    fs::write(&replacement_file, replacement.stdout).unwrap();
    assert!(
        current_use_cli(&f, "current-use-check", &replacement_file)
            .status
            .success()
    );
    assert!(
        !current_use_cli(&f, "current-use-check", &old_file)
            .status
            .success()
    );
    let mut session = Session::open(&f.run()).unwrap();
    session
        .begin_execution(workflow_harness::control::Capabilities {
            fresh_context: true,
            events: true,
            controlled_continuation: true,
            ..Default::default()
        })
        .unwrap();
    drop(session);
    assert!(
        !current_use_cli(&f, "current-use-replace", &assignment)
            .status
            .success()
    );
}

#[test]
fn host_cli_import_retains_blocking_findings_and_rejects_stale_saved_report() {
    let f = Fixture::new();
    let (session, response) = f.start(Mode::Disabled);
    drop(session);
    let report = f.0.join("snapshot.json");
    fs::write(&report, serde_json::to_vec(&current_use(&f, true)).unwrap()).unwrap();
    assert!(
        current_use_cli(&f, "current-use-adopt", &report)
            .status
            .success()
    );
    let mut session = Session::open(&f.run()).unwrap();
    assert!(session.accept(response).unwrap_err().contains("unresolved"));
    drop(session);
    fs::write(f.0.join("method.txt"), "Changed after report preparation\n").unwrap();
    assert!(
        !current_use_cli(&f, "current-use-adopt", &report)
            .status
            .success()
    );
}

#[test]
fn refreshed_current_use_preserves_started_host_return_handshake() {
    use workflow_harness::control::{Event, EventKind};
    for blocked in [false, true] {
        let f = Fixture::new();
        let (mut session, mut response) = f.start(Mode::Disabled);
        session.adopt_current_use(current_use(&f, false)).unwrap();
        session.accept(response.clone()).unwrap();
        let worker = session.request().unwrap();
        session
            .bind_host(workflow_harness::session::HostBinding {
                invocation_id: worker.invocation_id,
                backend_handle: "existing-worker".into(),
            })
            .unwrap();
        session
            .begin_execution(workflow_harness::control::Capabilities {
                fresh_context: true,
                events: true,
                controlled_continuation: true,
                ..Default::default()
            })
            .unwrap();
        session
            .event(Event {
                invocation_id: worker.invocation_id,
                sequence: 1,
                event: EventKind::Boundary {
                    reason: "Selected observation is ready".into(),
                    return_due: true,
                    effects_settled: true,
                },
            })
            .unwrap();
        fs::write(
            f.0.join("policy.md"),
            "Owner saved an ordinary metadata update\n",
        )
        .unwrap();
        drop(session);
        let report = f.0.join("refreshed-report.json");
        fs::write(
            &report,
            json!({"current_use":current_use(&f, blocked)}).to_string(),
        )
        .unwrap();
        assert!(
            current_use_cli(&f, "current-use-adopt", &report)
                .status
                .success()
        );
        let decision = host(&f, "continuation", json!("existing-worker"));
        assert_eq!(decision["decision"], "return");
        let reasons = decision["reasons"].as_array().unwrap();
        assert!(reasons.iter().any(|r| {
            r.as_str()
                .unwrap()
                .contains("Selected observation is ready")
        }));
        assert!(reasons.iter().any(|r| {
            r.as_str()
                .unwrap()
                .contains("Current-use owner reconciliation")
        }));
        let mut session = Session::open(&f.run()).unwrap();
        let execution = session.runtime.execution().unwrap();
        assert!(!execution.awaiting_continuation);
        assert!(execution.continuation_withheld);
        assert!(execution.effects_settled);
        assert!(
            session
                .replace_queued_work("Do not restart settled work".into())
                .is_err()
        );
        session
            .event(Event {
                invocation_id: worker.invocation_id,
                sequence: 2,
                event: EventKind::Stopped {
                    effects_settled: true,
                },
            })
            .unwrap();
        response.invocation_id = worker.invocation_id;
        response.role = Role::Worker;
        response.decision = workflow_harness::Decision::Observed;
        session
            .accept_host_return("existing-worker", response)
            .unwrap();
        assert_eq!(session.request().unwrap().role, Role::Coordinator);
    }
}

#[test]
fn changed_current_use_returns_started_actions_without_claiming_settlement() {
    use workflow_harness::control::{Continuation, Event, EventKind};
    let f = Fixture::new();
    let (mut session, response) = f.start(Mode::Disabled);
    session.adopt_current_use(current_use(&f, false)).unwrap();
    session.accept(response).unwrap();
    let worker = session.request().unwrap();
    session
        .begin_execution(workflow_harness::control::Capabilities {
            fresh_context: true,
            events: true,
            controlled_continuation: true,
            ..Default::default()
        })
        .unwrap();
    fs::write(
        f.0.join("policy.md"),
        "Owner changed after execution started\n",
    )
    .unwrap();
    let decision = session.check_action().unwrap();
    assert!(
        matches!(decision, Continuation::Return { reasons } if reasons.iter().any(|reason| reason.contains("Current-use owner reconciliation")))
    );
    assert!(!session.runtime.execution().unwrap().effects_settled);
    drop(session);
    let mut session = Session::open(&f.run()).unwrap();
    assert!(session.runtime.execution().unwrap().continuation_withheld);
    assert!(matches!(
        session.check_action().unwrap(),
        Continuation::Return { .. }
    ));
    session
        .event(Event {
            invocation_id: worker.invocation_id,
            sequence: 1,
            event: EventKind::Stopped {
                effects_settled: false,
            },
        })
        .unwrap();
    assert!(!session.runtime.execution().unwrap().effects_settled);
}

#[test]
fn checked_independent_scope_cannot_clear_an_affected_assignment() {
    use workflow_harness::current_use::CurrentUse;
    let f = Fixture::new();
    let (mut session, mut response) = f.start(Mode::Disabled);
    fs::write(f.0.join("independent.md"), "Independent useful task").unwrap();
    let independent = CurrentUse::capture(
        f.0.join("policy.md"),
        vec![f.0.join("independent.md")],
        vec!["confirmed-restriction".into()],
        vec![],
    )
    .unwrap();
    session.adopt_current_use(independent).unwrap();
    // Assignment scope comes from the owner, not from the passing report's files.
    assert!(
        session
            .accept(response.clone())
            .unwrap_err()
            .contains("scope differs")
    );
    response.actual_use = vec![f.0.join("independent.md")];
    response.assignment = "Complete only the independently selected task".into();
    session.accept(response).unwrap();
    let request = session.request().unwrap();
    assert_eq!(
        request.actual_use,
        vec![fs::canonicalize(f.0.join("independent.md")).unwrap()]
    );
    assert!(
        request
            .prompt
            .contains("Exact retained context and validation evidence")
    );
    assert!(
        session
            .runtime
            .read_context_evidence("/current_use/files")
            .unwrap()
            .to_string()
            .contains("Independent useful task")
    );
    session.verify_queued_current_use(&request).unwrap();
    let mut substituted = request.clone();
    substituted.actual_use = vec![f.0.join("method.txt")];
    assert!(
        session
            .verify_queued_current_use(&substituted)
            .unwrap_err()
            .contains("different queued request")
    );
}

#[test]
fn participating_request_without_actual_scope_is_not_implicitly_covered() {
    let f = Fixture::new();
    let (mut session, mut response) = f.start(Mode::Disabled);
    session.adopt_current_use(current_use(&f, false)).unwrap();
    response.actual_use.clear();
    assert!(
        session
            .accept(response)
            .unwrap_err()
            .contains("coverage unavailable")
    );
    // A legacy report is readable for retention but does not invent checked scope.
    let mut legacy = serde_json::to_value(current_use(&f, false)).unwrap();
    legacy.as_object_mut().unwrap().remove("checked_sources");
    let legacy: workflow_harness::current_use::CurrentUse = serde_json::from_value(legacy).unwrap();
    assert!(
        legacy
            .require_ready_for(&[f.0.join("method.txt")])
            .unwrap_err()
            .contains("coverage unavailable")
    );
}

#[test]
fn actual_scope_is_retained_across_queue_refresh_and_started_return() {
    use workflow_harness::control::{Continuation, Event, EventKind};
    use workflow_harness::current_use::CurrentUse;
    let f = Fixture::new();
    let (mut session, response) = f.start(Mode::Disabled);
    session.adopt_current_use(current_use(&f, false)).unwrap();
    session.accept(response).unwrap();
    let old = session.request().unwrap();
    fs::write(
        f.0.join("successor.md"),
        "Owner-selected corrected successor task",
    )
    .unwrap();
    // Python establishes the successor relation; Rust receives that scoped result.
    let successor = CurrentUse::capture(
        f.0.join("policy.md"),
        vec![f.0.join("successor.md")],
        vec!["confirmed-restriction".into()],
        vec![],
    )
    .unwrap();
    session.adopt_current_use(successor).unwrap();
    assert!(
        session
            .verify_queued_current_use(&old)
            .unwrap_err()
            .contains("scope differs")
    );
    assert!(
        session
            .replace_queued_work("Use successor".into())
            .unwrap_err()
            .contains("scope differs")
    );
    drop(session);
    let assignment = f.0.join("successor-assignment.txt");
    fs::write(&assignment, "Use the adopted successor task").unwrap();
    let replacement = std::process::Command::new(env!("CARGO_BIN_EXE_workflow-harness"))
        .args(["host", "current-use-replace"])
        .arg(f.run())
        .arg(&assignment)
        .arg(f.0.join("successor.md"))
        .output()
        .unwrap();
    assert!(
        replacement.status.success(),
        "{}",
        String::from_utf8_lossy(&replacement.stderr)
    );
    let request: workflow_harness::Invocation =
        serde_json::from_slice(&replacement.stdout).unwrap();
    let session = Session::open(&f.run()).unwrap();
    assert!(session.verify_queued_current_use(&old).is_err());
    session.verify_queued_current_use(&request).unwrap();
    drop(session);
    let mut session = Session::open(&f.run()).unwrap();
    session.verify_queued_current_use(&request).unwrap();
    session
        .begin_execution(workflow_harness::control::Capabilities {
            fresh_context: true,
            events: true,
            controlled_continuation: true,
            ..Default::default()
        })
        .unwrap();
    session.adopt_current_use(current_use(&f, false)).unwrap();
    session
        .event(Event {
            invocation_id: request.invocation_id,
            sequence: 1,
            event: EventKind::Boundary {
                reason: "Existing work returns".into(),
                return_due: false,
                effects_settled: false,
            },
        })
        .unwrap();
    let decision = session.continuation().unwrap();
    assert!(
        matches!(decision, Continuation::Return { reasons } if reasons.iter().any(|reason| reason.contains("scope differs")))
    );
    assert!(!session.runtime.execution().unwrap().effects_settled);
}

#[test]
fn actual_scoped_bytes_changed_after_preparation_reject_dispatch_without_new_review() {
    let f = Fixture::new();
    let (mut session, response) = f.start(Mode::Disabled);
    session.adopt_current_use(current_use(&f, false)).unwrap();
    session.accept(response).unwrap();
    let request = session.request().unwrap();
    fs::write(f.0.join("unrelated.txt"), "Unrelated change").unwrap();
    session.verify_queued_current_use(&request).unwrap();
    fs::write(
        f.0.join("method.txt"),
        "Scope source changed after preparation\n",
    )
    .unwrap();
    assert!(
        session
            .begin_execution(Default::default())
            .unwrap_err()
            .contains("source changed")
    );
    assert!(session.runtime.execution().is_none());
    assert!(session.decisions.pending.is_none());
}

#[test]
fn deciding_roles_receive_full_controlling_context_despite_local_excerpt_and_role_filter() {
    let f = Fixture::new();
    fs::write(f.0.join("objective.md"), "Historical method: stay with the incumbent.\nCurrent objective: maximize the overall useful outcome, with alternative methods allowed.\n").unwrap();
    let mut task = f.task();
    task.controlling_objective = Some(task.sources.len());
    task.sources.push(workflow_harness::Source {
        path: "objective.md".into(),
        first_line: 1,
        last_line: 1,
        purpose: "controlling objective".into(),
        roles: vec![Role::Worker],
    });
    let mut session = Session::create(task, &f.run()).unwrap();
    let request = session.request().unwrap();
    for text in [
        "Declared controlling objective source",
        "Current objective: maximize",
        "Full source context follows once",
        "Historical method:",
        "local task",
    ] {
        assert!(request.prompt.contains(text));
    }
    let response: Response = serde_json::from_value(json!({"invocation_id":request.invocation_id,"role":"coordinator","decision":"reconsider",
        "summary":"Resolve objective-level question", "update":{"remaining_work":[],"interpretation":"Retain current controlling source"}})).unwrap();
    session.accept(response).unwrap();
    // Cold resumption needs no fresh returned decision or correction enrollment.
    drop(session);
    let mut session = Session::open(&f.run()).unwrap();
    let resolver = session.request().unwrap();
    assert_eq!(resolver.role, Role::Resolver);
    assert!(resolver.prompt.contains("Current objective: maximize"));
    assert!(
        resolver
            .prompt
            .contains("Judge the current source role and authority")
    );
}

#[test]
fn standalone_task_keeps_ordinary_source_delivery_and_invalid_controlling_reference_fails() {
    let f = Fixture::new();
    let mut session = Session::create(f.task(), &f.run()).unwrap();
    assert!(
        !session
            .request()
            .unwrap()
            .prompt
            .contains("Declared controlling objective source")
    );
    let mut invalid = f.task();
    invalid.controlling_objective = Some(99);
    assert!(
        workflow_harness::Runtime::new(invalid)
            .unwrap_err()
            .contains("existing supplied source")
    );
}

#[test]
fn controlling_body_changes_outside_excerpt_reach_existing_source_checks() {
    use workflow_harness::control::{Capabilities, Continuation};
    for phase in ["return", "request", "started"] {
        let f = Fixture::new();
        let objective = f.0.join("objective.md");
        fs::write(
            &objective,
            "Historical method.\nCurrent authority permits A.\n",
        )
        .unwrap();
        let mut task = f.task();
        task.research = None;
        task.controlling_objective = Some(task.sources.len());
        task.sources.push(workflow_harness::Source {
            path: "objective.md".into(),
            first_line: 1,
            last_line: 1,
            purpose: "objective".into(),
            roles: vec![Role::Worker],
        });
        let mut session = Session::create(task, &f.run()).unwrap();
        let coordinator = session.request().unwrap();
        assert!(coordinator.prompt.contains("Current authority permits A."));
        let response: Response = serde_json::from_value(json!({
            "invocation_id": coordinator.invocation_id, "role": "coordinator",
            "decision": "work", "summary": "Use delivered objective", "assignment": "Perform A"
        }))
        .unwrap();
        if phase != "return" {
            session.accept(response.clone()).unwrap();
        }
        if phase == "started" {
            assert_eq!(session.request().unwrap().role, Role::Worker);
            session
                .begin_execution(Capabilities {
                    events: true,
                    controlled_continuation: true,
                    ..Default::default()
                })
                .unwrap();
        }
        // Persist the snapshot across restart before the previously omitted body changes.
        drop(session);
        fs::write(
            &objective,
            "Historical method.\nCurrent authority prohibits A; use B.\n",
        )
        .unwrap();
        let mut session = Session::open(&f.run()).unwrap();
        if phase == "return" {
            session.accept(response).unwrap();
        }
        if phase == "started" {
            assert!(
                matches!(session.check_action().unwrap(), Continuation::Return { reasons }
                if reasons.iter().any(|reason| reason.contains("Selected decision inputs")))
            );
            assert!(!session.runtime.execution().unwrap().effects_settled);
        } else {
            let next = session.request().unwrap();
            assert_eq!(next.role, Role::Coordinator, "phase {phase}");
            assert!(
                next.prompt
                    .contains("Current authority prohibits A; use B.")
            );
        }
    }
}

#[test]
fn unselected_noncontrolling_body_change_keeps_supported_assignment() {
    let f = Fixture::new();
    fs::write(
        f.0.join("method.txt"),
        "Selected method.\nUnselected historical note.\n",
    )
    .unwrap();
    let mut task = f.task();
    task.research = None;
    let mut session = Session::create(task, &f.run()).unwrap();
    let request = session.request().unwrap();
    fs::write(
        f.0.join("method.txt"),
        "Selected method.\nDifferent historical note.\n",
    )
    .unwrap();
    let response: Response = serde_json::from_value(json!({
        "invocation_id": request.invocation_id, "role": "coordinator",
        "decision": "work", "summary": "Selected method still applies", "assignment": "Continue useful work"
    })).unwrap();
    session.accept(response).unwrap();
    assert_eq!(session.request().unwrap().role, Role::Worker);
}

#[test]
fn explicit_current_use_check_cannot_report_coverage_for_an_unbound_run() {
    let f = Fixture::new();
    let (mut session, response) = f.start(Mode::Disabled);
    session.accept(response).unwrap();
    let request = session.request().unwrap();
    assert!(
        session
            .verify_queued_current_use(&request)
            .unwrap_err()
            .contains("coverage unavailable")
    );
    // Optional enforcement is not installed merely by requesting a status check.
    session
        .begin_execution(workflow_harness::control::Capabilities {
            fresh_context: true,
            events: true,
            controlled_continuation: true,
            ..Default::default()
        })
        .unwrap();
}

// These cases exercise real Session adoption and outgoing requests. They verify
// correspondence, not the truth of the owner's semantic equivalence argument.
fn complete_worker(s: &mut Session, p: &Response) -> usize {
    use workflow_harness::control::{Capabilities, Event, EventKind};
    let request = s
        .runtime
        .outstanding()
        .cloned()
        .unwrap_or_else(|| s.request().unwrap());
    assert_eq!(request.role, Role::Worker);
    s.begin_execution(Capabilities {
        fresh_context: true,
        events: true,
        controlled_continuation: true,
        ..Default::default()
    })
    .unwrap();
    s.event(Event {
        invocation_id: request.invocation_id,
        sequence: 1,
        event: EventKind::Stopped {
            effects_settled: true,
        },
    })
    .unwrap();
    let mut result = p.clone();
    result.invocation_id = request.invocation_id;
    result.role = Role::Worker;
    result.decision = workflow_harness::Decision::Observed;
    result.update.as_mut().unwrap().resolved_invocation = None;
    result.update.as_mut().unwrap().resolved_by.clear();
    s.accept(result).unwrap();
    s.request().unwrap().invocation_id
}

fn cleared_session(f: &Fixture) -> (Session, Response) {
    let (mut s, p) = f.submit(Mode::Enforce);
    s.decision_result(f.result(Verdict::NoFinding)).unwrap();
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    (s, p)
}

#[test]
fn false_flag_and_assignment_only_exclusions_cannot_reuse_old_clearance() {
    for assignment_only in [false, true] {
        let f = Fixture::new();
        let (mut s, mut p) = cleared_session(&f);
        p.invocation_id = complete_worker(&mut s, &p);
        if assignment_only {
            p.assignment
                .push_str(" Any setup failure permanently excludes this mechanism.");
        } else {
            p.update.as_mut().unwrap().reverse_when =
                "Any next wrapper failure ends the route".into();
        }
        assert!(!p.update.as_ref().unwrap().investment_changed);
        s.accept(p.clone()).unwrap();
        assert!(s.decisions.holds());
        assert!(s.request().is_err());
        drop(s);
        let mut s = Session::open(&f.run()).unwrap();
        assert!(s.request().is_err());
        assert_eq!(
            s.decisions.pending.as_ref().unwrap().proposal.assignment,
            p.assignment
        );
    }
}

#[test]
fn old_accepted_resolver_does_not_cover_changed_assignment_or_terminal_exclusion() {
    for finish in [false, true] {
        let f = Fixture::new();
        let (mut s, mut p) = f.start(Mode::Enforce);
        p.decision = workflow_harness::Decision::Reconsider;
        s.accept(p.clone()).unwrap();
        let resolver = s.request().unwrap();
        let mut r = p.clone();
        r.role = Role::Resolver;
        r.invocation_id = resolver.invocation_id;
        r.decision = workflow_harness::Decision::Work;
        s.accept(r).unwrap();
        p.invocation_id = s.request().unwrap().invocation_id;
        p.decision = if finish {
            workflow_harness::Decision::Finish
        } else {
            workflow_harness::Decision::Work
        };
        p.assignment = "Reject the mechanism after any further setup failure".into();
        p.summary = "The failed prerequisite ends investment in this mechanism".into();
        p.update.as_mut().unwrap().investment_changed = true;
        p.update.as_mut().unwrap().resolved_invocation = Some(resolver.invocation_id);
        s.accept(p).unwrap();
        assert!(s.decisions.holds());
        assert!(s.runtime.terminal().is_none());
        assert!(s.request().is_err());
    }
}

#[test]
fn structured_external_judgment_reuses_only_its_current_actual_consequence() {
    for changed in ["none", "assignment", "header"] {
        let f = Fixture::new();
        let (_unused, mut p) = f.start(Mode::Disabled);
        let judged = task_projection(
            &f,
            &p,
            &["Actual role method for mechanical verification.".into()],
        )
        .unwrap();
        fs::write(
            f.0.join("judgment.json"),
            json!({"judged_proposal":judged}).to_string(),
        )
        .unwrap();
        let mut task = f.task();
        if changed == "header" {
            task.constraints = "Different current task scope".into();
        }
        task.sources.push(workflow_harness::Source {
            path: "judgment.json".into(),
            first_line: 1,
            last_line: 1,
            purpose: "independent judgment".into(),
            roles: vec![Role::Coordinator],
        });
        let run = f.0.join("external-run");
        let mut s = Session::create(task, &run).unwrap();
        s.configure_decisions(f.config(Mode::Enforce)).unwrap();
        p.invocation_id = s.request().unwrap().invocation_id;
        p.update.as_mut().unwrap().resolved_by = vec![1];
        if changed == "assignment" {
            p.assignment
                .push_str(" Eliminate the mechanism on any error.");
        }
        s.accept(p).unwrap();
        drop(s);
        let mut s = Session::open(&run).unwrap();
        if changed != "none" {
            assert!(s.decisions.pending.is_some());
            assert!(s.request().is_err());
        } else {
            assert!(s.decisions.pending.is_none());
            assert_eq!(s.decisions.receipts[0].reused_sources, vec![1]);
            f.publish(&s);
            s.confirm_publication(1).unwrap();
            assert_eq!(s.request().unwrap().role, Role::Worker);
        }
    }
}

#[test]
fn ordinary_repair_reuses_same_judgment_across_return_handoff_and_reload() {
    let f = Fixture::new();
    let (mut s, mut p) = cleared_session(&f);
    p.invocation_id = complete_worker(&mut s, &p);
    let previous = task_projection(
        &f,
        &p,
        &["Actual role method for mechanical verification.".into()],
    )
    .unwrap();
    p.assignment = "Repair the known interface name and obtain the selected observation".into();
    p.update.as_mut().unwrap().interpretation =
        "Wrapper failed before execution; same affordable selected commitment".into();
    let current = task_projection(
        &f,
        &p,
        &["Actual role method for mechanical verification.".into()],
    )
    .unwrap();
    p.update.as_mut().unwrap().judgment_reuse = Some(workflow_harness::decision::JudgmentReuse {
        previous: workflow_harness::decision::projection_identity(&previous).unwrap(),
        current: workflow_harness::decision::projection_identity(&current).unwrap(),
        reason: "Known support repair remains within the selected observation and limits".into(),
    });
    s.accept(p.clone()).unwrap();
    assert_eq!(s.decisions.next_id, 1);
    drop(s);
    let mut s = Session::open(&f.run()).unwrap();
    let request = s.request().unwrap();
    assert!(request.prompt.contains("Repair the known interface name"));
    assert!(s.decisions.pending.is_none());
    p.invocation_id = complete_worker(&mut s, &p);
    p.update.as_mut().unwrap().judgment_reuse = None;
    p.summary = "Ordinary next progress, no changed consequence".into();
    s.accept(p).unwrap();
    assert_eq!(s.decisions.next_id, 1);
    assert_eq!(s.request().unwrap().role, Role::Worker);
}

#[test]
fn stale_equivalence_cannot_bind_a_later_assignment_change() {
    let f = Fixture::new();
    let (mut s, mut p) = cleared_session(&f);
    p.invocation_id = complete_worker(&mut s, &p);
    let id = workflow_harness::decision::projection_identity(
        &task_projection(
            &f,
            &p,
            &["Actual role method for mechanical verification.".into()],
        )
        .unwrap(),
    )
    .unwrap();
    p.update.as_mut().unwrap().judgment_reuse = Some(workflow_harness::decision::JudgmentReuse {
        previous: id.clone(),
        current: id,
        reason: "Wording-only edit".into(),
    });
    p.assignment
        .push_str(" Stop all research after another setup failure.");
    s.accept(p).unwrap();
    assert!(s.decisions.holds());
}

#[test]
fn terminal_investment_is_checked_but_bounded_completion_and_mandatory_stop_are_immediate() {
    use workflow_harness::decision::TerminalScope;
    for scope in [
        None,
        Some(TerminalScope::Investment),
        Some(TerminalScope::Completion),
        Some(TerminalScope::MandatoryStop),
    ] {
        let f = Fixture::new();
        let (mut s, mut p) = f.start(Mode::Enforce);
        p.decision = workflow_harness::Decision::Finish;
        p.assignment.clear();
        let u = p.update.as_mut().unwrap();
        u.options.clear();
        u.selected.clear();
        u.terminal_scope = scope;
        s.accept(p).unwrap();
        if matches!(
            scope,
            Some(TerminalScope::Completion | TerminalScope::MandatoryStop)
        ) {
            assert!(s.runtime.terminal().is_some());
            assert_eq!(s.decisions.next_id, 0);
        } else {
            assert!(s.runtime.terminal().is_none());
            assert!(s.decisions.holds());
            s.bind_decision(1, "actual-checker".into()).unwrap();
            s.decision_result(f.result(Verdict::NoFinding)).unwrap();
            f.publish(&s);
            s.confirm_publication(1).unwrap();
            s.verify_judgment_consumption().unwrap();
            fs::write(f.0.join("method.txt"), "Changed terminal evidence\n").unwrap();
            assert!(s.verify_judgment_consumption().is_err());
        }
    }
}

#[test]
fn known_correction_blocks_terminal_investment_but_not_a_required_scoped_stop() {
    let f = Fixture::new();
    let (mut s, mut p) = f.start(Mode::Enforce);
    s.adopt_current_use(current_use(&f, true)).unwrap();
    p.decision = workflow_harness::Decision::Finish;
    assert!(s.accept(p.clone()).unwrap_err().contains("unresolved"));
    p.update.as_mut().unwrap().terminal_scope =
        Some(workflow_harness::decision::TerminalScope::MandatoryStop);
    s.accept(p).unwrap();
    assert!(s.runtime.terminal().is_some());
    assert_eq!(s.decisions.next_id, 0);
}

#[test]
fn cleared_assignment_cannot_be_changed_through_queued_replacement() {
    let f = Fixture::new();
    let (mut s, _) = cleared_session(&f);
    let old = s.request().unwrap();
    assert!(
        s.replace_queued_work("Now reject the mechanism on the next setup error".into())
            .unwrap_err()
            .contains("judged consequence")
    );
    s.verify_queued_context(&old).unwrap();
}

#[test]
fn free_text_judgment_uses_same_turn_owner_association_without_new_checker() {
    let f = Fixture::new();
    let (mut s, mut p) = f.start(Mode::Enforce);
    p.update.as_mut().unwrap().resolved_by = vec![0];
    let current = workflow_harness::decision::projection_identity(
        &task_projection(
            &f,
            &p,
            &["Actual role method for mechanical verification.".into()],
        )
        .unwrap(),
    )
    .unwrap();
    p.update.as_mut().unwrap().judgment_reuse = Some(workflow_harness::decision::JudgmentReuse {
        previous: workflow_harness::decision::source_judgment_identity(
            &["Actual role method for mechanical verification.".into()], &[0]).unwrap(),
        current,
        reason: "This fixture owner associates the supplied evidence with the current consequence; semantic correctness is not tested".into(),
    });
    s.accept(p).unwrap();
    assert!(s.decisions.pending.is_none());
    assert!(s.decisions.receipts[0].result.is_none());
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    assert_eq!(s.request().unwrap().role, Role::Worker);
}

#[test]
fn mandatory_pause_does_not_wait_for_pending_terminal_judgment() {
    let f = Fixture::new();
    let (mut s, mut p) = f.start(Mode::Enforce);
    p.decision = workflow_harness::Decision::Finish;
    s.accept(p).unwrap();
    assert!(s.decisions.holds());
    s.pause("Real user resource limit exhausted; affected work stops immediately".into())
        .unwrap();
    assert!(s.request().is_err());
    assert!(s.runtime.terminal().is_none());
    assert!(s.decisions.pending.is_some());
}

#[test]
fn host_judgment_view_prepares_same_turn_reuse_without_changing_saved_state() {
    use std::{
        io::Write,
        process::{Command, Stdio},
    };
    let f = Fixture::new();
    let (mut s, mut p) = cleared_session(&f);
    p.invocation_id = complete_worker(&mut s, &p);
    p.assignment = "Perform the next internal repair under the same selected commitment".into();
    drop(s);
    let before = fs::read(f.run().join("state.json")).unwrap();
    let mut child = Command::new(env!("CARGO_BIN_EXE_workflow-harness"))
        .args(["host", "judgment-view", f.run().to_str().unwrap()])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(&serde_json::to_vec(&p).unwrap())
        .unwrap();
    let output = child.wait_with_output().unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(fs::read(f.run().join("state.json")).unwrap(), before);
    let view: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    p.update.as_mut().unwrap().judgment_reuse = Some(workflow_harness::decision::JudgmentReuse {
        previous: view["previous"].as_str().unwrap().into(),
        current: view["current"].as_str().unwrap().into(),
        reason: "Same supported repair scope and selected observation".into(),
    });
    let mut s = Session::open(&f.run()).unwrap();
    s.accept(p).unwrap();
    assert_eq!(s.decisions.next_id, 1);
    assert!(s.request().unwrap().prompt.contains("next internal repair"));
}

#[test]
fn pending_judgment_cannot_rebind_changed_evidence_or_actual_use_after_reload() {
    for actual_use in [false, true] {
        for reload in [false, true] {
            let f = Fixture::new();
            let (mut s, mut p) = f.start(Mode::Enforce);
            let separate = f.0.join("separately-declared-result.json");
            fs::write(&separate, "{\"available_units\":1}").unwrap();
            if actual_use {
                p.actual_use = vec![separate.clone()];
            } else {
                p.evidence = vec![separate.clone()];
            }
            s.accept(p).unwrap();
            s.bind_decision(1, "actual-checker".into()).unwrap();
            let captured = s
                .decisions
                .pending
                .as_ref()
                .unwrap()
                .judged_projection
                .clone();
            if reload {
                drop(s);
                s = Session::open(&f.run()).unwrap();
            }
            fs::write(&separate, "{\"available_units\":0}").unwrap();
            s.decision_result(f.result(Verdict::NoFinding)).unwrap();
            assert_eq!(s.decisions.receipts[0].judged_projection, captured);
            assert!(s.decisions.pending.is_none());
            assert!(s.decisions.publication.is_none());
            assert!(s.decisions.last_commitment.is_none());
            assert_eq!(s.runtime.outstanding().unwrap().role, Role::Coordinator);
            assert!(s.runtime.terminal().is_none());
            assert!(s.request().is_err());
        }
    }
}

#[test]
fn drifted_pending_use_can_be_abandoned_but_a_finding_still_requires_its_owner() {
    for finding in [false, true] {
        let f = Fixture::new();
        let (mut s, mut p) = f.start(Mode::Enforce);
        let separate = f.0.join("declared-task.txt");
        fs::write(&separate, "Original actual task").unwrap();
        p.actual_use = vec![separate.clone()];
        s.accept(p).unwrap();
        s.bind_decision(1, "actual-checker".into()).unwrap();
        if finding {
            s.decision_result(f.result(Verdict::Revise)).unwrap();
        }
        fs::remove_file(&separate).unwrap();
        let result =
            s.abandon_decision("Actual task disappeared; retain the return for its owner".into());
        if finding {
            assert!(result.unwrap_err().contains("concrete finding"));
            assert!(s.decisions.holds());
        } else {
            result.unwrap();
            assert!(s.decisions.pending.is_none());
            assert!(s.decisions.publication.is_none());
            assert_eq!(s.runtime.outstanding().unwrap().role, Role::Coordinator);
        }
    }
}

#[test]
fn legacy_pending_without_captured_projection_returns_to_owner_without_adoption() {
    let f = Fixture::new();
    let (s, _) = f.submit(Mode::Enforce);
    drop(s);
    let path = f.run().join("state.json");
    let mut state: serde_json::Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
    state["decisions"]["pending"]
        .as_object_mut()
        .unwrap()
        .remove("judged_projection");
    fs::write(&path, serde_json::to_vec(&state).unwrap()).unwrap();
    let mut s = Session::open(&f.run()).unwrap();
    s.decision_result(f.result(Verdict::NoFinding)).unwrap();
    assert!(s.decisions.publication.is_none());
    assert!(s.decisions.last_commitment.is_none());
    assert_eq!(s.runtime.outstanding().unwrap().role, Role::Coordinator);
}

#[test]
fn existing_owner_can_adopt_current_correction_after_pending_evidence_drift() {
    let f = Fixture::new();
    let (mut s, mut p) = f.start(Mode::Enforce);
    let separate = f.0.join("evidence.txt");
    fs::write(&separate, "Original support evidence").unwrap();
    p.evidence = vec![separate.clone()];
    s.accept(p.clone()).unwrap();
    s.bind_decision(1, "actual-checker".into()).unwrap();
    s.decision_result(f.result(Verdict::Revise)).unwrap();
    fs::write(
        &separate,
        "Current correction evidence reviewed by the existing owner",
    )
    .unwrap();
    p.assignment = "Perform the currently corrected bounded assignment".into();
    s.resolve_decision(f.owner(Disposition::Revised, Some(p)))
        .unwrap();
    assert_eq!(s.decisions.next_id, 1);
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    assert!(
        s.request()
            .unwrap()
            .prompt
            .contains("currently corrected bounded assignment")
    );
}

#[test]
fn same_assignment_replacement_cannot_change_judged_actual_use() {
    let f = Fixture::new();
    let (mut s, mut p) = f.start(Mode::Enforce);
    let assignment = p.assignment.clone();
    p.assignment =
        format!("This assignment supersedes the earlier queued assignment.\n{assignment}");
    let equivalent = f.0.join("second-dependency.md");
    fs::write(&equivalent, "Existing dependency").unwrap();
    p.actual_use.push(equivalent.clone());
    s.accept(p).unwrap();
    s.bind_decision(1, "actual-checker".into()).unwrap();
    s.decision_result(f.result(Verdict::NoFinding)).unwrap();
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    let original = s.request().unwrap();
    let changed = f.0.join("different-task.md");
    fs::write(
        &changed,
        "Any further setup error permanently excludes the mechanism",
    )
    .unwrap();
    drop(s);
    let mut s = Session::open(&f.run()).unwrap();
    assert!(
        s.replace_queued_work_for(assignment.clone(), vec![changed])
            .unwrap_err()
            .contains("judged consequence")
    );
    s.verify_queued_context(&original).unwrap();
    // Reordering the same canonical dependency set is not a different use.
    let replacement = s
        .replace_queued_work_for(assignment, vec![equivalent, f.0.join("method.txt")])
        .unwrap();
    s.verify_queued_context(&replacement).unwrap();
}

fn task_projection(
    f: &Fixture,
    response: &Response,
    sources: &[String],
) -> workflow_harness::Result<serde_json::Value> {
    let mut projection = workflow_harness::decision::projection(response, sources)?;
    projection["task_header"] = json!({"task_objective": f.task().objective,
        "task_constraints": f.task().constraints});
    Ok(projection)
}

fn owner_task_correction() -> workflow_harness::QueuedWorkCorrection {
    serde_json::from_value(json!({
        "assignment":"Use the authorized local device; measure CPU target timing separately.",
        "objective":"Improve the full molecular ranking result",
        "constraints":"Local MPS development is allowed; retain CPU target timing. No paid resources."
    })).unwrap()
}

#[test]
fn owner_task_correction_updates_full_request_and_cold_recovery() {
    let f = Fixture::new();
    let (mut s, response) = f.start(Mode::Disabled);
    s.adopt_current_use(current_use(&f, false)).unwrap();
    s.accept(response).unwrap();
    let old = s.request().unwrap();
    let before = serde_json::to_value(&s.runtime).unwrap();
    let replacement = s
        .replace_queued_work_with_correction(owner_task_correction())
        .unwrap();
    let header = replacement
        .prompt
        .split("Current assignment:")
        .next()
        .unwrap();
    assert!(header.contains("Objective: Improve the full molecular ranking result"));
    assert!(header.contains("Constraints: Local MPS development is allowed"));
    assert!(!header.contains("Constraints: Temporary files only"));
    assert!(
        replacement
            .prompt
            .contains("measure CPU target timing separately")
    );
    assert!(replacement.prompt.contains("No paid resources"));
    assert_ne!(replacement.invocation_id, old.invocation_id);
    s.verify_queued_context(&replacement).unwrap();
    s.verify_queued_current_use(&replacement).unwrap();
    assert!(s.verify_queued_context(&old).is_err());
    let after = serde_json::to_value(&s.runtime).unwrap();
    for field in ["history", "executions", "segment", "judged_uses"] {
        assert_eq!(before[field], after[field], "{field}");
    }
    assert_eq!(before["task"]["research"], after["task"]["research"]);
    assert_eq!(
        before["task"]["invocation_limit"],
        after["task"]["invocation_limit"]
    );
    assert_eq!(before["task"]["sources"], after["task"]["sources"]);
    assert_eq!(old.actual_use, replacement.actual_use);
    assert!(
        f.run()
            .join(format!("request-{}.json", old.invocation_id))
            .is_file()
    );
    drop(s);
    let s = Session::open(&f.run()).unwrap();
    assert_eq!(s.runtime.outstanding().unwrap().prompt, replacement.prompt);
    assert_eq!(serde_json::to_value(&s.runtime).unwrap(), after);
    s.verify_queued_current_use(&replacement).unwrap();
}

#[test]
fn owner_task_correction_omitted_fields_and_legacy_calls_preserve_task() {
    let f = Fixture::new();
    let (mut s, response) = f.start(Mode::Disabled);
    s.accept(response).unwrap();
    let original = s.request().unwrap();
    let task = serde_json::to_value(&s.runtime).unwrap()["task"].clone();
    let minimal =
        serde_json::from_value(json!({"assignment":"Continue the selected observation"})).unwrap();
    s.replace_queued_work_with_correction(minimal).unwrap();
    let request = s
        .replace_queued_work("Revise the assignment wording only".into())
        .unwrap();
    assert_eq!(serde_json::to_value(&s.runtime).unwrap()["task"], task);
    assert_eq!(original.actual_use, request.actual_use);
    assert!(request.prompt.contains("Constraints: Temporary files only"));
    assert!(
        !request
            .prompt
            .contains("supersedes the earlier queued restriction")
    );
    // Worker responses cannot smuggle task corrections through the return schema.
    for field in ["objective", "constraints", "task", "actual_use_correction"] {
        let mut response = json!({"invocation_id":request.invocation_id,"role":"worker",
            "decision":"observed","summary":"Observation","evidence":[]});
        response[field] = json!("Unrequested authority change");
        assert!(
            serde_json::from_value::<Response>(response).is_err(),
            "{field}"
        );
    }
}

#[test]
fn owner_task_correction_preserves_all_started_work_guards() {
    for started in ["execution", "host", "stdout"] {
        let f = Fixture::new();
        let (mut s, response) = f.start(Mode::Disabled);
        s.accept(response).unwrap();
        let request = s.request().unwrap();
        match started {
            "execution" => {
                s.begin_execution(workflow_harness::control::Capabilities {
                    fresh_context: true,
                    events: true,
                    controlled_continuation: true,
                    ..Default::default()
                })
                .unwrap();
            }
            "host" => s
                .bind_host(workflow_harness::session::HostBinding {
                    invocation_id: request.invocation_id,
                    backend_handle: "existing-worker".into(),
                })
                .unwrap(),
            _ => fs::write(
                f.run()
                    .join(format!("stdout-{}.json", request.invocation_id)),
                "",
            )
            .unwrap(),
        }
        let before = serde_json::to_value(&s.runtime).unwrap();
        let disk = fs::read(f.run().join("state.json")).unwrap();
        assert!(
            s.replace_queued_work_with_correction(owner_task_correction())
                .unwrap_err()
                .contains("unstarted")
        );
        assert_eq!(serde_json::to_value(&s.runtime).unwrap(), before);
        assert_eq!(fs::read(f.run().join("state.json")).unwrap(), disk);
    }
}

#[test]
fn owner_task_correction_keeps_known_correction_and_judgment_checks() {
    let f = Fixture::new();
    let (mut s, response) = f.start(Mode::Disabled);
    s.accept(response).unwrap();
    s.request().unwrap();
    s.adopt_current_use(current_use(&f, true)).unwrap();
    let before = serde_json::to_value(&s.runtime).unwrap();
    assert!(
        s.replace_queued_work_with_correction(owner_task_correction())
            .unwrap_err()
            .contains("unresolved")
    );
    assert_eq!(serde_json::to_value(&s.runtime).unwrap(), before);

    let f = Fixture::new();
    let (mut s, _) = f.submit(Mode::Enforce);
    s.decision_result(f.result(Verdict::NoFinding)).unwrap();
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    let original = s.request().unwrap();
    let disk = fs::read(f.run().join("state.json")).unwrap();
    assert!(
        s.replace_queued_work("Changed assignment without owner adoption".into())
            .unwrap_err()
            .contains("judged consequence")
    );
    s.verify_queued_context(&original).unwrap();
    assert_eq!(fs::read(f.run().join("state.json")).unwrap(), disk);
}

#[test]
fn owner_task_correction_rolls_back_after_checkpoint_but_failed_journal() {
    let f = Fixture::new();
    let (mut s, response) = f.start(Mode::Disabled);
    s.adopt_current_use(current_use(&f, false)).unwrap();
    s.accept(response).unwrap();
    let original = s.request().unwrap();
    let before = serde_json::to_value(&s.runtime).unwrap();
    let disk = fs::read(f.run().join("state.json")).unwrap();
    // Force a failure after request() has already saved the new checkpoint.
    fs::rename(
        f.run().join("events.jsonl"),
        f.run().join("events.saved.jsonl"),
    )
    .unwrap();
    fs::create_dir(f.run().join("events.jsonl")).unwrap();
    assert!(
        s.replace_queued_work_with_correction(owner_task_correction())
            .is_err()
    );
    assert_eq!(serde_json::to_value(&s.runtime).unwrap(), before);
    assert_eq!(fs::read(f.run().join("state.json")).unwrap(), disk);
    s.verify_queued_context(&original).unwrap();
    s.verify_queued_current_use(&original).unwrap();
    drop(s);
    let s = Session::open(&f.run()).unwrap();
    assert_eq!(serde_json::to_value(&s.runtime).unwrap(), before);
    s.verify_queued_current_use(&original).unwrap();
}

#[test]
fn host_cli_corrects_task_header_and_rejects_started_or_invalid_updates() {
    let f = Fixture::new();
    let (mut s, response) = f.start(Mode::Disabled);
    s.accept(response).unwrap();
    s.request().unwrap();
    drop(s);
    let path = f.0.join("correction.json");
    fs::write(&path, serde_json::to_vec(&owner_task_correction()).unwrap()).unwrap();
    let result = current_use_cli(&f, "current-use-correct", &path);
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    let request: workflow_harness::Invocation = serde_json::from_slice(&result.stdout).unwrap();
    assert!(
        request
            .prompt
            .contains("Constraints: Local MPS development is allowed")
    );
    let s = Session::open(&f.run()).unwrap();
    s.verify_queued_context(&request).unwrap();
    s.bind_host(workflow_harness::session::HostBinding {
        invocation_id: request.invocation_id,
        backend_handle: "running-worker".into(),
    })
    .unwrap();
    drop(s);
    assert!(
        !current_use_cli(&f, "current-use-correct", &path)
            .status
            .success()
    );
    let s = Session::open(&f.run()).unwrap();
    s.verify_queued_context(&request).unwrap();
    drop(s);
    fs::write(
        &path,
        json!({"assignment":"Continue", "invocation_limit":100}).to_string(),
    )
    .unwrap();
    let invalid = current_use_cli(&f, "current-use-correct", &path);
    assert!(!invalid.status.success());
    assert!(String::from_utf8_lossy(&invalid.stderr).contains("unknown field"));
}

#[test]
fn excerpt_correction_requires_full_read_or_owner_delivery_of_qualifications() {
    let f = Fixture::new();
    fs::write(f.0.join("arrangement.md"), "# Original arrangement\nUse CPU only during local development.\n\n# Current owner correction\nLocal MPS development is allowed; retain CPU target timing separately.\n").unwrap();
    let mut task = f.task();
    task.research = None;
    task.sources.push(
        serde_json::from_value(json!({"path":"arrangement.md","first_line":1,"last_line":2,
        "purpose":"local execution arrangement","roles":["coordinator","resolver","worker"]}))
        .unwrap(),
    );
    let mut s = Session::create(task.clone(), &f.run()).unwrap();
    let request = s.request().unwrap();
    assert!(
        request
            .prompt
            .contains("Use CPU only during local development.")
    );
    assert!(!request.prompt.contains("Local MPS development is allowed"));
    s.verify_queued_context(&request).unwrap();
    let full = s.runtime.read_context_evidence("/full_sources/1").unwrap();
    assert!(
        full.as_str()
            .unwrap()
            .contains("Local MPS development is allowed")
    );
    // The existing owner can read the omitted qualification and explicitly
    // deliver its current scope without mutating source selectors or history.
    s.accept(serde_json::from_value(json!({
        "invocation_id":request.invocation_id,"role":"coordinator","decision":"work",
        "summary":"Adopt the current owner correction after reading its full source",
        "assignment":"Use local MPS for development and retain CPU target timing separately. The earlier CPU-only local-development arrangement in the source excerpt is superseded.",
        "actual_use":[f.0.join("arrangement.md")],"evidence":[f.0.join("arrangement.md")]
    })).unwrap()).unwrap();
    let worker = s.request().unwrap();
    assert_eq!(worker.role, Role::Worker);
    assert!(
        worker
            .prompt
            .contains("Current assignment: Use local MPS for development")
    );
    assert!(
        worker
            .prompt
            .contains("retain CPU target timing separately")
    );
    s.verify_queued_context(&worker).unwrap();
    drop(s);
    let recovered = Session::open(&f.run()).unwrap();
    assert_eq!(
        recovered.runtime.outstanding().unwrap().prompt,
        worker.prompt
    );
    task.sources[1].last_line = 5;
    let mut complete = Session::create(task, &f.0.join("complete-run")).unwrap();
    assert!(
        complete
            .request()
            .unwrap()
            .prompt
            .contains("Local MPS development is allowed")
    );
}

#[test]
fn enforced_header_correction_returns_owner_and_supports_existing_reuse_or_check() {
    for reuse in [false, true] {
        let f = Fixture::new();
        let (mut s, mut proposal) = f.start(Mode::Enforce);
        let assignment = proposal.assignment.clone();
        proposal.assignment =
            format!("This assignment supersedes the earlier queued assignment.\n{assignment}");
        s.adopt_current_use(current_use(&f, false)).unwrap();
        s.accept(proposal.clone()).unwrap();
        s.bind_decision(1, "actual-checker".into()).unwrap();
        s.decision_result(f.result(Verdict::NoFinding)).unwrap();
        f.publish(&s);
        s.confirm_publication(1).unwrap();
        let old = s.request().unwrap();
        drop(s);
        let mut s = Session::open(&f.run()).unwrap();
        let correction = workflow_harness::QueuedWorkCorrection {
            assignment,
            objective: Some("Corrected project objective".into()),
            constraints: Some("Local MPS development; CPU target timing; no paid resources".into()),
            actual_use: None,
        };
        let owner = if reuse {
            s.replace_queued_work_with_correction(correction).unwrap()
        } else {
            drop(s);
            let path = f.0.join("header-correction.json");
            fs::write(&path, serde_json::to_vec(&correction).unwrap()).unwrap();
            let output = current_use_cli(&f, "current-use-correct", &path);
            assert!(
                output.status.success(),
                "{}",
                String::from_utf8_lossy(&output.stderr)
            );
            s = Session::open(&f.run()).unwrap();
            serde_json::from_slice::<workflow_harness::Invocation>(&output.stdout).unwrap()
        };
        assert_eq!(owner.role, Role::Coordinator);
        assert!(
            owner
                .prompt
                .contains("Objective: Corrected project objective")
        );
        assert!(owner.prompt.contains("Constraints: Local MPS development"));
        assert!(s.verify_queued_context(&old).is_err());
        assert_eq!(s.decisions.next_id, 1);
        drop(s);
        let mut s = Session::open(&f.run()).unwrap();
        assert_eq!(s.runtime.outstanding().unwrap().prompt, owner.prompt);
        proposal.invocation_id = owner.invocation_id;
        let view = s.judgment_view(&proposal).unwrap();
        assert_ne!(view["previous"], view["current"]);
        assert_eq!(
            view["projection"]["task_header"]["task_objective"],
            "Corrected project objective"
        );
        if reuse {
            proposal.update.as_mut().unwrap().judgment_reuse = Some(workflow_harness::decision::JudgmentReuse {
                previous:view["previous"].as_str().unwrap().into(), current:view["current"].as_str().unwrap().into(),
                reason:"The owner verified the corrected development scope; the selected mechanism and target evidence remain applicable.".into()
            });
        }
        s.accept(proposal).unwrap();
        if reuse {
            assert!(s.decisions.pending.is_none());
            assert_eq!(s.decisions.next_id, 1);
        } else {
            assert_eq!(s.decisions.pending.as_ref().unwrap().check_id, 2);
            assert!(s.request().is_err());
            s.bind_decision(2, "actual-checker".into()).unwrap();
            let mut result = f.result(Verdict::NoFinding);
            result.check_id = 2;
            s.decision_result(result).unwrap();
            f.publish(&s);
            s.confirm_publication(2).unwrap();
        }
        let worker = s.request().unwrap();
        assert_eq!(worker.role, Role::Worker);
        assert!(worker.prompt.contains("Constraints: Local MPS development"));
        s.verify_queued_current_use(&worker).unwrap();
        drop(s);
        let s = Session::open(&f.run()).unwrap();
        s.verify_queued_context(&worker).unwrap();
    }
}

#[test]
fn enforced_unchanged_header_keeps_worker_without_an_owner_round_trip() {
    let f = Fixture::new();
    let (mut s, mut proposal) = f.start(Mode::Enforce);
    let assignment = proposal.assignment.clone();
    proposal.assignment =
        format!("This assignment supersedes the earlier queued assignment.\n{assignment}");
    s.accept(proposal).unwrap();
    s.bind_decision(1, "actual-checker".into()).unwrap();
    s.decision_result(f.result(Verdict::NoFinding)).unwrap();
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    s.request().unwrap();
    let request = s
        .replace_queued_work_with_correction(workflow_harness::QueuedWorkCorrection {
            assignment,
            objective: Some(f.task().objective),
            constraints: Some(f.task().constraints),
            actual_use: None,
        })
        .unwrap();
    assert_eq!(request.role, Role::Worker);
    assert_eq!(s.decisions.next_id, 1);
    s.verify_queued_context(&request).unwrap();
}

#[test]
fn legacy_judgment_requires_original_header_evidence_and_can_return_to_owner() {
    for evidence in ["matching", "changed", "missing"] {
        let f = Fixture::new();
        let (mut s, _) = cleared_session(&f);
        let worker = s.request().unwrap();
        drop(s);
        let path = f.run().join("state.json");
        let mut state: serde_json::Value =
            serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
        let mut commitment: serde_json::Value =
            serde_json::from_str(state["decisions"]["last_commitment"].as_str().unwrap()).unwrap();
        commitment.as_object_mut().unwrap().remove("task_header");
        state["decisions"]["last_commitment"] = json!(commitment.to_string());
        state["decisions"]["last_sources"]
            .as_array_mut()
            .unwrap()
            .pop();
        if evidence == "changed" {
            state["runtime"]["task"]["constraints"] = json!("Unverified different constraint");
        } else if evidence == "missing" {
            fs::remove_file(f.run().join("request-1.json")).unwrap();
        }
        fs::write(&path, serde_json::to_vec(&state).unwrap()).unwrap();
        let mut s = Session::open(&f.run()).unwrap();
        if evidence == "matching" {
            s.verify_queued_context(&worker).unwrap();
            assert_eq!(s.runtime.outstanding().unwrap().role, Role::Worker);
            continue;
        } else {
            assert!(
                s.verify_queued_context(&worker)
                    .unwrap_err()
                    .contains("legacy judgment")
            );
        }
        let owner = s
            .replace_queued_work_with_correction(
                serde_json::from_value(json!({
                    "assignment":"Continue after the owner verifies the current scope"
                }))
                .unwrap(),
            )
            .unwrap();
        assert_eq!(owner.role, Role::Coordinator);
        s.verify_queued_context(&owner).unwrap();
        assert!(owner.prompt.contains("was not bound to"));
    }
}

#[test]
fn historical_resolver_header_is_not_recomputed_as_current_evidence() {
    let f = Fixture::new();
    let (mut s, mut proposal) = f.start(Mode::Enforce);
    proposal.decision = workflow_harness::Decision::Reconsider;
    s.accept(proposal.clone()).unwrap();
    let resolver = s.request().unwrap();
    let mut resolved = proposal.clone();
    resolved.role = Role::Resolver;
    resolved.invocation_id = resolver.invocation_id;
    resolved.decision = workflow_harness::Decision::Work;
    s.accept(resolved).unwrap();
    proposal.invocation_id = s.request().unwrap().invocation_id;
    proposal.decision = workflow_harness::Decision::Work;
    proposal.update.as_mut().unwrap().resolved_invocation = Some(resolver.invocation_id);
    s.accept(proposal.clone()).unwrap();
    assert!(s.decisions.pending.is_none());
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    s.request().unwrap();
    let owner = s.replace_queued_work_with_correction(serde_json::from_value(json!({
        "assignment":proposal.assignment,"constraints":"A different current development scope"
    })).unwrap()).unwrap();
    assert_eq!(owner.role, Role::Coordinator);
    proposal.invocation_id = owner.invocation_id;
    s.accept(proposal).unwrap();
    assert!(s.decisions.pending.is_some());
    let saved = serde_json::to_value(&s.runtime).unwrap();
    assert_eq!(
        saved["judged_uses"][resolver.invocation_id.to_string()]["proposal"]["task_header"]["task_constraints"],
        f.task().constraints
    );
}

#[test]
fn legacy_matching_header_keeps_assignment_replacement_on_worker() {
    let f = Fixture::new();
    let (mut s, mut proposal) = f.start(Mode::Enforce);
    let assignment = proposal.assignment.clone();
    proposal.assignment =
        format!("This assignment supersedes the earlier queued assignment.\n{assignment}");
    s.accept(proposal.clone()).unwrap();
    s.bind_decision(1, "actual-checker".into()).unwrap();
    s.decision_result(f.result(Verdict::NoFinding)).unwrap();
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    s.request().unwrap();
    drop(s);
    let path = f.run().join("state.json");
    let mut state: serde_json::Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
    let mut commitment: serde_json::Value =
        serde_json::from_str(state["decisions"]["last_commitment"].as_str().unwrap()).unwrap();
    commitment.as_object_mut().unwrap().remove("task_header");
    state["decisions"]["last_commitment"] = json!(commitment.to_string());
    state["decisions"]["last_sources"]
        .as_array_mut()
        .unwrap()
        .pop();
    fs::write(path, serde_json::to_vec(&state).unwrap()).unwrap();
    let mut s = Session::open(&f.run()).unwrap();
    let replacement = s.replace_queued_work(assignment).unwrap();
    assert_eq!(replacement.role, Role::Worker);
    assert_eq!(s.decisions.next_id, 1);
    s.verify_queued_context(&replacement).unwrap();
    drop(s);
    let mut s = Session::open(&f.run()).unwrap();
    s.verify_queued_context(&replacement).unwrap();
    proposal.invocation_id = complete_worker(&mut s, &proposal);
    let view = s.judgment_view(&proposal).unwrap();
    assert_ne!(view["previous"], view["current"]);
    proposal.update.as_mut().unwrap().judgment_reuse = Some(workflow_harness::decision::JudgmentReuse {
        previous:view["previous"].as_str().unwrap().into(), current:view["current"].as_str().unwrap().into(),
        reason:"The owner verified the unchanged legacy task header against its original delivery; the same commitment remains applicable.".into()
    });
    s.accept(proposal).unwrap();
    assert_eq!(s.decisions.next_id, 1);
    assert!(s.decisions.pending.is_none());
    assert_eq!(s.request().unwrap().role, Role::Worker);
}

#[test]
fn native_retry_preserves_enforced_judgment_and_current_use_consumption() {
    use workflow_harness::control::{HostDispatch, HostDispatchOutcome};
    let f = Fixture::new();
    let (mut s, proposal) = f.start(Mode::Enforce);
    s.adopt_current_use(current_use(&f, false)).unwrap();
    s.accept(proposal.clone()).unwrap();
    assert!(s.prepare_host_dispatch(2, "held-call".into()).is_err());
    assert!(s.host_dispatch_history().is_empty());
    s.bind_decision(1, "actual-checker".into()).unwrap();
    s.decision_result(f.result(Verdict::NoFinding)).unwrap();
    f.publish(&s);
    s.confirm_publication(1).unwrap();
    let old = s.request().unwrap();
    s.prepare_host_dispatch(old.invocation_id, "rejected-call".into())
        .unwrap();
    s.reconcile_host_dispatch(HostDispatch {
        invocation_id: old.invocation_id,
        call_id: "rejected-call".into(),
        outcome: HostDispatchOutcome::NotStarted {
            evidence: "Host confirms capacity rejection before starting work".into(),
        },
    })
    .unwrap();
    drop(s);
    let mut s = Session::open(&f.run()).unwrap();
    let retry = s.retry_not_started(old.invocation_id).unwrap();
    assert_ne!(old.invocation_id, retry.invocation_id);
    assert_eq!(retry.role, Role::Worker);
    assert!(retry.prompt.contains(&proposal.assignment));
    assert!(s.decisions.pending.is_none());
    s.verify_judgment_consumption().unwrap();
    s.verify_queued_current_use(&retry).unwrap();
    assert!(s.verify_queued_current_use(&old).is_err());
    drop(s);
    let mut s = Session::open(&f.run()).unwrap();
    s.verify_judgment_consumption().unwrap();
    s.verify_queued_current_use(&retry).unwrap();
    fs::write(
        f.0.join("method.txt"),
        "Changed source after retry preparation\n",
    )
    .unwrap();
    assert!(
        s.prepare_host_dispatch(retry.invocation_id, "stale-call".into())
            .is_err()
    );
    assert!(s.host_dispatch().is_none());
    assert!(s.begin_execution(Default::default()).is_err());
}
