//! Request/return bridge for Agent tools already available in the current host.
//! Each command exits immediately; model work stays with the existing host.

use crate::{StreamConfig, emit, read_json, stream_backend};
use serde::Deserialize;
use std::io::{self, Read};
use std::path::PathBuf;
use workflow_harness::control::{Capabilities, Event};
use workflow_harness::session::{HostBinding, Session};
use workflow_harness::{Response, Result, Task};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct HostReturn {
    backend_handle: String,
    response: Response,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct HostEvent {
    backend_handle: String,
    event: Event,
}

fn input<T: serde::de::DeserializeOwned>() -> Result<T> {
    let mut text = String::new();
    io::stdin()
        .read_to_string(&mut text)
        .map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

fn next(session: &mut Session) -> Result<()> {
    session.expire_decision()?;
    if session.decisions.holds() {
        return emit(
            &serde_json::json!({"event":"decision_pending", "decisions":session.decisions.status(),
            "instruction":"Use the normal host for one correlated check; this command releases the run lock on exit. Publish through the existing owner before dispatch."}),
        );
    }
    if let Some(outcome) = session.runtime.terminal() {
        emit(&serde_json::json!({"event":"pilot_terminal","outcome":outcome}))
    } else {
        let invocation = session.request()?;
        if session
            .decisions
            .pending
            .as_ref()
            .is_some_and(|p| p.observed_only)
        {
            emit(
                &serde_json::json!({"event":"invocation_with_observation","invocation":invocation,"check":session.decisions.pending}),
            )
        } else {
            emit(&invocation)
        }
    }
}

pub fn run() -> Result<()> {
    let args: Vec<_> = std::env::args_os().skip(2).collect();
    let Some(command) = args.first().and_then(|s| s.to_str()) else {
        return Err("host command required".into());
    };
    if command == "context-read" && args.len() == 4 {
        return emit(&Session::read_saved_context(
            &PathBuf::from(&args[1]),
            args[2].to_str().ok_or("invalid evidence identity")?,
            args[3].to_str().ok_or("invalid evidence pointer")?,
        )?);
    }
    if command == "start" && args.len() == 3 {
        let task: Task = read_json(&PathBuf::from(&args[1]))?;
        return next(&mut Session::create(task, &PathBuf::from(&args[2]))?);
    }
    if [
        "current-use-adopt",
        "current-use-replace",
        "current-use-check",
        "context-check",
    ]
    .contains(&command)
        && (args.len() == 3 || (command == "current-use-replace" && args.len() > 3))
    {
        let mut session = Session::open(&PathBuf::from(&args[1]))?;
        let path = PathBuf::from(&args[2]);
        return match command {
            "current-use-adopt" => {
                let report: serde_json::Value = read_json(&path)?;
                let snapshot = report.get("current_use").unwrap_or(&report).clone();
                let binding = serde_json::from_value(snapshot).map_err(|e| e.to_string())?;
                session.adopt_current_use(binding)?;
                emit(&serde_json::json!({"event":"current_use_adopted",
                    "instruction":"Owner validation remains with the producing checker; verify the actual queued request before dispatch."}))
            }
            "current-use-replace" => {
                let assignment = std::fs::read_to_string(path).map_err(|e| e.to_string())?;
                let request = if args.len() > 3 {
                    session.replace_queued_work_for(
                        assignment,
                        args[3..].iter().map(PathBuf::from).collect(),
                    )?
                } else {
                    session.replace_queued_work(assignment)?
                };
                emit(&request)
            }
            "current-use-check" | "context-check" => {
                let request = read_json(&path)?;
                if command == "context-check" {
                    session.verify_queued_context(&request)?;
                } else {
                    session.verify_queued_current_use(&request)?;
                }
                emit(&serde_json::json!({"event":format!("{command}_verified"),
                    "invocation_id":request.invocation_id,
                    "instruction":"Saved bytes and request identity match now; this is not semantic acceptance or protection against later concurrent edits."}))
            }
            _ => unreachable!(),
        };
    }
    if args.len() != 2
        || ![
            "bind",
            "return",
            "status",
            "continue",
            "begin",
            "event",
            "continuation",
            "pause",
            "resume",
            "drive",
            "next",
            "decision-config",
            "decision-bind",
            "decision-result",
            "decision-resolve",
            "decision-publish",
            "decision-abandon",
            "decision-status",
        ]
        .contains(&command)
    {
        return Err("usage: workflow-harness host start TASK.json NEW_RUN_DIRECTORY\n       workflow-harness host bind|return|status|continue|begin|event|continuation|pause|resume|drive RUN_DIRECTORY\nOptional decisions: decision-config|decision-bind|decision-result|decision-resolve|decision-publish|decision-abandon|decision-status|next RUN_DIRECTORY. Current use: current-use-adopt RUN_DIRECTORY REPORT.json | current-use-replace RUN_DIRECTORY ASSIGNMENT.txt [ACTUAL_SOURCE ...] | current-use-check RUN_DIRECTORY REQUEST.json. Other commands with input read JSON from stdin; status never redispatches work. drive executes only the pending invocation using a stream adapter configuration.".into());
    }
    if command == "pause" {
        Session::request_pause(&PathBuf::from(&args[1]), input::<String>()?)?;
        return emit(
            &serde_json::json!({"event":"pause_requested","new_work":"withheld at the next controlled boundary; existing effects are not killed"}),
        );
    }
    let mut session = Session::open(&PathBuf::from(&args[1]))?;
    match command {
        "next" => next(&mut session),
        "decision-config" => {
            session.configure_decisions(input()?)?;
            emit(
                &serde_json::json!({"event":"decision_configured","config":session.decisions.config}),
            )
        }
        "decision-bind" => {
            #[derive(Deserialize)]
            #[serde(deny_unknown_fields)]
            struct Binding {
                check_id: u64,
                backend_handle: String,
            }
            let binding: Binding = input()?;
            session.bind_decision(binding.check_id, binding.backend_handle)?;
            emit(&serde_json::json!({"event":"decision_bound"}))
        }
        "decision-result" => {
            session.decision_result(input()?)?;
            emit(
                &serde_json::json!({"event":"decision_result_consumed","decisions":session.decisions.status()}),
            )
        }
        "decision-resolve" => {
            session.resolve_decision(input()?)?;
            emit(
                &serde_json::json!({"event":"decision_owner_disposition_consumed","decisions":session.decisions.status()}),
            )
        }
        "decision-publish" => {
            session.confirm_publication(input()?)?;
            next(&mut session)
        }
        "decision-abandon" => {
            session.abandon_decision(input()?)?;
            emit(
                &serde_json::json!({"event":"stale_proposal_returned","decisions":session.decisions.status()}),
            )
        }
        "decision-status" => {
            session.expire_decision()?;
            emit(
                &serde_json::json!({"event":"decision_status","decisions":session.decisions.status(),
                "instruction":"Status never dispatches. A bound or uncertain checker must not be invoked again. After release use host next, not a new Coordinator invocation."}),
            )
        }
        "drive" => {
            let config: StreamConfig = input()?;
            let mut backend = stream_backend(&session, &config)?;
            session.drive(&mut backend)?;
            next(&mut session)
        }
        "begin" => {
            session.begin_execution(input::<Capabilities>()?)?;
            emit(&serde_json::json!({"event":"execution_registered"}))
        }
        "event" => {
            let value: HostEvent = input()?;
            let binding = session.host_binding()?.ok_or("no host binding")?;
            if binding.backend_handle != value.backend_handle
                || binding.invocation_id != value.event.invocation_id
            {
                return Err("event does not match host binding".into());
            }
            emit(&serde_json::json!({"accepted":session.event(value.event)?}))
        }
        "continuation" => {
            let handle: String = input()?;
            if session
                .host_binding()?
                .is_none_or(|binding| binding.backend_handle != handle)
            {
                return Err("continuation does not match host binding".into());
            }
            emit(&session.continuation()?)
        }
        "resume" => {
            session.unpause()?;
            next(&mut session)
        }
        "bind" => {
            let binding: HostBinding = input()?;
            session.bind_host(binding.clone())?;
            emit(&serde_json::json!({"event":"host_bound","binding":binding}))
        }
        "return" => {
            let result: HostReturn = input()?;
            session.accept_host_return(&result.backend_handle, result.response)?;
            next(&mut session)
        }
        "status" => emit(&serde_json::json!({
            "pending":session.runtime.outstanding(),"binding":session.host_binding()?,
            "terminal":session.runtime.terminal(),
            "execution":session.runtime.execution(),
            "cumulative_usage":session.runtime.cumulative_usage()?,
            "execution_status":"Inspect the recorded host handle; pending does not mean not started. This command does not dispatch."
        })),
        "continue" => {
            session.recover_for_adoption()?;
            next(&mut session)
        }
        _ => unreachable!(),
    }
}
