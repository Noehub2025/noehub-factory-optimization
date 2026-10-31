//! Host-owned command admission for one existing Session. This is not a sandbox.
//! Backend requests arrive on a pipe bound by the host to one invocation; a model
//! cannot select another invocation or publish a correction through that pipe.
use super::*;
use std::collections::BTreeMap;
use std::io::{BufRead, BufReader};
use std::sync::mpsc;
use std::time::Duration;

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct ManagedCommand {
    pub program: PathBuf,
    #[serde(default)]
    pub args: Vec<String>,
}

#[derive(Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ManagedCorrection {
    pub correction_id: String,
    pub expected_invocation: usize,
    pub replacement: QueuedWorkCorrection,
}

#[derive(Clone, Default, Deserialize, Serialize)]
pub(super) struct State {
    invocations: BTreeMap<usize, InvocationState>,
    corrections: BTreeMap<String, (String, usize)>,
}

#[derive(Clone, Deserialize, Serialize)]
struct InvocationState {
    // prepared -> installing -> ready -> completed, or retired by publication.
    phase: String,
    actions: BTreeMap<String, Action>,
}

#[derive(Clone, Deserialize, Serialize)]
struct Action {
    command: ManagedCommand,
    // An intent without an outcome is uncertain, never permission to replay.
    outcome: Option<i32>,
    not_started: bool,
    stdout: PathBuf,
    stderr: PathBuf,
}

impl State {
    fn unsettled(&self) -> bool {
        self.invocations.values().any(|i| {
            i.actions
                .values()
                .any(|a| a.outcome.is_none() && !a.not_started)
        })
    }
}

fn key(value: &str) -> Result<()> {
    if value.is_empty()
        || value.len() > 128
        || !value
            .bytes()
            .all(|c| c.is_ascii_alphanumeric() || b"-_".contains(&c))
    {
        return Err(
            "use a nonempty action/correction key containing letters, digits, '-' or '_'".into(),
        );
    }
    Ok(())
}

impl Session {
    pub(super) fn require_unmanaged_transport(&self) -> Result<()> {
        if self
            .runtime
            .outstanding()
            .is_some_and(|r| self.managed.invocations.contains_key(&r.invocation_id))
        {
            return Err("invocation belongs to the managed host; do not change transports or accept an unbound return".into());
        }
        Ok(())
    }

    /// Managed hosts hold this lock only during admission/publication, never while
    /// waiting for model or command completion. Transient contention is normal.
    pub fn open_managed(directory: &Path) -> Result<Self> {
        loop {
            match Self::open(directory) {
                Err(e) if e == "another harness may own this run" => {
                    std::thread::sleep(Duration::from_millis(5))
                }
                result => return result,
            }
        }
    }

    fn managed_current(&self, id: usize) -> Result<()> {
        if self.runtime.outstanding().map(|r| r.invocation_id) != Some(id)
            || self
                .managed
                .invocations
                .get(&id)
                .is_some_and(|i| i.phase == "retired")
        {
            return Err(
                "superseded invocation; no new action or current return is admitted".into(),
            );
        }
        self.observe_managed_sources()
    }

    fn observe_managed_sources(&self) -> Result<()> {
        self.verify_current_use_consumption()?;
        self.runtime.verify_context_consumption()
    }

    /// Claim a host installation once. An uncertain previous installation cannot
    /// be restarted merely because its original driver stopped responding.
    fn managed_install(&mut self) -> Result<Invocation> {
        self.reconcile_managed_receipts()?;
        if self.managed.unsettled() {
            return Err(
                "admitted effects remain unresolved; reconcile their original receipts".into(),
            );
        }
        let request = self.runtime.outstanding().ok_or("no queued work")?.clone();
        self.managed_current(request.invocation_id)?;
        if self.runtime.execution().is_some()
            || self.host_dispatch().is_some()
            || self.host_binding()?.is_some()
        {
            return Err(
                "invocation already has another transport; reconcile it before changing hosts"
                    .into(),
            );
        }
        let item = self
            .managed
            .invocations
            .entry(request.invocation_id)
            .or_insert(InvocationState {
                phase: "prepared".into(),
                actions: BTreeMap::new(),
            });
        if item.phase != "prepared" {
            return Err(
                "managed installation already attempted; do not replay an uncertain host call"
                    .into(),
            );
        }
        item.phase = "installing".into();
        self.runtime.begin_execution(Capabilities {
            events: true,
            controlled_continuation: true,
            fresh_context: true,
            isolation: "Host-owned pipe actions in this Session; no out-of-pipe effects".into(),
            ..Default::default()
        })?;
        self.runtime.execution_mut()?.dispatch_intent = true;
        self.persist(&self.runtime)?;
        Ok(request)
    }

