use std::fs;
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};
use workflow_harness::session::{HostBinding, ProcessAdapter, Session};
use workflow_harness::{Decision, Response, Role, Runtime, Task};

struct Directory(PathBuf);
static NEXT_DIRECTORY: AtomicUsize = AtomicUsize::new(0);
impl Directory {
    fn new() -> Self {
        let id = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let sequence = NEXT_DIRECTORY.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "workflow-transport-{}-{id}-{sequence}",
            std::process::id()
        ));
        fs::create_dir(&path).unwrap();
        Self(path)
    }

    fn command(&self) -> Command {
        let task = serde_json::json!({
            "objective":"Transport test only", "workspace":std::env::current_dir().unwrap(),
            "constraints":"No external actions", "sources":[], "invocation_limit":3
        });
        fs::write(self.0.join("task.json"), serde_json::to_vec(&task).unwrap()).unwrap();
        let mut command = Command::new(env!("CARGO_BIN_EXE_workflow-harness"));
        command
            .arg(self.0.join("task.json"))
            .arg(self.0.join("run"));
        command
    }
}
impl Drop for Directory {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.0).unwrap();
    }
}

#[test]
fn disconnect_preserves_pending_and_existing_run_is_not_replayed() {
    let directory = Directory::new();
    let first = directory.command().stdin(Stdio::null()).output().unwrap();
    assert!(!first.status.success());
    let journal = directory.0.join("run/events.jsonl");
    let before = fs::read(&journal).unwrap();
    assert!(String::from_utf8_lossy(&before).contains("invocation_pending"));
    assert!(!directory.0.join("run/response-1.json").exists());
    let second = directory.command().stdin(Stdio::null()).output().unwrap();
    assert!(!second.status.success());
    assert_eq!(before, fs::read(journal).unwrap());
}

#[test]
fn piped_transport_runs_work_then_adopts_once() {
    let directory = Directory::new();
    let mut child = directory
        .command()
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    let mut stdin = child.stdin.take().unwrap();
    for (id, role, decision) in [
        (1, "coordinator", "work"),
        (2, "worker", "observed"),
        (3, "coordinator", "finish"),
    ] {
        let result = serde_json::json!({"invocation_id":id,"role":role,"decision":decision,
            "summary":"Mechanical transport test", "assignment":"Bounded test work",
            "evidence":[std::env::current_dir().unwrap().join("Cargo.toml")]});
        writeln!(stdin, "{result}").unwrap();
    }
    drop(stdin);
    let output = child.wait_with_output().unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let events: Vec<serde_json::Value> = String::from_utf8(output.stdout)
        .unwrap()
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect();
    assert_eq!(events.len(), 4);
    assert_eq!(events[0]["role"], "coordinator");
    assert_eq!(events[1]["role"], "worker");
    assert_eq!(events[2]["role"], "coordinator");
    assert_eq!(events[3]["event"], "pilot_terminal");
}

fn task(directory: &Directory, with_source: bool) -> Task {
    let sources = if with_source {
        fs::write(directory.0.join("selected.txt"), "original observation\n").unwrap();
        serde_json::json!([{"path":"selected.txt","first_line":1,"last_line":1,
            "purpose":"Selected input for mechanical checks", "roles":["coordinator","worker","resolver"]}])
    } else {
        serde_json::json!([])
    };
    serde_json::from_value(serde_json::json!({
        "objective":"State transition checks, not a research pilot", "workspace":directory.0,
        "constraints":"Local mechanical checks only", "sources":sources,"invocation_limit":12
    }))
    .unwrap()
}

fn response(request: &workflow_harness::Invocation, decision: Decision) -> Response {
    Response {
        invocation_id: request.invocation_id,
        role: request.role,
        decision,
        summary: "Mechanical state transition evidence only".into(),
        assignment: "One bounded check".into(),
        evidence: vec![std::env::current_dir().unwrap().join("Cargo.toml")],
        update: None,
    }
}

#[test]
fn selected_change_reaches_coordinator_before_worker_but_unrelated_change_does_not() {
    let d = Directory::new();
    let mut runtime = Runtime::new(task(&d, true)).unwrap();
    let request = runtime.request().unwrap();
    runtime.accept(response(&request, Decision::Work)).unwrap();
    fs::write(d.0.join("selected.txt"), "changed observation\n").unwrap();
    let request = runtime.request().unwrap();
    assert_eq!(request.role, Role::Coordinator);
    assert!(request.prompt.contains("changed observation"));
    runtime.accept(response(&request, Decision::Work)).unwrap();
    fs::write(d.0.join("unrelated.txt"), "an unrelated edit").unwrap();
    assert_eq!(runtime.request().unwrap().role, Role::Worker);
}

