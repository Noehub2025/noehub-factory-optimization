//! Mechanical native-CLI fixtures; these are not real model or optimization trials.
#![cfg(unix)]

use serde_json::{Value, json};
use std::fs;
use std::io::Write;
use std::os::unix::fs::PermissionsExt;
use std::path::PathBuf;
use std::process::{Command, Output, Stdio};
use std::sync::atomic::{AtomicUsize, Ordering};
use workflow_harness::{Invocation, Role};

static NEXT: AtomicUsize = AtomicUsize::new(0);
struct Directory(PathBuf);
impl Directory {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "workflow-codex-test-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).unwrap();
        Self(path)
    }
}
impl Drop for Directory {
    fn drop(&mut self) {
        fs::remove_dir_all(&self.0).unwrap();
    }
}

struct Fixture {
    directory: Directory,
    request: Invocation,
}
impl Fixture {
    fn new() -> Self {
        let d = Directory::new();
        let script = d.0.join("codex fixture");
        fs::write(
            &script,
            r#"#!/bin/sh
printf '%s\n' "$@" > "$FIXTURE_ARGUMENTS"
printf 'invoked\n' >> "$FIXTURE_CALLS"
while [ "$#" -gt 0 ]; do
  case "$1" in --output-last-message) shift; final=$1;; esac
  shift
done
cat > "$FIXTURE_PROMPT"
cp "$FIXTURE_RESPONSE" "$final"
cat "$FIXTURE_EVENTS"
exit "$FIXTURE_EXIT"
"#,
        )
        .unwrap();
        fs::set_permissions(&script, fs::Permissions::from_mode(0o700)).unwrap();
        fs::create_dir(d.0.join("trace")).unwrap();
        fs::write(d.0.join("response.json"), json!({"invocation_id":1,"role":"coordinator","decision":"finish","summary":"Mechanical fixture only","assignment":"","evidence":[std::env::current_dir().unwrap().join("Cargo.toml")]}).to_string()).unwrap();
        fs::write(d.0.join("events.jsonl"), "{\"type\":\"thread.started\",\"thread_id\":\"fixture-thread\"}\n{\"type\":\"turn.completed\",\"usage\":{\"input_tokens\":10,\"output_tokens\":5}}\n").unwrap();
        Self {
            directory: d,
            request: Invocation {
                contract: None,
                protocol: "workflow-invocation/1".into(),
                invocation_id: 1,
                role: Role::Coordinator,
                prompt: "Literal source text with spaces, 中文, `backticks` and $(substitution).\n"
                    .into(),
            },
        }
    }

    fn command(&self) -> Command {
        let d = &self.directory.0;
        let mut command = Command::new(env!("CARGO_BIN_EXE_workflow-codex-adapter"));
        command
            .args(["--codex"])
            .arg(d.join("codex fixture"))
            .args(["--worker-sandbox", "workspace-write"])
            .env("WORKFLOW_INVOCATION_DIRECTORY", d.join("trace"))
            .env("FIXTURE_ARGUMENTS", d.join("arguments.txt"))
            .env("FIXTURE_PROMPT", d.join("prompt.txt"))
            .env("FIXTURE_RESPONSE", d.join("response.json"))
            .env("FIXTURE_EVENTS", d.join("events.jsonl"))
            .env("FIXTURE_CALLS", d.join("calls.txt"))
            .env("FIXTURE_EXIT", "0");
        command
    }

    fn run(&self, exit: &str) -> Output {
        let mut child = self
            .command()
            .env("FIXTURE_EXIT", exit)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        child
            .stdin
            .take()
            .unwrap()
            .write_all(&serde_json::to_vec(&self.request).unwrap())
            .unwrap();
        child.wait_with_output().unwrap()
    }
}

#[test]
fn native_adapter_preserves_prompt_correlation_trace_and_role_sandbox() {
    let f = Fixture::new();
    let output = f.run("0");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let result: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(result["invocation_id"], 1);
    let d = &f.directory.0;
    assert_eq!(
        fs::read_to_string(d.join("prompt.txt")).unwrap(),
        f.request.prompt
    );
    let arguments = fs::read_to_string(d.join("arguments.txt")).unwrap();
    assert!(arguments.contains("--ask-for-approval\nnever\nexec\n--json"));
    assert!(arguments.contains("--sandbox\nread-only\n"));
    assert!(!arguments.contains("workspace-write"));
    let metadata: Value =
        serde_json::from_slice(&fs::read(d.join("trace/native-completion.json")).unwrap()).unwrap();
    assert_eq!(metadata["thread_id"], "fixture-thread");
    assert_eq!(metadata["usage"]["input_tokens"], 10);
    assert!(!f.run("0").status.success());
    assert_eq!(
        fs::read_to_string(d.join("calls.txt")).unwrap(),
        "invoked\n"
    );
}

