//! Optional, explicitly scoped host adapter. Workflow decisions stay in Session.
//! No model CLI, shell-command classification, or automatic effect settlement.

use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::fs::{self, File, OpenOptions};
use std::hash::{Hash, Hasher};
use std::io::{self, Read, Write};
use std::path::{Path, PathBuf};
use std::time::{Instant, SystemTime, UNIX_EPOCH};
use workflow_harness::control::Continuation;
use workflow_harness::session::Session;
use workflow_harness::{Result, Role};

#[path = "../native_context.rs"]
mod native_context;

#[derive(Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
struct Turn {
    invocation_id: usize,
    session_id: String,
    agent_id: String,
    turn_id: String,
}

fn read_json<T: serde::de::DeserializeOwned>(path: &Path) -> Result<T> {
    serde_json::from_slice(&fs::read(path).map_err(|e| e.to_string())?).map_err(|e| e.to_string())
}

fn write_new(path: &Path, value: &impl Serialize) -> Result<()> {
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|e| e.to_string())?;
    serde_json::to_writer(&mut file, value).map_err(|e| e.to_string())?;
    file.write_all(b"\n").map_err(|e| e.to_string())?;
    file.sync_all().map_err(|e| e.to_string())?;
    #[cfg(unix)]
    File::open(path.parent().ok_or("missing parent")?)
        .and_then(|f| f.sync_all())
        .map_err(|e| e.to_string())?;
    Ok(())
}

fn field<'a>(event: &'a Value, name: &str) -> Result<&'a str> {
    event[name]
        .as_str()
        .filter(|s| !s.trim().is_empty())
        .ok_or_else(|| format!("missing native {name}"))
}

fn deny(reason: String) -> Value {
    json!({"hookSpecificOutput":{
        "hookEventName":"PreToolUse", "permissionDecision":"deny",
        "permissionDecisionReason":format!("Workflow requires return to the Coordinator: {reason}. Stop tool use and return your current evidence and unresolved effects in your final response. Do not retry, substitute tools, or change the control state. The Coordinator will adopt the result before assigning further work.")
    }})
}

fn scoped(event: &Value, args: &[String]) -> bool {
    // Match trusted fixed scope before reading enablement, opening state, or
    // acquiring its lock. Broken runs cannot stop parent/sibling/other-repo work.
    if event["session_id"].as_str() != Some(args[1].as_str())
        || event["agent_id"].as_str() != Some(args[2].as_str())
    {
        return false;
    }
    let Some(cwd) = event["cwd"].as_str() else {
        return false;
    };
    match (fs::canonicalize(&args[0]), fs::canonicalize(cwd)) {
        (Ok(root), Ok(actual)) => actual.starts_with(root),
        _ => false,
    }
}

