//! Line-based controlled Agent transport. The configured backend provides model
//! inference and native tools; this module only controls invocation/continuation.

use crate::control::{Adapter, Cancellation, Capabilities, Continuation, Message, Recovery};
use crate::session::ProcessAdapter;
use crate::{Invocation, Result};
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};

pub struct StreamAdapter {
    process: ProcessAdapter,
    capabilities: Capabilities,
    directory: PathBuf,
    workspace: PathBuf,
    invocation_id: Option<usize>,
    child: Option<Child>,
    input: Option<ChildStdin>,
    output: Option<BufReader<ChildStdout>>,
    trace: Option<File>,
    effects_settled: bool,
}

impl StreamAdapter {
    pub fn new(
        process: ProcessAdapter,
        capabilities: Capabilities,
        directory: &Path,
        workspace: &Path,
    ) -> Self {
        Self {
            process,
            capabilities,
            directory: directory.to_path_buf(),
            invocation_id: None,
            workspace: workspace.to_path_buf(),
            child: None,
            input: None,
            output: None,
            trace: None,
            effects_settled: false,
        }
    }

    fn send(&mut self, value: &impl serde::Serialize) -> Result<()> {
        let input = self.input.as_mut().ok_or("no live backend input")?;
        serde_json::to_writer(&mut *input, value).map_err(|e| e.to_string())?;
        input
            .write_all(b"\n")
            .and_then(|_| input.flush())
            .map_err(|e| e.to_string())
    }
}

impl Adapter for StreamAdapter {
    fn capabilities(&self) -> Capabilities {
        self.capabilities.clone()
    }

    fn invoke(&mut self, invocation: &Invocation) -> Result<()> {
        if self.invocation_id.is_some() {
            return Err("stream adapter cannot redispatch".into());
        }
        if !self.process.program.is_absolute() || !self.process.program.is_file() {
            return Err("adapter executable must be an existing absolute file".into());
        }
        // Exclusive creation means a failed spawn is still reconciled, not retried.
        fs::create_dir(&self.directory).map_err(|e| e.to_string())?;
        let stderr = File::create(self.directory.join("stderr.txt")).map_err(|e| e.to_string())?;
        let trace = File::create(self.directory.join("events.jsonl")).map_err(|e| e.to_string())?;
        self.invocation_id = Some(invocation.invocation_id);
        let mut child = Command::new(&self.process.program)
            .args(&self.process.args)
            .current_dir(&self.workspace)
            .env("WORKFLOW_INVOCATION_DIRECTORY", &self.directory)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(stderr)
            .spawn()
            .map_err(|e| e.to_string())?;
        self.input = child.stdin.take();
        self.output = child.stdout.take().map(BufReader::new);
        self.trace = Some(trace);
        self.child = Some(child);
        self.send(&serde_json::json!({"message":"invoke","invocation":invocation}))
    }

    fn next(&mut self) -> Result<Message> {
        let mut line = String::new();
        if self
            .output
            .as_mut()
            .ok_or("backend was not invoked")?
            .read_line(&mut line)
            .map_err(|e| e.to_string())?
            == 0
        {
            return Err(
                "backend disconnected; execution remains unknown and is not replayed".into(),
            );
        }
        let trace = self.trace.as_mut().unwrap();
        trace
            .write_all(line.as_bytes())
            .and_then(|_| trace.sync_all())
            .map_err(|e| e.to_string())?;
        let message: Message =
            serde_json::from_str(&line).map_err(|e| format!("invalid backend event: {e}"))?;
        match &message {
            Message::Event { event } => {
                if let crate::control::EventKind::Stopped { effects_settled } = event.event {
                    self.effects_settled = effects_settled;
                }
            }
            Message::Return { response } => {
                // End input and require terminal process evidence before adoption.
                self.input.take();
                let status = self
                    .child
                    .as_mut()
                    .unwrap()
                    .wait()
                    .map_err(|e| e.to_string())?;
                if !status.success() {
                    return Err("backend exited unsuccessfully; reconcile partial results".into());
                }
                let receipt = Recovery::Terminal {
                    response: response.clone(),
                    effects_settled: self.effects_settled,
                };
                let mut file = OpenOptions::new()
                    .write(true)
                    .create_new(true)
                    .open(self.directory.join("terminal.json"))
                    .map_err(|e| e.to_string())?;
                serde_json::to_writer(&mut file, &receipt).map_err(|e| e.to_string())?;
                file.sync_all().map_err(|e| e.to_string())?;
            }
        }
        Ok(message)
    }

    fn continue_work(&mut self, decision: &Continuation) -> Result<()> {
        self.send(&serde_json::json!({"message":"continuation","invocation_id":self.invocation_id,"decision":decision}))
    }

    fn cancel(&mut self, invocation_id: usize) -> Result<Cancellation> {
        if !self.capabilities.cooperative_cancel {
            return Ok(Cancellation::Unsupported);
        }
        if self.invocation_id != Some(invocation_id) {
            return Err("wrong cancellation invocation".into());
        }
        self.send(&serde_json::json!({"message":"cancel","invocation_id":invocation_id}))?;
        // Sending is not confirmation and never kills a native operation.
        Ok(Cancellation::Pending)
    }

    fn recover(&mut self, invocation_id: usize) -> Result<Recovery> {
        if !self.capabilities.recovery {
            return Ok(Recovery::Unsupported);
        }
        let receipt = self.directory.join("terminal.json");
        if receipt.exists() {
            let recovered: Recovery =
                serde_json::from_slice(&fs::read(receipt).map_err(|e| e.to_string())?)
                    .map_err(|e| e.to_string())?;
            if let Recovery::Terminal { response, .. } = &recovered
                && response.invocation_id != invocation_id
            {
                return Err("wrong recovered invocation".into());
            }
            return Ok(recovered);
        }
        if self.invocation_id == Some(invocation_id)
            && self
                .child
                .as_mut()
                .is_some_and(|child| matches!(child.try_wait(), Ok(None)))
        {
            return Ok(Recovery::Running);
        }
        Ok(Recovery::Unknown)
    }
}