#[test]
fn output_without_native_completion_or_with_later_failure_is_not_adopted() {
    for events in [
        "{\"type\":\"turn.started\"}\n",
        "{\"type\":\"turn.completed\"}\n{\"type\":\"turn.failed\"}\n",
        "{\"type\":\"turn.completed\"}\n{\"type\":\"turn.started\"}\n",
    ] {
        let f = Fixture::new();
        fs::write(f.directory.0.join("events.jsonl"), events).unwrap();
        let output = f.run("0");
        assert!(!output.status.success());
        assert!(output.stdout.is_empty());
        assert!(f.directory.0.join("trace/final-response.json").exists());
        assert!(!f.directory.0.join("trace/native-completion.json").exists());
    }
}

#[test]
fn failed_process_or_mismatched_return_is_preserved_without_retry() {
    for exit in ["0", "1"] {
        let f = Fixture::new();
        fs::write(f.directory.0.join("response.json"),json!({"invocation_id":99,"role":"coordinator","decision":"finish","summary":"Mismatch","assignment":"","evidence":[]}).to_string()).unwrap();
        let output = f.run(exit);
        assert!(!output.status.success());
        assert!(output.stdout.is_empty());
        assert_eq!(
            fs::read_to_string(f.directory.0.join("calls.txt")).unwrap(),
            "invoked\n"
        );
        assert!(f.directory.0.join("trace/native-exit.json").exists());
    }
}

#[test]
fn generated_configuration_drives_the_runtime_through_the_native_adapter() {
    let f = Fixture::new();
    let d = &f.directory.0;
    let config = d.join("adapter.json");
    let setup = f
        .command()
        .current_dir(d)
        .args(["--codex", "./codex fixture"])
        .arg("--configure")
        .arg(&config)
        .output()
        .unwrap();
    assert!(setup.status.success());
    let saved: Value = serde_json::from_slice(&fs::read(&config).unwrap()).unwrap();
    let last_cli = saved["args"]
        .as_array()
        .unwrap()
        .windows(2)
        .rfind(|pair| pair[0] == "--codex")
        .unwrap()[1]
        .as_str()
        .unwrap();
    assert!(std::path::Path::new(last_cli).is_absolute());
    assert!(
        !d.join("calls.txt").exists(),
        "configuration must not invoke a model"
    );
    fs::write(d.join("task.json"),json!({"objective":"Mechanical native integration check","workspace":std::env::current_dir().unwrap(),"constraints":"No research claim","sources":[],"invocation_limit":1}).to_string()).unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_workflow-harness"))
        .arg(d.join("task.json"))
        .arg(d.join("run"))
        .arg("--adapter")
        .arg(&config)
        .envs(
            f.command()
                .get_envs()
                .filter_map(|(k, v)| v.map(|v| (k, v))),
        )
        .stdin(Stdio::null())
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(String::from_utf8_lossy(&output.stdout).contains("pilot_terminal"));
    assert!(d.join("run/backend-1/native-completion.json").exists());
    assert_eq!(
        fs::read_to_string(d.join("calls.txt")).unwrap(),
        "invoked\n"
    );
}

#[test]
fn executable_preflight_checks_flags_and_bounds_a_hung_metadata_command() {
    let f = Fixture::new();
    let cli = f.directory.0.join("codex fixture");
    fs::write(&cli, "#!/bin/sh\ncase \"$1\" in --version) echo fixture-version;; exec) echo '--json --output-schema --output-last-message --sandbox';; *) exit 1;; esac\n").unwrap();
    assert!(
        f.command()
            .arg("--check")
            .output()
            .unwrap()
            .status
            .success()
    );
    fs::write(&cli, "#!/bin/sh\nexec /bin/sleep 30\n").unwrap();
    let start = std::time::Instant::now();
    let output = f.command().arg("--check").output().unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("metadata check timed out"));
    assert!(start.elapsed() < std::time::Duration::from_secs(20));
    assert!(!f.directory.0.join("calls.txt").exists());
}