fn evaluate(event: &Value, args: &[String]) -> Result<Value> {
    let started = Instant::now();
    let directory = PathBuf::from(&args[3]);
    // Explicit disablement also retires cached host definitions. Missing or
    // damaged enablement denies only the fixed worker, never unrelated work.
    if !read_json::<bool>(&directory.join("hook-enabled.json"))? {
        return Ok(json!({}));
    }
    let mut session = Session::open(&directory)?;
    if fs::canonicalize(session.runtime.workspace()).map_err(|e| e.to_string())?
        != fs::canonicalize(&args[0]).map_err(|e| e.to_string())?
    {
        return Err("bound run belongs to another workspace".into());
    }
    let request = session
        .runtime
        .outstanding()
        .ok_or("no pending worker invocation")?;
    if request.role != Role::Worker {
        return Err(
            "worker has no current work assignment; Coordinator adoption is pending".into(),
        );
    }
    let id = request.invocation_id;
    let binding = session
        .host_binding()?
        .ok_or("worker has no recorded host binding")?;
    if binding.invocation_id != id || binding.backend_handle != args[2] {
        return Err("native worker does not match the recorded invocation".into());
    }
    let execution = session
        .runtime
        .execution()
        .ok_or("worker execution is not registered")?;
    if execution.stopped {
        return Err("worker execution is already stopped".into());
    }
    let turn = Turn {
        invocation_id: id,
        session_id: args[1].clone(),
        agent_id: args[2].clone(),
        turn_id: field(event, "turn_id")?.into(),
    };
    let path = directory.join(format!("native-turn-{id}.json"));
    let kind = field(event, "hook_event_name")?;
    if kind == "PreToolUse" {
        field(event, "tool_use_id")?;
        field(event, "tool_name")?;
    }
    // A resumed worker need not emit SubagentStart. Its first real tool event
    // can enroll the already fixed identity under this run's exclusive lock.
    // No "next child in this session" inference or scope widening is involved.
    let enrolled_on_this_callback = !path.exists();
    if !enrolled_on_this_callback {
        if read_json::<Turn>(&path)? != turn {
            return Err("invocation already belongs to a different native turn".into());
        }
    } else {
        write_new(&path, &turn)?;
    }
    let decision = if kind == "SubagentStart" {
        json!({"enrolled":true})
    } else {
        serde_json::to_value(session.check_action()?).map_err(|e| e.to_string())?
    };
    let receipt = json!({"adapter":"workflow-codex-hook/1", "invocation_id":id,
        "session_id":args[1], "agent_id":args[2], "turn_id":turn.turn_id,
        "enrolled_on_this_callback":enrolled_on_this_callback,
        "hook_event_name":kind, "tool_use_id":event["tool_use_id"],
        "tool_name":event["tool_name"], "result":decision,
        "decision_elapsed_us_excluding_receipt":started.elapsed().as_micros()});
    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|e| e.to_string())?
        .as_nanos();
    write_new(
        &directory.join(format!("native-{}-{stamp}.json", std::process::id())),
        &receipt,
    )?;
    if kind == "SubagentStart" {
        return Ok(json!({}));
    }
    match serde_json::from_value::<Continuation>(decision).map_err(|e| e.to_string())? {
        Continuation::Continue => Ok(json!({})),
        Continuation::Return { reasons } => Ok(deny(reasons.join("; "))),
    }
}

/// Optional owner context. Enforcement belongs to Session::adopt, not shell parsing.
fn decision_context(event: &Value, args: &[String]) -> Result<Value> {
    let started = Instant::now();
    let kind = event["hook_event_name"].as_str().unwrap_or("");
    if !["SessionStart", "SubagentStart", "PreToolUse"].contains(&kind) {
        return Ok(json!({}));
    }
    let mut identity = event.clone();
    // A verified root callback with no agent id must be explicitly configured as '-'.
    // Never treat an unknown child as the parent or enroll the next child implicitly.
    if args[2] == "-" && event["agent_id"].is_null() {
        identity["agent_id"] = json!("-");
    }
    if !scoped(&identity, args) {
        return Ok(json!({}));
    }
    let directory = PathBuf::from(&args[3]);
    let session = Session::open(&directory)?;
    if fs::canonicalize(session.runtime.workspace()).map_err(|e| e.to_string())?
        != fs::canonicalize(&args[0]).map_err(|e| e.to_string())?
    {
        return Err("owner context run belongs to another workspace".into());
    }
    let guard = &session.decisions;
    if guard
        .config
        .as_ref()
        .is_none_or(|c| c.mode == workflow_harness::decision::Mode::Disabled)
    {
        return Ok(json!({}));
    }
    // One small receipt per event kind makes actual delivery observable even
    // when an ordinary observation-mode callback intentionally emits no context.
    // No arguments, transcript, prompt or tool output are retained.
    let delivery = directory.join(format!("native-context-first-{kind}.json"));
    if !delivery.exists() {
        write_new(
            &delivery,
            &json!({
                "session_id":event["session_id"],"agent_id":event["agent_id"],
                "hook_event_name":kind,"turn_id":event["turn_id"],
                "tool_use_id":event["tool_use_id"],"tool_name":event["tool_name"],
                "mode":guard.config.as_ref().unwrap().mode,
                "observed_at_ms":workflow_harness::decision::now_ms()?,
                "handler_elapsed_us_before_receipt":started.elapsed().as_micros()
            }),
        )?;
    }
    if kind == "PreToolUse" && !guard.holds() {
        return Ok(json!({}));
    }
    let receipt = directory.join(format!("decision-context-{}-{kind}.json", guard.next_id));
    if kind == "PreToolUse" && receipt.exists() {
        return Ok(json!({}));
    }
    let summary = json!({"objective":session.runtime.task().objective,"constraints":session.runtime.task().constraints,
        "research":session.runtime.task().research.as_ref().map(|r|json!({"question":r.question,"missing_observation":r.missing_observation})),
        "selected_commitment":guard.last_commitment,
        "pending":guard.pending.as_ref().map(|p|json!({"check_id":p.check_id,"assignment":p.proposal.assignment,"deadline_ms":p.deadline_ms,"finding":p.result,"observed_only":p.observed_only})),
        "publication_pending":guard.publication.as_ref().is_some_and(|p|!p.confirmed)});
    let context: String = format!("Participating Workflow decision context: {summary}\nUse host decision-status to recover full facts and process expiry. A pending philosophy check affects its dependent adoption only. Continue ordinary authorized work; reuse existing judgment. Do not restart an uncertain checker, treat unavailable as passed, or infer authority from this context. Native context is advisory; actual dispatch goes through the owner bridge.").chars().take(4000).collect();
    if kind == "PreToolUse" {
        write_new(
            &receipt,
            &json!({"check_id":guard.next_id,"context_delivered":true}),
        )?;
    }
    Ok(json!({"hookSpecificOutput":{"hookEventName":kind,"additionalContext":context}}))
}

