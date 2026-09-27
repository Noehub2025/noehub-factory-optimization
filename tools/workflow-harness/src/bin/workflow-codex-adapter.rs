//! Optional Codex CLI backend. The Workflow library does not import this binary.
//! One native turn produces one correlated return; failures never rerun work.

use serde_json::{Value, json};
use std::ffi::OsString;
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
use std::time::{Duration, Instant};
use workflow_harness::{Invocation, Response, Result, Role};

struct Options {
    codex: OsString,
    model: Option<OsString>,
    profile: Option<OsString>,
    worker_sandbox: String,
}

fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}

fn run() -> Result<()> {
    let mut options = Options {
        codex: "codex".into(),
        model: None,
        profile: None,
        worker_sandbox: "read-only".into(),
    };
    let mut configure = None;
    let mut check = false;
    let mut args = std::env::args_os().skip(1);
    let mut stored_args = vec![];
    while let Some(arg) = args.next() {
        if arg == "--capabilities" {
            println!(
                "{}",
                json!({"protocol":"workflow-invocation/1",
                "backend":"codex-exec", "automatic_dispatch":true,
                "delivery":"exact prompt file passed to codex exec stdin",
                "effective_context_verified":false,"native_events":true,
                "safe_mid_invocation_interrupt":false,
                "external_effect_recovery":false,
                "isolation":"Codex CLI sandbox; not isolation of every external tool"})
            );
            return Ok(());
        }
        if arg == "--check" {
            check = true;
            continue;
        }
        let value = args
            .next()
            .ok_or_else(|| format!("{} requires a value", arg.to_string_lossy()))?;
        match arg.to_str() {
            Some("--configure") => configure = Some(PathBuf::from(value)),
            Some("--codex") => {
                // Saved configurations run in the task workspace, not this directory.
                // Keep bare command names on PATH; bind relative file paths here.
                let path = Path::new(&value);
                let value = if path.is_relative() && path.components().count() > 1 {
                    std::env::current_dir()
                        .map_err(|e| e.to_string())?
                        .join(path)
                        .into_os_string()
                } else {
                    value
                };
                options.codex = value.clone();
                stored_args.extend([arg, value]);
            }
            Some("--model") => {
                options.model = Some(value.clone());
                stored_args.extend([arg, value]);
            }
            Some("--profile") => {
                options.profile = Some(value.clone());
                stored_args.extend([arg, value]);
            }
            Some("--worker-sandbox") => {
                options.worker_sandbox = value.to_str().ok_or("sandbox must be UTF-8")?.into();
                if !["read-only", "workspace-write"].contains(&options.worker_sandbox.as_str()) {
                    return Err("worker sandbox must be read-only or workspace-write".into());
                }
                stored_args.extend([arg, value]);
            }
            _ => return Err(format!("unknown option: {}", arg.to_string_lossy())),
        }
    }
    if let Some(path) = configure {
        if check {
            return Err("run --check separately from --configure".into());
        }
        let args: Vec<_> = stored_args
            .iter()
            .map(|v| {
                v.to_str()
                    .ok_or("adapter configuration arguments must be UTF-8")
            })
            .collect::<std::result::Result<_, _>>()?;
        let config =
            json!({"program":std::env::current_exe().map_err(|e|e.to_string())?, "args":args});
        write_new(
            &path,
            &serde_json::to_vec_pretty(&config).map_err(|e| e.to_string())?,
        )?;
        eprintln!("Adapter configuration written to {}", path.display());
        return Ok(());
    }
    if check {
        let version = inspect_cli(Command::new(&options.codex).arg("--version"))?;
        if !version.status.success() {
            return Err(format!(
                "Codex executable check failed ({}); no Agent was invoked",
                version.status
            ));
        }
        io::stdout()
            .write_all(&version.stdout)
            .map_err(|e| e.to_string())?;
        let output = inspect_cli(Command::new(&options.codex).args(["exec", "--help"]))?;
        let help = String::from_utf8_lossy(&output.stdout);
        if !output.status.success()
            || [
                "--json",
                "--output-schema",
                "--output-last-message",
                "--sandbox",
            ]
            .iter()
            .any(|flag| !help.contains(flag))
        {
            return Err(
                "Codex exec lacks required invocation/output flags; no Agent was invoked".into(),
            );
        }
        eprintln!(
            "Required CLI flags are available. Authentication and model access still require a real invocation."
        );
        return Ok(());
    }
    let mut input = String::new();
    io::stdin()
        .read_to_string(&mut input)
        .map_err(|e| e.to_string())?;
    let request: Invocation = serde_json::from_str(&input).map_err(|e| e.to_string())?;
    if request.protocol != "workflow-invocation/1" || request.prompt.trim().is_empty() {
        return Err("unsupported or empty invocation".into());
    }
    let directory = std::env::var_os("WORKFLOW_INVOCATION_DIRECTORY")
        .map(PathBuf::from)
        .ok_or("run this adapter through workflow-harness; invocation directory is missing")?;
    let response = invoke(&options, &request, &directory)?;
    println!(
        "{}",
        serde_json::to_string(&response).map_err(|e| e.to_string())?
    );
    Ok(())
}