#[test]
fn changed_worker_only_source_is_supplied_to_the_coordinator() {
    let d = Directory::new();
    let mut task = task(&d, true);
    task.sources[0].roles = vec![Role::Worker];
    let mut runtime = Runtime::new(task).unwrap();
    let request = runtime.request().unwrap();
    assert!(!request.prompt.contains("original observation"));
    runtime.accept(response(&request, Decision::Work)).unwrap();
    fs::write(d.0.join("selected.txt"), "changed worker evidence\n").unwrap();
    let request = runtime.request().unwrap();
    assert_eq!(request.role, Role::Coordinator);
    assert!(request.prompt.contains("selected.txt:1-1"));
    assert!(request.prompt.contains("changed worker evidence"));
    runtime.accept(response(&request, Decision::Work)).unwrap();
    assert_eq!(runtime.request().unwrap().role, Role::Worker);
}

#[test]
fn changed_input_prevents_stale_completion_without_discarding_return() {
    let d = Directory::new();
    let mut runtime = Runtime::new(task(&d, true)).unwrap();
    let request = runtime.request().unwrap();
    fs::write(d.0.join("selected.txt"), "new evidence\n").unwrap();
    runtime
        .accept(response(&request, Decision::Finish))
        .unwrap();
    assert!(runtime.terminal().is_none());
    let request = runtime.request().unwrap();
    assert_eq!(request.role, Role::Coordinator);
    assert!(
        request
            .prompt
            .contains("Mechanical state transition evidence only")
    );
    assert!(request.prompt.contains("new evidence"));
    runtime
        .accept(response(&request, Decision::Finish))
        .unwrap();
    assert!(runtime.terminal().is_some());
}

#[test]
fn stale_resolver_return_does_not_clear_an_existing_challenge() {
    let d = Directory::new();
    let mut runtime = Runtime::new(task(&d, true)).unwrap();
    let request = runtime.request().unwrap();
    runtime
        .accept(response(&request, Decision::Reconsider))
        .unwrap();
    let request = runtime.request().unwrap();
    assert_eq!(request.role, Role::Resolver);
    fs::write(d.0.join("selected.txt"), "changed comparison evidence\n").unwrap();
    runtime.accept(response(&request, Decision::Work)).unwrap();
    let request = runtime.request().unwrap();
    assert!(
        runtime
            .accept(response(&request, Decision::Finish))
            .is_err()
    );
    runtime.accept(response(&request, Decision::Work)).unwrap();
    assert_eq!(runtime.request().unwrap().role, Role::Resolver);
}

#[test]
fn lost_required_source_preserves_return_and_stops_new_dispatch() {
    let d = Directory::new();
    let mut runtime = Runtime::new(task(&d, true)).unwrap();
    let request = runtime.request().unwrap();
    fs::remove_file(d.0.join("selected.txt")).unwrap();
    runtime.accept(response(&request, Decision::Work)).unwrap();
    assert!(runtime.outstanding().is_none());
    assert!(runtime.request().is_err());
    fs::write(d.0.join("selected.txt"), "restored current source\n").unwrap();
    assert_eq!(runtime.request().unwrap().role, Role::Coordinator);
}

#[test]
fn saved_adoption_resumes_with_coordinator_and_cannot_be_applied_twice() {
    let d = Directory::new();
    let path = d.0.join("saved-run");
    let mut session = Session::create(task(&d, false), &path).unwrap();
    let request = session.request().unwrap();
    let result = response(&request, Decision::Work);
    session.accept(result.clone()).unwrap();
    assert!(Session::open(&path).is_err(), "one writer must own the run");
    drop(session);
    let mut session = Session::open(&path).unwrap();
    assert!(session.accept(result).is_err());
    session.recover_for_adoption().unwrap();
    let request = session.request().unwrap();
    assert_eq!(request.role, Role::Coordinator);
    assert_eq!(request.invocation_id, 2);
    assert!(request.prompt.contains("resumed after interruption"));
}