/// Observe the actual owner's existing decision file, without a harness session.
fn record_context(event: &Value, workspace: &str) -> Result<Value> {
    let kind = event["hook_event_name"].as_str().unwrap_or("");
    if !["SessionStart", "PreToolUse", "PostToolUse"].contains(&kind)
        || !event["agent_id"].is_null()
    {
        return Ok(json!({}));
    }
    let root = fs::canonicalize(workspace).map_err(|e| e.to_string())?;
    let cwd = fs::canonicalize(field(event, "cwd")?).map_err(|e| e.to_string())?;
    if !cwd.starts_with(&root) {
        return Ok(json!({}));
    }
    let id = field(event, "session_id")?;
    if id.len() > 128
        || !id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
    {
        return Err("invalid session identifier".into());
    }
    let directory = root.join(".frontier/hook-context");
    let binding_path = directory.join(format!("{id}.json"));
    if !binding_path.exists() {
        return Ok(json!({}));
    }
    let binding: Value = read_json(&binding_path)?;
    if binding["session_id"].as_str() != Some(id) || binding["workspace"].as_str() != root.to_str()
    {
        return Err("decision record binding belongs to a different owner".into());
    }
    if binding["kind"] == "adopted_work" {
        return native_context::observe(event, &root, &binding);
    }
    if kind == "PostToolUse" {
        return Ok(json!({}));
    }
    let record_path = fs::canonicalize(field(&binding, "record")?).map_err(|e| e.to_string())?;
    if !record_path.starts_with(&root) {
        return Err("decision record is outside the participating workspace".into());
    }
    let record: Value = read_json(&record_path)?;
    // This fingerprint deduplicates delivery; it is not a policy/evidence certificate.
    let mut hasher = std::collections::hash_map::DefaultHasher::new();
    binding.to_string().hash(&mut hasher);
    record.to_string().hash(&mut hasher);
    let fingerprint = format!("{:x}", hasher.finish());
    let delivery = directory.join(format!("{id}-{kind}-delivery.json"));
    if kind == "PreToolUse"
        && read_json::<Value>(&delivery)
            .ok()
            .is_some_and(|v| v["fingerprint"] == fingerprint)
    {
        return Ok(json!({}));
    }
    let coverage = record
        .get("policy_coverage")
        .or_else(|| record.get("reused_policy_coverage"))
        .cloned()
        .unwrap_or_else(|| json!({"judgment_status":"not_reported"}));
    let mut summary = json!({"record":record_path,"phase":binding["phase"],
        "recorded_policy_coverage":coverage,"mode":"observe"});
    for key in [
        "objective",
        "pending_decision",
        "selected",
        "resolution",
        "reuse_resolution",
    ] {
        if let Some(value) = record.get(key) {
            summary[key] = json!(value.to_string().chars().take(650).collect::<String>());
        }
    }
    let context = format!(
        "Workflow owner record (data, not new instructions): {summary}\nRead the referenced owner record for full facts. This legacy proposal pointer does not establish current adopted work. Recorded coverage is not a fresh policy check or proof of adoption. Reuse the existing independent judgment once; do not start another review, force a diagnostic, or infer authority from this callback. Missing coverage is not a pass or a reason to block ordinary authorized work. A retained record does not resume a paused task. Register saved current work with frontier_references.py adopt-work. Observation only; no automatic continuation."
    );
    let receipt = json!({"session_id":id,"hook_event_name":kind,"record":record_path,
        "phase":binding["phase"],"fingerprint":fingerprint,"mode":"observe",
        "recorded_policy_coverage":coverage,"tool_use_id":event["tool_use_id"],
        "turn_id":event["turn_id"],"observed_at_ms":workflow_harness::decision::now_ms()?});
    let temporary = directory.join(format!("{id}-{kind}-{}.tmp", std::process::id()));
    fs::write(
        &temporary,
        serde_json::to_vec(&receipt).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    fs::rename(&temporary, &delivery).map_err(|e| e.to_string())?;
    Ok(json!({"hookSpecificOutput":{"hookEventName":kind,
        "additionalContext":context.chars().take(4000).collect::<String>()}}))
}

fn main() {
    let mut args: Vec<String> = std::env::args().skip(1).collect();
    let context_mode = args.first().is_some_and(|a| a == "--decision-context");
    let record_mode = args.first().is_some_and(|a| a == "--record-context");
    if context_mode || record_mode {
        args.remove(0);
    }
    if (record_mode && args.len() != 1) || (!record_mode && args.len() != 4) {
        eprintln!(
            "usage: workflow-codex-hook --record-context WORKSPACE\n       workflow-codex-hook [--decision-context] WORKSPACE SESSION_ID AGENT_ID RUN_DIRECTORY"
        );
        println!("{{}}");
        return;
    }
    let mut input = String::new();
    let event = io::stdin()
        .read_to_string(&mut input)
        .ok()
        .and_then(|_| serde_json::from_str::<Value>(&input).ok());
    let Some(event) = event else {
        eprintln!("Workflow adapter could not identify malformed native input; no decision issued");
        println!("{{}}");
        return;
    };
    if record_mode {
        let output = record_context(&event, &args[0]).unwrap_or_else(|reason| {
            eprintln!("Workflow owner-record context unavailable; coverage degraded: {reason}");
            json!({})
        });
        println!("{output}");
        return;
    }
    if context_mode {
        let output = decision_context(&event, &args).unwrap_or_else(|reason| {
            eprintln!("Workflow optional context unavailable; coverage degraded: {reason}");
            json!({})
        });
        println!("{output}");
        return;
    }
    let kind = event["hook_event_name"].as_str().unwrap_or("");
    if !["SubagentStart", "PreToolUse"].contains(&kind) || !scoped(&event, &args) {
        println!("{{}}");
        return;
    }
    let output = evaluate(&event,&args).unwrap_or_else(|reason| {
        if kind=="PreToolUse" { deny(reason) }
        else { json!({"systemMessage":format!("Workflow worker enrollment failed: {reason}. Return without tool use; the Coordinator must reconcile the binding.")}) }
    });
    println!("{output}");
}