    fn managed_installed(&mut self, id: usize) -> Result<()> {
        self.managed_current(id)?;
        let item = self
            .managed
            .invocations
            .get_mut(&id)
            .ok_or("unknown managed invocation")?;
        if item.phase != "installing" {
            return Err("invalid installation transition".into());
        }
        item.phase = "ready".into();
        self.runtime.execution_mut()?.start_confirmed = true;
        self.persist(&self.runtime)
    }

    /// The caller is the trusted host holding the pipe identity, not a model-
    /// supplied version. Launch occurs under the same Session lock as correction.
    fn managed_start(
        &mut self,
        id: usize,
        action_id: &str,
        command: ManagedCommand,
    ) -> Result<std::process::Child> {
        key(action_id)?;
        self.observe_pause()?;
        if self.runtime.paused.is_some() {
            return Err("run is paused".into());
        }
        self.managed_current(id)?;
        if self.decisions.holds() {
            return Err("owner decision is pending".into());
        }
        if let Continuation::Return { reasons } = self.check_action()? {
            return Err(format!(
                "return required before further work: {}",
                reasons.join("; ")
            ));
        }
        let item = self
            .managed
            .invocations
            .get(&id)
            .ok_or("no installed managed context")?;
        if item.phase != "ready" {
            return Err("managed context is not active".into());
        }
        if item.actions.contains_key(action_id) {
            return Err(
                "action already admitted; inspect its receipt, never replay its key".into(),
            );
        }
        if !command.program.is_absolute() || !command.program.is_file() {
            return Err("managed action requires an existing absolute executable".into());
        }
        let stdout = self
            .directory
            .join(format!("action-{id}-{action_id}.stdout"));
        let stderr = self
            .directory
            .join(format!("action-{id}-{action_id}.stderr"));
        let output = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(&stdout)
            .map_err(|e| e.to_string())?;
        let error = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(&stderr)
            .map_err(|e| e.to_string())?;
        self.managed
            .invocations
            .get_mut(&id)
            .unwrap()
            .actions
            .insert(
                action_id.into(),
                Action {
                    command: command.clone(),
                    outcome: None,
                    not_started: false,
                    stdout,
                    stderr,
                },
            );
        self.persist(&self.runtime)?;
        match Command::new(&command.program)
            .args(&command.args)
            .current_dir(self.runtime.workspace())
            .stdout(output)
            .stderr(error)
            .stdin(Stdio::null())
            .spawn()
        {
            Ok(child) => Ok(child),
            Err(error) => {
                self.managed
                    .invocations
                    .get_mut(&id)
                    .unwrap()
                    .actions
                    .get_mut(action_id)
                    .unwrap()
                    .not_started = true;
                self.persist(&self.runtime)?;
                Err(format!("action did not start: {error}"))
            }
        }
    }

    fn managed_settle(
        &mut self,
        id: usize,
        action_id: &str,
        outcome: i32,
    ) -> Result<serde_json::Value> {
        let action = self
            .managed
            .invocations
            .get_mut(&id)
            .and_then(|i| i.actions.get_mut(action_id))
            .ok_or("unknown admitted action")?;
        if action.outcome.is_some() || action.not_started {
            return Err("action already settled".into());
        }
        action.outcome = Some(outcome);
        let receipt = serde_json::json!({"kind":"action_result", "invocation_id":id, "action_id":action_id,
            "exit_code":outcome, "stdout":action.stdout, "stderr":action.stderr});
        self.persist(&self.runtime)?;
        Ok(receipt)
    }

    pub fn reconcile_managed_receipts(&mut self) -> Result<()> {
        let mut found = Vec::new();
        for (id, invocation) in &self.managed.invocations {
            for (key, action) in &invocation.actions {
                if action.outcome.is_some() || action.not_started {
                    continue;
                }
                let path = self
                    .directory
                    .join(format!("action-{id}-{key}.receipt.json"));
                if !path.exists() {
                    continue;
                }
                let receipt: Receipt =
                    serde_json::from_slice(&fs::read(path).map_err(|e| e.to_string())?)
                        .map_err(|e| e.to_string())?;
                if receipt.invocation_id != *id
                    || receipt.action_id != *key
                    || receipt.command != action.command
                {
                    return Err(
                        "completion receipt differs from its original admitted action".into(),
                    );
                }
                found.push((*id, key.clone(), receipt.exit_code));
            }
        }
        for (id, key, outcome) in found {
            self.managed_settle(id, &key, outcome)?;
        }
        Ok(())
    }