#[test]
fn pending_invocation_is_reconciled_without_repeat_and_before_new_work() {
    let d = Directory::new();
    let path = d.0.join("saved-run");
    let mut session = Session::create(task(&d, false), &path).unwrap();
    let request = session.request().unwrap();
    drop(session);
    let mut session = Session::open(&path).unwrap();
    assert!(session.recover_for_adoption().is_err());
    assert!(session.request().is_err());
    assert!(session.collected_response().is_err());
    session.accept(response(&request, Decision::Work)).unwrap();
    session.recover_for_adoption().unwrap();
    assert_eq!(session.request().unwrap().role, Role::Coordinator);
}

#[test]
fn cli_resume_does_not_redispatch_unknown_pending_work() {
    let d = Directory::new();
    d.command().stdin(Stdio::null()).output().unwrap();
    let run = d.0.join("run");
    let before = fs::read(run.join("state.json")).unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_workflow-harness"))
        .arg("--resume")
        .arg(&run)
        .stdin(Stdio::null())
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("no terminal receipt"));
    assert_eq!(before, fs::read(run.join("state.json")).unwrap());
    assert!(!run.join("request-2.json").exists());
}

#[cfg(unix)]
fn adapter(d: &Directory, body: &str) -> ProcessAdapter {
    let script = d.0.join("mechanical adapter.sh");
    fs::write(&script, body).unwrap();
    ProcessAdapter {
        program: "/bin/sh".into(),
        args: vec![
            script.to_string_lossy().into_owned(),
            d.0.join("calls.txt").to_string_lossy().into_owned(),
            std::env::current_dir()
                .unwrap()
                .join("Cargo.toml")
                .to_string_lossy()
                .into_owned(),
        ],
    }
}

#[cfg(unix)]
const ADAPTER: &str = r#"
input=$(cat)
id=$(printf '%s' "$input" | sed -n 's/.*"invocation_id": \([0-9]*\).*/\1/p')
printf '%s\n' "$id" >> "$1"
case "$id" in
1) role=coordinator; decision=work;;
2) role=worker; decision=observed;;
3) role=coordinator; decision=finish;;
*) exit 2;;
esac
printf '{"invocation_id":%s,"role":"%s","decision":"%s","summary":"Mechanical process check","assignment":"One bounded check","evidence":["%s"]}\n' "$id" "$role" "$decision" "$2"
"#;

#[test]
#[cfg(unix)]
fn automatic_process_adapter_completes_the_controlled_loop() {
    let d = Directory::new();
    let a = adapter(&d, ADAPTER);
    let config = d.0.join("adapter.json");
    fs::write(
        &config,
        serde_json::json!({"program":a.program,"args":a.args}).to_string(),
    )
    .unwrap();
    let output = d
        .command()
        .arg("--adapter")
        .arg(config)
        .stdin(Stdio::null())
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        fs::read_to_string(d.0.join("calls.txt")).unwrap(),
        "1\n2\n3\n"
    );
    let session = Session::open(&d.0.join("run")).unwrap();
    assert!(session.runtime.terminal().is_some());
}

#[test]
#[cfg(unix)]
fn process_return_survives_interruption_before_adoption() {
    let d = Directory::new();
    let a = adapter(&d, ADAPTER);
    let path = d.0.join("saved-run");
    let mut session = Session::create(task(&d, false), &path).unwrap();
    session.request().unwrap();
    session.invoke(&a).unwrap();
    drop(session);
    let mut session = Session::open(&path).unwrap();
    let result = session.collected_response().unwrap();
    session.accept(result).unwrap();
    session.recover_for_adoption().unwrap();
    assert_eq!(session.request().unwrap().role, Role::Coordinator);
    assert_eq!(fs::read_to_string(d.0.join("calls.txt")).unwrap(), "1\n");
}

#[test]
#[cfg(unix)]
fn failed_process_keeps_unknown_effects_and_is_not_retried() {
    let d = Directory::new();
    let a = adapter(
        &d,
        "cat >/dev/null\nprintf 'acted\\n' >> \"$1\"\nprintf 'partial output'\nexit 1\n",
    );
    let path = d.0.join("saved-run");
    let mut session = Session::create(task(&d, false), &path).unwrap();
    session.request().unwrap();
    assert!(session.invoke(&a).is_err());
    assert!(session.invoke(&a).is_err());
    drop(session);
    let session = Session::open(&path).unwrap();
    assert!(session.collected_response().is_err());
    assert!(session.runtime.outstanding().is_some());
    assert_eq!(
        fs::read_to_string(d.0.join("calls.txt")).unwrap(),
        "acted\n"
    );
}

