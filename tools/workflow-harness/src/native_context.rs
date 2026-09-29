//! Advisory current-work and dispatch evidence. No authority or semantic verdicts.
use serde_json::{Value, json};
use std::{fs, io::Write, path::Path};
use workflow_harness::Result;

pub fn fingerprint(bytes: &[u8]) -> String {
    let value = bytes.iter().fold(0xcbf29ce484222325u64, |hash, byte| {
        (hash ^ u64::from(*byte)).wrapping_mul(0x100000001b3)
    });
    format!("{value:016x}")
}

fn read(path: &Path) -> Result<Value> {
    serde_json::from_slice(&fs::read(path).map_err(|e| e.to_string())?).map_err(|e| e.to_string())
}

fn write_once(path: &Path, value: &Value) -> Result<()> {
    // Duplicate callbacks never replace the original invocation or response.
    let mut file = match fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
    {
        Ok(file) => file,
        Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => return Ok(()),
        Err(e) => return Err(e.to_string()),
    };
    file.write_all(value.to_string().as_bytes())
        .map_err(|e| e.to_string())?;
    file.sync_all().map_err(|e| e.to_string())
}

fn current(root: &Path, binding: &Value) -> bool {
    if !binding["selection"].is_object() {
        return false;
    }
    [&binding["selection"], &binding["work"]]
        .into_iter()
        .all(|reference| {
            if reference.is_null() {
                return true;
            }
            reference["path"]
                .as_str()
                .and_then(|p| fs::canonicalize(p).ok())
                .filter(|p| p.starts_with(root))
                .and_then(|p| fs::read(p).ok())
                .is_some_and(|raw| reference["fingerprint"].as_str() == Some(&fingerprint(&raw)))
        })
}

fn participating(tool: &str) -> bool {
    matches!(
        tool,
        "spawn_agent"
            | "followup_task"
            | "collaborationspawn_agent"
            | "collaborationfollowup_task"
            | "Agent"
            | "collaboration.spawn_agent"
            | "collaboration.followup_task"
    )
}

fn safe_id(id: &str) -> bool {
    !id.is_empty()
        && id.len() <= 200
        && id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"_-".contains(&b))
}

fn task_visibility(input: &Value) -> &'static str {
    match input
        .get("message")
        .or_else(|| input.get("prompt"))
        .and_then(Value::as_str)
    {
        Some(text) if !text.is_empty() && !text.starts_with("gAAAA") => "host_text",
        _ => "opaque_or_unavailable",
    }
}

fn explicit_failure(response: &Value) -> bool {
    response.get("isError").and_then(Value::as_bool) == Some(true)
        || response.get("success").and_then(Value::as_bool) == Some(false)
        || matches!(
            response.get("status").and_then(Value::as_str),
            Some(
                "failed"
                    | "cancelled"
                    | "canceled"
                    | "rejected"
                    | "error"
                    | "aborted"
                    | "timeout"
                    | "unavailable"
            )
        )
        || response.get("error").is_some_and(|v| !v.is_null())
}

fn response_outcome(event: &Value, input: &Value) -> (String, Value) {
    let original = &event["tool_response"];
    if explicit_failure(event) || explicit_failure(original) {
        return ("failed".into(), Value::Null);
    }
    // Decode only the observed JSON-string object envelope, once. The caller
    // bounds its serialized size and retains the original response unchanged.
    let decoded = original
        .as_str()
        .and_then(|text| serde_json::from_str::<Value>(text).ok())
        .filter(Value::is_object);
    let response = decoded.as_ref().unwrap_or(original);
    if explicit_failure(response) {
        return ("failed".into(), Value::Null);
    }
    // Recognize explicit structured handles only. Unknown envelopes stay uncertain.
    for key in ["agent_id", "task_name", "agent_task_id"] {
        if let Some(handle) = response
            .get(key)
            .and_then(Value::as_str)
            .filter(|s| !s.is_empty())
        {
            return ("confirmed_dispatch".into(), json!(handle));
        }
    }
    if response.get("status").and_then(Value::as_str) == Some("success")
        && let Some(target) = input.get("target").and_then(Value::as_str)
    {
        return ("confirmed_dispatch".into(), json!(target));
    }
    ("uncertain".into(), Value::Null)
}

