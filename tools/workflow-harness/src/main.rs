use std::fs;
use std::io::{self, BufRead, Write};
use std::path::{Path, PathBuf};
use workflow_harness::control::{Capabilities, Recovery};
use workflow_harness::session::{ProcessAdapter, Session};
use workflow_harness::stream::StreamAdapter;
use workflow_harness::{Response, Task};

#[derive(serde::Deserialize)]
#[serde(deny_unknown_fields)]
struct StreamConfig {
    process: ProcessAdapter,
    capabilities: Capabilities,
}

fn stream_backend(session: &Session, config: &StreamConfig) -> Result<StreamAdapter, String> {
    let id = session
        .runtime
        .outstanding()
        .ok_or("no pending invocation")?
        .invocation_id;
    Ok(StreamAdapter::new(
        config.process.clone(),
        config.capabilities.clone(),
        &session.directory().join(format!("stream-{id}")),
        session.runtime.workspace(),
    ))
}

mod host;

fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}

fn read_json<T: serde::de::DeserializeOwned>(path: &Path) -> Result<T, String> {
    serde_json::from_slice(&fs::read(path).map_err(|e| e.to_string())?)
        .map_err(|e| format!("{}: {e}", path.display()))
}

fn emit(value: &impl serde::Serialize) -> Result<(), String> {
    println!(
        "{}",
        serde_json::to_string(value).map_err(|e| e.to_string())?
    );
    io::stdout().flush().map_err(|e| e.to_string())
}

fn run() -> Result<(), String> {
    if std::env::args_os().nth(1).as_deref() == Some(std::ffi::OsStr::new("host")) {
        return host::run();
    }
    let mut args = std::env::args_os().skip(1);
    let mut positional = vec![];
    let mut resume = false;
    let mut adapter_path = None;
    let mut response_path = None;
    let mut stream_path = None;
    while let Some(arg) = args.next() {
        if arg == "--resume" {
            resume = true;
        } else if arg == "--adapter" {
            adapter_path = Some(PathBuf::from(args.next().ok_or("--adapter needs a file")?));
        } else if arg == "--response" {
            response_path = Some(PathBuf::from(args.next().ok_or("--response needs a file")?));
        } else if arg == "--stream-adapter" {
            stream_path = Some(PathBuf::from(
                args.next().ok_or("--stream-adapter needs a file")?,
            ));
        } else if arg.to_string_lossy().starts_with("--") {
            return Err(format!("unknown option: {}", arg.to_string_lossy()));
        } else {
            positional.push(PathBuf::from(arg));
        }
    }
    if positional.len() != if resume { 1 } else { 2 } || (!resume && response_path.is_some()) {
        return Err("usage: workflow-harness TASK.json NEW_RUN_DIRECTORY [--adapter CONFIG.json | --stream-adapter CONFIG.json]\n       workflow-harness --resume RUN_DIRECTORY [--response VERIFIED_RETURN.json] [--adapter CONFIG.json | --stream-adapter CONFIG.json]\nThe legacy --adapter transport accepts protocol version 1 only. A stream resume reconciles a terminal receipt; it never repeats an unresolved invocation.".into());
    }
    let adapter: Option<ProcessAdapter> = adapter_path.as_deref().map(read_json).transpose()?;
    let stream: Option<StreamConfig> = stream_path.as_deref().map(read_json).transpose()?;
    if stream.is_some() && adapter.is_some() {
        return Err("select only one adapter transport".into());
    }
    let mut session = if resume {
        Session::open(&positional[0])?
    } else {
        Session::create(read_json::<Task>(&positional[0])?, &positional[1])?
    };
    if resume {
        if session.runtime.outstanding().is_some() {
            if let Some(config) = &stream {
                if response_path.is_some() {
                    return Err(
                        "reconcile the controlled backend before using a corrected return".into(),
                    );
                }
                let mut backend = stream_backend(&session, config)?;
                if !matches!(
                    session.recover_backend(&mut backend)?,
                    Recovery::Terminal { .. }
                ) {
                    return Err("controlled backend is not terminal; no dispatch or continuation was repeated".into());
                }
            } else {
                let response = if let Some(path) = &response_path {
                    read_json::<Response>(path)?
                } else {
                    // Collect only a terminal return saved by the previous process.
                    // No receipt means unknown, even when no child appears to be running.
                    session.collected_response()?
                };
                session.accept(response)?;
            }
        } else if response_path.is_some() {
            return Err(
                "no pending invocation; an already accepted result cannot be adopted twice".into(),
            );
        }
        session.recover_for_adoption()?;
    }
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    loop {
        if let Some(outcome) = session.runtime.terminal() {
            emit(&serde_json::json!({"event":"pilot_terminal","outcome":outcome}))?;
            return Ok(());
        }
        let request = session.request()?;
        emit(&request)?;
        if let Some(config) = &stream {
            let mut backend = stream_backend(&session, config)?;
            session.drive(&mut backend)?;
            continue;
        }
        if let Some(adapter) = &adapter {
            let response = session.invoke(adapter)?;
            session.accept(response)?;
            continue;
        }
        loop {
            let line = lines.next().ok_or("transport disconnected with an unresolved invocation; reconcile the run before resuming")?
                .map_err(|e| e.to_string())?;
            let result = serde_json::from_str::<Response>(&line)
                .map_err(|e| e.to_string())
                .and_then(|response| {
                    session.runtime.clone().accept(response.clone())?;
                    Ok(response)
                });
            match result {
                Err(error) => {
                    emit(&serde_json::json!({"event":"response_rejected","error":error}))?
                }
                Ok(response) => {
                    // Persistence failures terminate instead of inviting duplicate adoption.
                    session.accept(response)?;
                    break;
                }
            }
        }
    }
}