/// Only executable metadata checks use this timeout. Never use it for Agent work.
fn inspect_cli(command: &mut Command) -> Result<Output> {
    let mut child = command
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| e.to_string())?;
    let start = Instant::now();
    loop {
        if child.try_wait().map_err(|e| e.to_string())?.is_some() {
            return child.wait_with_output().map_err(|e| e.to_string());
        }
        if start.elapsed() >= Duration::from_secs(10) {
            child.kill().map_err(|e| e.to_string())?;
            child.wait().map_err(|e| e.to_string())?;
            return Err(
                "CLI metadata check timed out after 10 seconds; no Agent was invoked".into(),
            );
        }
        std::thread::sleep(Duration::from_millis(25));
    }
}

fn write_new(path: &Path, bytes: &[u8]) -> Result<()> {
    let mut file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|e| e.to_string())?;
    file.write_all(bytes).map_err(|e| e.to_string())?;
    file.sync_all().map_err(|e| e.to_string())
}

fn schema(request: &Invocation) -> Value {
    json!({"type":"object", "additionalProperties":false,
    "required":["invocation_id","role","decision","summary","assignment","evidence"],
    "properties":{
        "invocation_id":{"type":"integer","enum":[request.invocation_id]},
        "role":{"type":"string","enum":[request.role]},
        "decision":{"type":"string","enum":["work","reconsider","observed","finish","blocked"]},
        "summary":{"type":"string"},"assignment":{"type":"string"},
        "evidence":{"type":"array","items":{"type":"string"}}
    }})
}

fn invoke(options: &Options, request: &Invocation, directory: &Path) -> Result<Response> {
    if !directory.is_absolute() || !directory.is_dir() {
        return Err("invocation directory must be an existing absolute directory".into());
    }
    let prompt = directory.join("prompt.txt");
    let schema_path = directory.join("response-schema.json");
    let final_path = directory.join("final-response.json");
    if final_path.exists() {
        return Err(
            "a native response already exists; reconcile it instead of repeating the invocation"
                .into(),
        );
    }
    write_new(&prompt, request.prompt.as_bytes())?;
    write_new(
        &schema_path,
        &serde_json::to_vec_pretty(&schema(request)).map_err(|e| e.to_string())?,
    )?;
    let events = directory.join("native-events.jsonl");
    let output = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&events)
        .map_err(|e| e.to_string())?;
    let diagnostics = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(directory.join("native-stderr.txt"))
        .map_err(|e| e.to_string())?;
    let sandbox = if request.role == Role::Worker {
        options.worker_sandbox.as_str()
    } else {
        "read-only"
    };
    let mut command = Command::new(&options.codex);
    command.args(["--ask-for-approval", "never"]);
    if let Some(profile) = &options.profile {
        command.arg("--profile").arg(profile);
    }
    command
        .args(["exec", "--json", "--color", "never", "--sandbox", sandbox])
        .arg("--output-schema")
        .arg(&schema_path)
        .arg("--output-last-message")
        .arg(&final_path);
    if let Some(model) = &options.model {
        command.arg("--model").arg(model);
    }
    command
        .arg("-")
        .stdin(Stdio::from(File::open(&prompt).map_err(|e| e.to_string())?))
        .stdout(Stdio::from(output.try_clone().map_err(|e| e.to_string())?))
        .stderr(Stdio::from(
            diagnostics.try_clone().map_err(|e| e.to_string())?,
        ));
    let start = Instant::now();
    let status = command
        .status()
        .map_err(|e| format!("Codex could not be invoked: {e}; no automatic retry"))?;
    output.sync_all().map_err(|e| e.to_string())?;
    diagnostics.sync_all().map_err(|e| e.to_string())?;
    write_new(&directory.join("native-exit.json"), &serde_json::to_vec_pretty(&json!({
        "invocation_id":request.invocation_id,"success":status.success(),
        "exit_code":status.code(),"status":status.to_string(),"elapsed_ms":start.elapsed().as_millis()
    })).map_err(|e|e.to_string())?)?;
    if !status.success() {
        return Err(format!(
            "Codex invocation failed ({status}); inspect {}, retain pending work, and do not automatically retry",
            directory.display()
        ));
    }
    let metadata = completed_turn(&events)?;
    let response: Response = serde_json::from_slice(
        &fs::read(&final_path).map_err(|e| e.to_string())?,
    )
    .map_err(|e| format!("invalid native response: {e}; preserve work and correct the return"))?;
    if response.invocation_id != request.invocation_id || response.role != request.role {
        return Err(
            "native response does not match the invocation; preserve it without adoption".into(),
        );
    }
    write_new(
        &directory.join("native-completion.json"),
        &serde_json::to_vec_pretty(&metadata).map_err(|e| e.to_string())?,
    )?;
    Ok(response)
}

fn completed_turn(path: &Path) -> Result<Value> {
    let mut thread = Value::Null;
    let mut completion = None;
    for line in BufReader::new(File::open(path).map_err(|e| e.to_string())?).lines() {
        let event: Value = serde_json::from_str(&line.map_err(|e| e.to_string())?)
            .map_err(|e| format!("invalid native event stream: {e}"))?;
        match event["type"].as_str() {
            Some("thread.started") => thread = event["thread_id"].clone(),
            Some("turn.completed") => completion = Some(event),
            Some("turn.started" | "turn.failed" | "error") => completion = None,
            _ => {}
        }
    }
    let terminal = completion.ok_or(
        "no successful native turn completion; output alone does not complete an invocation",
    )?;
    Ok(json!({"thread_id":thread,"usage":terminal["usage"]}))
}