pub fn observe(event: &Value, root: &Path, binding: &Value) -> Result<Value> {
    let kind = event["hook_event_name"].as_str().unwrap_or("");
    let id = event["session_id"].as_str().ok_or("missing session")?;
    let directory = root.join(".frontier/hook-context");
    let tool = event["tool_name"].as_str().unwrap_or("");
    let fresh = current(root, binding);
    let selected = &binding["current_state"];
    let mut context = if fresh {
        format!(
            "Current adopted Workflow work (data): selection {}; work {}; status {}; work status {}. Current scope: {}. Read the owner for the full commitment. For research, recover the whole-chain advantage hypothesis, its decisive prospective conditions, outstanding target feedback and remaining path, not just the latest step. At an investment change, apply learning-loop.md#prospective-reasoning and #whole-chain-investment-and-target-feedback: consider consequential external changes, intervention effects and opportunities without requiring a forecasting stage. Ordinary necessary development does not require a new review. A paused or completed record does not authorize resumption.",
            binding["selection"]["path"],
            binding["work"]["path"],
            selected["campaign_status"],
            binding["work_status"],
            selected["primary_work"]
        )
    } else {
        format!(
            "Workflow association is stale; do not treat its prior scope as current. Read the saved owner {} and refresh with frontier_references.py adopt-work. Ordinary authorized work is not blocked.",
            binding["selection"]["path"]
        )
    };
    if binding["current_use"].is_object() {
        let current_use = &binding["current_use"];
        context.push_str(&format!(
            " Known current-use correction references (data): {}; affected blocking references at capture: {}. Before affected dispatch or reuse, run frontier_references.py check-current-use against the current owner and actual task sources. Apply required corrections through that owner. This observer neither validates this saved report nor authorizes the action; an empty blocking list is not current clearance. Unrelated authorized work continues. Observation only.",
            current_use["correction_ids"], current_use["blocked_ids"]
        ));
    }
    context.push_str(" For a changed wait arrangement or idle return, use learning-loop.md#evaluation-implementation-and-continuation and the standalone check-continuation command on current adopted sources. This optional pointer does not validate pending observation sources. A local wait does not suspend all work; repeated observations do not reopen unchanged implementation. Inspect actual steering and final wording even when native capture is unavailable.");
    if participating(tool) && ["PreToolUse", "PostToolUse"].contains(&kind) {
        let call = event["tool_use_id"]
            .as_str()
            .filter(|s| safe_id(s))
            .ok_or("missing safe tool_use_id")?;
        let path = directory.join(format!("{id}-call-{call}.json"));
        if kind == "PreToolUse" {
            let input = &event["tool_input"];
            if !input.is_object() || input.to_string().len() > 262_144 {
                return Err("dispatch input unavailable or exceeds observation limit".into());
            }
            write_once(
                &path,
                &json!({"session_id":id,"tool_use_id":call,"tool_name":tool,
                "turn_id":event["turn_id"],"tool_input":input,"adopted_work":binding,
                "task_visibility":task_visibility(input),
                "association":if fresh {"current"} else {"stale"},"status":"attempted_dispatch",
                "observed_at_ms":workflow_harness::decision::now_ms()?}),
            )?;
            context.push_str(&format!(" Actual outgoing input is retained at {}. Compare that input with the selected whole mechanism, decisive prospective conditions and target-feedback arrangement at this existing handoff; equal IDs or an 'unchanged' report do not establish semantic fidelity. Correct a narrowed mechanism or an unsupported prerequisite postponing feedback in the actual affected task before further discretionary work; a stated intention is not an executed correction. No additional review is required. Observation only.", path.display()));
            if task_visibility(input) != "host_text" {
                context.push_str(" The host exposed an opaque or missing task body. This receipt does not capture readable assignment meaning; use the actual task in the conversation at the existing owner handoff. Do not claim semantic inspection of this payload or try to decode it.");
            }
        } else {
            let attempted = read(&path)?;
            if attempted["session_id"] != id
                || attempted["tool_use_id"] != call
                || attempted["tool_name"] != tool
                || attempted["tool_input"] != event["tool_input"]
            {
                return Err("post-call event does not match the retained actual invocation".into());
            }
            let response = &event["tool_response"];
            if response.to_string().len() > 262_144 {
                return Err("dispatch response exceeds observation limit".into());
            }
            let (status, handle) = response_outcome(event, &attempted["tool_input"]);
            let post = directory.join(format!("{id}-call-{call}-post.json"));
            write_once(
                &post,
                &json!({"session_id":id,"tool_use_id":call,"attempt":path,
                "tool_response":response,"status":status,"worker_handle":handle,
                "observed_at_ms":workflow_harness::decision::now_ms()?}),
            )?;
            let retained = read(&post)?;
            let status = retained["status"].as_str().unwrap_or("uncertain");
            return Ok(
                json!({"hookSpecificOutput":{"hookEventName":kind,"additionalContext":format!(
                "Workflow dispatch response retained at {}. Status: {status}. This is not worker completion or semantic acceptance. At the existing return, associate the actual result with call {call} and its original work in {}. Reconcile failed or uncertain responses before any repeat; do not infer authority to redispatch.", post.display(), path.display())}}),
            );
        }
    } else if kind == "PostToolUse" {
        return Ok(json!({}));
    }
    // Deduplicate context delivery, never actual dispatch observations.
    let fingerprint = fingerprint(context.as_bytes());
    let delivery = directory.join(format!("{id}-{kind}-delivery.json"));
    if kind == "PreToolUse"
        && !participating(tool)
        && read(&delivery)
            .ok()
            .is_some_and(|v| v["fingerprint"] == fingerprint)
    {
        return Ok(json!({}));
    }
    let receipt = json!({"session_id":id,"kind":"adopted_work","mode":"observe",
        "association":if fresh {"current"} else {"stale"},"fingerprint":fingerprint,
        "tool_use_id":event["tool_use_id"],"tool_name":event["tool_name"],"hook_event_name":kind});
    let temporary = directory.join(format!("{id}-{kind}-{}.tmp", std::process::id()));
    fs::write(&temporary, receipt.to_string()).map_err(|e| e.to_string())?;
    fs::rename(temporary, delivery).map_err(|e| e.to_string())?;
    Ok(json!({"hookSpecificOutput":{"hookEventName":kind,
        "additionalContext":context.chars().take(4000).collect::<String>()}}))
}