    fn managed_stopped(&mut self, id: usize) -> Result<()> {
        let settled = self.managed.invocations.get(&id).is_some_and(|i| {
            i.actions
                .values()
                .all(|a| a.outcome.is_some() || a.not_started)
        });
        let execution = self
            .runtime
            .executions
            .iter_mut()
            .find(|e| e.invocation_id == id)
            .ok_or("missing managed execution")?;
        if !execution.stopped {
            execution.event(Event {
                invocation_id: id,
                sequence: execution.events.len() as u64 + 1,
                event: EventKind::Stopped {
                    effects_settled: settled,
                },
            })?;
        }
        self.persist(&self.runtime)
    }

    pub(super) fn has_prepared_managed_correction(&self) -> bool {
        let Some(request) = self.runtime.outstanding() else {
            return false;
        };
        self.runtime.execution().is_none()
            && self
                .managed
                .corrections
                .values()
                .any(|(_, id)| *id == request.invocation_id)
            && self
                .managed
                .invocations
                .get(&request.invocation_id)
                .is_some_and(|item| item.phase == "prepared" && item.actions.is_empty())
    }

    /// Publish once under the action-admission lock. The existing renderer builds
    /// the full successor request. Prior effects and retired returns stay evidence.
    pub fn correct_managed_work_with_use(
        &mut self,
        correction: ManagedCorrection,
        binding: crate::current_use::CurrentUse,
    ) -> Result<Invocation> {
        self.correct_managed_work_with_binding(correction, Some(binding))
    }

    /// Source publication happened separately; this checkpoint is activation.
    pub fn correct_managed_work(&mut self, correction: ManagedCorrection) -> Result<Invocation> {
        self.correct_managed_work_with_binding(correction, None)
    }

    fn correct_managed_work_with_binding(
        &mut self,
        correction: ManagedCorrection,
        binding: Option<crate::current_use::CurrentUse>,
    ) -> Result<Invocation> {
        key(&correction.correction_id)?;
        let body = serde_json::to_string(&correction).map_err(|e| e.to_string())?;
        if let Some((saved, id)) = self.managed.corrections.get(&correction.correction_id) {
            if saved != &body {
                return Err("correction key reused for a different replacement".into());
            }
            return serde_json::from_slice(
                &fs::read(self.directory.join(format!("request-{id}.json")))
                    .map_err(|e| e.to_string())?,
            )
            .map_err(|e| e.to_string());
        }
        // Pause observation and decision expiry can themselves checkpoint. Run
        // them before changing the binding or retiring any invocation.
        self.observe_request_controls()?;
        let old = self.runtime.outstanding().ok_or("no active work")?.clone();
        if old.invocation_id != correction.expected_invocation {
            return Err("correction refers to another invocation".into());
        }
        if !self.managed.invocations.contains_key(&old.invocation_id) {
            return Err(
                "active invocation is outside managed coverage; do not assume it retired".into(),
            );
        }
        let change = correction.replacement;
        crate::contract::nonempty(&change.assignment, "corrected assignment")?;
        if let Some(objective) = &change.objective {
            crate::contract::nonempty(objective, "corrected objective")?;
        }
        let actual_use = change
            .actual_use
            .unwrap_or_else(|| self.runtime.actual_use.clone());
        let actual_use: Vec<_> = crate::current_use::normalized_sources(&actual_use)?
            .into_iter()
            .collect();
        let root = fs::canonicalize(self.runtime.workspace()).map_err(|e| e.to_string())?;
        if actual_use.iter().any(|path| !path.starts_with(&root)) {
            return Err("actual-use source is outside the workspace".into());
        }
        if let Some(binding) = &binding {
            binding.require_ready_for(&actual_use)?;
            if let Some(previous) = &self.current_use.adopted {
                binding.carries(previous)?;
            }
        } else {
            self.require_current_use_ready_for(&actual_use)?;
        }
        let sources = crate::source_contents(&self.runtime.task)?;
        let before = fs::read(self.directory.join("state.json")).map_err(|e| e.to_string())?;
        let old_runtime = self.runtime.clone();
        let old_managed = self.managed.clone();
        let old_use = self.current_use.clone();
        let old_decisions = self.decisions.clone();
        let successor_id = self
            .runtime
            .next_id
            .checked_add(1)
            .ok_or("invocation id overflow")?;
        if let Some(binding) = binding {
            self.current_use.adopted = Some(binding);
        }
        if let Some(v) = change.objective {
            self.runtime.task.objective = v;
        }
        if let Some(v) = change.constraints {
            self.runtime.task.constraints = v;
        }
        self.runtime.assignment = change.assignment;
        self.runtime.actual_use = actual_use;
        self.runtime.selected_sources = sources;
        self.runtime.outstanding = None;
        self.runtime.next_id = successor_id;
        // Let the existing owner adopt changed governing meaning; do not bypass
        // enforced investment correspondence or manufacture a Worker result.
        self.runtime.role = Role::Coordinator;
        self.runtime.context_notice = format!(
            "The owner published correction {}. This current task replaces the retired invocation {}. Its unfinished actions and any later returns remain evidence in {}/state.json under managed, not current instructions. Reuse completed effects; do not repeat them. Adopt the replacement through the existing owner before further dependent work.",
            correction.correction_id,
            old.invocation_id,
            self.directory.display()
        );
        self.managed
            .invocations
            .get_mut(&old.invocation_id)
            .unwrap()
            .phase = "retired".into();
        self.current_use.queued = None;
        self.managed.invocations.insert(
            successor_id,
            InvocationState {
                phase: "prepared".into(),
                actions: BTreeMap::new(),
            },
        );
        self.managed
            .corrections
            .insert(correction.correction_id, (body, self.runtime.next_id));
        // No control transition may persist this partially staged replacement.
        // Render the complete successor while retaining an observed pause. The
        // final checkpoint publishes its request, binding and retirement together.
        let result = self.render_request(true);
        if result.is_err()
            && fs::read(self.directory.join("state.json")).ok().as_ref() == Some(&before)
        {
            self.runtime = old_runtime;
            self.managed = old_managed;
            self.current_use = old_use;
            self.decisions = old_decisions;
        }
        result
    }
}

