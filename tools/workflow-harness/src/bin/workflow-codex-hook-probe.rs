//! A disposable host-boundary probe, not an investment policy or action sandbox.
//! It declines exactly one read of existing B141 evidence and observes no contents.

use serde_json::{Value, json};
use std::fs::{self, OpenOptions};
use std::io::{self, Read, Write};
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

const PROBE_COMMAND: &str = "sed -n '1,12p' artifacts/workflow-harness/current-host-b141-2026-09-20/coordinator-1/findings.md";

fn main() {
    if std::env::args_os().nth(3).as_deref() == Some(std::ffi::OsStr::new("--observe")) {
        if let Err(error) = observe() {
            eprintln!("Workflow hook observation failed: {error}");
        }
        // Diagnostics never approve, reject, or rewrite an action.
        println!("{{}}");
        return;
    }
    if let Err(error) = run() {
        // Exit 2 is the documented blocking result. Never silently pass a
        // malformed event or failed receipt while evaluating this probe.
        eprintln!("Workflow hook probe failed: {error}");
        std::process::exit(2);
    }
}

fn observe() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    let root = fs::canonicalize(PathBuf::from(&args[0]))?;
    let receipts = fs::canonicalize(PathBuf::from(&args[1]))?;
    let mut input = String::new();
    io::stdin().read_to_string(&mut input)?;
    let parsed = serde_json::from_str::<Value>(&input);
    let event = parsed.as_ref().ok();
    let field = |name: &str| event.and_then(|e| e.get(name)).and_then(Value::as_str);
    let in_scope = field("cwd")
        .and_then(|cwd| fs::canonicalize(cwd).ok())
        .is_some_and(|cwd| cwd == root);
    let keys = |value: Option<&Value>| {
        value
            .and_then(Value::as_object)
            .map(|object| object.keys().cloned().collect::<Vec<_>>())
            .unwrap_or_default()
    };
    let receipt = json!({
        "probe":"workflow-hook-observation/1", "json_parsed":parsed.is_ok(),
        "session_id":field("session_id"), "turn_id":field("turn_id"),
        "tool_use_id":field("tool_use_id"), "agent_id":field("agent_id"),
        "tool_name":field("tool_name"), "hook_event_name":field("hook_event_name"),
        "source":field("source"), "in_scope":in_scope,
        "event_keys":keys(event),
        "tool_input_keys":keys(event.and_then(|e| e.get("tool_input")))
    });
    let timestamp = SystemTime::now().duration_since(UNIX_EPOCH)?.as_nanos();
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(receipts.join(format!("observe-{}-{timestamp}.json", std::process::id())))?;
    serde_json::to_writer(&mut file, &receipt)?;
    file.write_all(b"\n")?;
    file.sync_all()?;
    Ok(())
}

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    if args.len() != 2 {
        return Err("expected absolute workspace and existing receipt directory".into());
    }
    let root = fs::canonicalize(PathBuf::from(&args[0]))?;
    let receipts = fs::canonicalize(PathBuf::from(&args[1]))?;
    let mut input = String::new();
    io::stdin().read_to_string(&mut input)?;
    let event: Value = serde_json::from_str(&input)?;
    let cwd = event["cwd"].as_str().ok_or("missing cwd")?;
    let in_scope = fs::canonicalize(cwd)? == root;
    let event_name = event["hook_event_name"]
        .as_str()
        .ok_or("missing event name")?;
    let tool = event["tool_name"].as_str().ok_or("missing tool name")?;
    let deny = in_scope
        && event_name == "PreToolUse"
        && tool == "Bash"
        && event["tool_input"]["command"].as_str() == Some(PROBE_COMMAND);

    if in_scope {
        // Each callback publishes its own file. No command text, tool output,
        // transcript, environment variables, or credentials enter receipts.
        let receipt = json!({
            "session_id":event["session_id"], "turn_id":event["turn_id"],
            "tool_use_id":event["tool_use_id"], "tool_name":tool,
            "hook_event_name":event_name, "denied":deny,
            "probe":"workflow-b141-pre-tool-use/1"
        });
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(receipts.join(format!("event-{}.json", std::process::id())))?;
        serde_json::to_writer(&mut file, &receipt)?;
        file.write_all(b"\n")?;
        file.sync_all()?;
    }

    let output = if deny {
        json!({"hookSpecificOutput":{
            "hookEventName":"PreToolUse", "permissionDecision":"deny",
            "permissionDecisionReason":"Workflow boundary probe: this exact B141 evidence read was withheld before execution. Report the rejection; do not retry or substitute another command. This is an adapter check, not an investment decision."
        }})
    } else {
        // No opinion: do not approve a call or override other host controls.
        json!({})
    };
    println!("{output}");
    Ok(())
}