fn host_command(
    d: &Directory,
    operation: &str,
    value: Option<serde_json::Value>,
) -> std::process::Output {
    let mut command = Command::new(env!("CARGO_BIN_EXE_workflow-harness"));
    command.args(["host", operation]);
    if operation == "start" {
        fs::write(
            d.0.join("host-task.json"),
            serde_json::to_vec(&task(d, false)).unwrap(),
        )
        .unwrap();
        command.arg(d.0.join("host-task.json"));
    }
    let mut child = command
        .arg(d.0.join("host-run"))
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    if let Some(value) = value {
        child
            .stdin
            .take()
            .unwrap()
            .write_all(&serde_json::to_vec(&value).unwrap())
            .unwrap();
    }
    child.wait_with_output().unwrap()
}

#[test]
fn host_bridge_preserves_normal_roles_and_correlates_actual_handles() {
    let d = Directory::new();
    let start = host_command(&d, "start", None);
    assert!(start.status.success());
    let mut request: workflow_harness::Invocation = serde_json::from_slice(&start.stdout).unwrap();
    for (id, role, decision, handle) in [
        (1, Role::Coordinator, Decision::Work, "host-coordinator"),
        (2, Role::Worker, Decision::Observed, "host-worker"),
        (3, Role::Coordinator, Decision::Finish, "host-coordinator"),
    ] {
        assert_eq!(request.invocation_id, id);
        assert_eq!(request.role, role);
        let binding = serde_json::json!({"invocation_id":id,"backend_handle":handle});
        assert!(
            host_command(&d, "bind", Some(binding.clone()))
                .status
                .success()
        );
        assert!(host_command(&d, "bind", Some(binding)).status.success());
        assert!(!host_command(&d, "continue", None).status.success());
        let status = host_command(&d, "status", None);
        let status: serde_json::Value = serde_json::from_slice(&status.stdout).unwrap();
        assert_eq!(status["binding"]["backend_handle"], handle);
        let result = response(&request, decision);
        assert!(
            !host_command(
                &d,
                "return",
                Some(serde_json::json!({"backend_handle":"wrong-host","response":result}))
            )
            .status
            .success()
        );
        let output = host_command(
            &d,
            "return",
            Some(serde_json::json!({"backend_handle":handle,"response":result})),
        );
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        if id < 3 {
            request = serde_json::from_slice(&output.stdout).unwrap();
        } else {
            assert!(String::from_utf8_lossy(&output.stdout).contains("pilot_terminal"));
        }
    }
}

#[test]
fn host_binding_recovers_temporary_write_and_cannot_be_bypassed_by_process_or_legacy_return() {
    let d = Directory::new();
    let path = d.0.join("host-run");
    let mut session = Session::create(task(&d, false), &path).unwrap();
    let request = session.request().unwrap();
    fs::write(path.join("host-1.next.json"), "{partial").unwrap();
    assert!(session.host_binding().unwrap().is_none());
    let binding = HostBinding {
        invocation_id: 1,
        backend_handle: "existing-host-agent".into(),
    };
    session.bind_host(binding.clone()).unwrap();
    assert_eq!(session.host_binding().unwrap(), Some(binding));
    assert!(
        session
            .bind_host(HostBinding {
                invocation_id: 1,
                backend_handle: "another-agent".into()
            })
            .is_err()
    );
    let result = response(&request, Decision::Work);
    assert!(session.accept(result.clone()).is_err());
    assert!(
        session
            .invoke(&ProcessAdapter {
                program: "/unused".into(),
                args: vec![]
            })
            .is_err()
    );
    assert!(!path.join("stdout-1.json").exists());
    drop(session);
    fs::write(
        d.0.join("legacy-return.json"),
        serde_json::to_vec(&result).unwrap(),
    )
    .unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_workflow-harness"))
        .arg("--resume")
        .arg(&path)
        .arg("--response")
        .arg(d.0.join("legacy-return.json"))
        .stdin(Stdio::null())
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("host-bound"));
    let mut session = Session::open(&path).unwrap();
    session
        .accept_host_return("existing-host-agent", result.clone())
        .unwrap();
    assert!(
        session
            .accept_host_return("existing-host-agent", result)
            .is_err()
    );
}