#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
enum Request {
    Event {
        event: EventKind,
    },
    Action {
        action_id: String,
        command: ManagedCommand,
        #[serde(default)]
        invocation_id: Option<usize>,
    },
    Return {
        response: Response,
    },
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Receipt {
    invocation_id: usize,
    action_id: String,
    command: ManagedCommand,
    exit_code: i32,
}

fn send(stdin: &mut impl Write, value: &impl Serialize) -> Result<()> {
    serde_json::to_writer(&mut *stdin, value).map_err(|e| e.to_string())?;
    stdin
        .write_all(b"\n")
        .and_then(|_| stdin.flush())
        .map_err(|e| e.to_string())
}

/// Execute a real pipe-based host. Only Action messages are mediated; arbitrary
/// effects performed by the backend or command descendants are outside coverage.
pub fn drive_managed(directory: &Path, backend: &ProcessAdapter) -> Result<Response> {
    if !backend.program.is_absolute() || !backend.program.is_file() {
        return Err("managed backend requires an existing absolute executable".into());
    }
    loop {
        let request = Session::open_managed(directory)?.managed_install()?;
        let id = request.invocation_id;
        let mut transcript = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(directory.join(format!("managed-{id}.jsonl")))
            .map_err(|e| e.to_string())?;
        let mut child = Command::new(&backend.program)
            .args(&backend.args)
            .current_dir(Session::open_managed(directory)?.runtime.workspace())
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .map_err(|e| e.to_string())?;
        let mut input = child.stdin.take().expect("spawned with piped stdin");
        let output = child.stdout.take().expect("spawned with piped stdout");
        let (tx, rx) = mpsc::channel();
        let reader = std::thread::spawn(move || {
            for line in BufReader::new(output).lines() {
                if let Ok(text) = &line {
                    if let Err(e) =
                        writeln!(transcript, "{text}").and_then(|_| transcript.sync_data())
                    {
                        let _ = tx.send(Err(e));
                        break;
                    }
                }
                if tx.send(line).is_err() {
                    break;
                }
            }
        });
        let result = (|| -> Result<Option<Response>> {
            // Installation is recorded only after the complete bytes are written.
            send(&mut input, &request)?;
            match Session::open_managed(directory)?.managed_installed(id) {
                Ok(()) => (),
                Err(e) => {
                    if Session::open_managed(directory)?
                        .runtime
                        .outstanding()
                        .map(|r| r.invocation_id)
                        != Some(id)
                    {
                        return Ok(None);
                    }
                    return Err(e);
                }
            }
            loop {
                // This checks identity only while waiting; full source checks run
                // at actual admission. Publication can proceed while we wait.
                if Session::open_managed(directory)?
                    .runtime
                    .outstanding()
                    .map(|r| r.invocation_id)
                    != Some(id)
                {
                    return Ok(None);
                }
                let line = match rx.recv_timeout(Duration::from_millis(50)) {
                    Ok(line) => line.map_err(|e| e.to_string())?,
                    Err(mpsc::RecvTimeoutError::Timeout) => continue,
                    Err(_) => {
                        return Err(
                            "backend ended without a correlated return; do not replay".into()
                        );
                    }
                };
                match serde_json::from_str::<Request>(&line).map_err(|e| e.to_string())? {
                    Request::Event { event } => {
                        if !matches!(
                            event,
                            EventKind::Usage { .. }
                                | EventKind::Progress { .. }
                                | EventKind::Challenge { .. }
                        ) {
                            return Err("the host owns managed continuation and settlement".into());
                        }
                        let mut session = Session::open_managed(directory)?;
                        session.managed_current(id)?;
                        let sequence = session
                            .runtime
                            .execution()
                            .ok_or("missing execution")?
                            .events
                            .len() as u64
                            + 1;
                        session.event(Event {
                            invocation_id: id,
                            sequence,
                            event,
                        })?;
                        send(
                            &mut input,
                            &serde_json::json!({"kind":"recorded","invocation_id":id,"sequence":sequence}),
                        )?;
                    }
                    Request::Action {
                        action_id,
                        command,
                        invocation_id,
                    } => {
                        if invocation_id.is_some_and(|v| v != id) {
                            send(
                                &mut input,
                                &serde_json::json!({"kind":"denied","reason":"invocation identity belongs to the host pipe"}),
                            )?;
                            continue;
                        }
                        let launch = Session::open_managed(directory)?.managed_start(
                            id,
                            &action_id,
                            command.clone(),
                        );
                        match launch {
                            Ok(mut action) => {
                                // Release the Session lock before waiting. A
                                // correction can retire this worker meanwhile.
                                let status = action.wait().map_err(|e| e.to_string())?;
                                let outcome = status.code().unwrap_or(-1);
                                write_json(
                                    &directory
                                        .join(format!("action-{id}-{action_id}.receipt.json")),
                                    &Receipt {
                                        invocation_id: id,
                                        action_id: action_id.clone(),
                                        command,
                                        exit_code: outcome,
                                    },
                                )?;
                                let receipt = Session::open_managed(directory)?
                                    .managed_settle(id, &action_id, outcome)?;
                                if Session::open_managed(directory)?
                                    .runtime
                                    .outstanding()
                                    .map(|r| r.invocation_id)
                                    != Some(id)
                                {
                                    return Ok(None);
                                }
                                if let Err(error) = send(&mut input, &receipt) {
                                    if Session::open_managed(directory)?
                                        .runtime
                                        .outstanding()
                                        .map(|r| r.invocation_id)
                                        != Some(id)
                                    {
                                        return Ok(None);
                                    }
                                    return Err(error);
                                }
                            }
                            Err(reason) => send(
                                &mut input,
                                &serde_json::json!({"kind":"denied","reason":reason}),
                            )?,
                        }
                    }
                    Request::Return { response } => {
                        if response.invocation_id != id || response.role != request.role {
                            return Err("return differs from host-owned invocation".into());
                        }
                        let session = Session::open_managed(directory)?;
                        write_json(
                            &directory.join(format!("managed-return-{id}.json")),
                            &response,
                        )?;
                        if session.runtime.outstanding().map(|r| r.invocation_id) != Some(id) {
                            return Ok(None);
                        }
                        session.managed_current(id)?;
                        return Ok(Some(response));
                    }
                }
            }
        })();
        // No admitted command is running here. Retiring backend computation does
        // not claim rollback of actions or coverage of unmediated descendants.
        drop(input);
        if child.try_wait().map_err(|e| e.to_string())?.is_none() {
            child.kill().map_err(|e| e.to_string())?;
        }
        child.wait().map_err(|e| e.to_string())?;
        Session::open_managed(directory)?.managed_stopped(id)?;
        // Do not wait indefinitely for a descendant holding stdout open.
        if reader.is_finished() {
            let _ = reader.join();
        }
        match result? {
            Some(response) => {
                let mut session = Session::open_managed(directory)?;
                if session.runtime.outstanding().map(|r| r.invocation_id) != Some(id) {
                    continue;
                }
                session.managed_current(id)?;
                session.adopt(response.clone())?;
                session.managed.invocations.get_mut(&id).unwrap().phase = "completed".into();
                session.persist(&session.runtime)?;
                return Ok(response);
            }
            None => continue,
        }
    }
}
