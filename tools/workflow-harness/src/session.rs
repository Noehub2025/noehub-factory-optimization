//! Durable invocation state and a replaceable, single-invocation process adapter.
//! No failed or uncertain process invocation is automatically repeated.

use crate::control::{
    Adapter, Cancellation, Capabilities, Continuation, Event, EventKind, Message, Recovery,
};
use crate::{Invocation, Response, Result, Role, Runtime, Task};
use serde::{Deserialize, Serialize};
use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Checkpoint {
    format_version: u32,
    runtime: Runtime,
    #[serde(default)]
    decisions: crate::decision::Guard,
    #[serde(default)]
    current_use: crate::current_use::Bindings,
}

#[derive(Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProcessAdapter {
    pub program: PathBuf,
    #[serde(default)]
    pub args: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct HostBinding {
    pub invocation_id: usize,
    pub backend_handle: String,
}

pub struct Session {
    pub runtime: Runtime,
    pub decisions: crate::decision::Guard,
    current_use: crate::current_use::Bindings,
    directory: PathBuf,
    // The operating system releases this lock if the harness exits or crashes.
    _lock: File,
}

impl Drop for Session {
    fn drop(&mut self) {
        // Release ownership explicitly. A concurrent process spawn can briefly
        // inherit an open descriptor before exec closes it; closing only our
        // descriptor can then leave a dropped Session's lock apparently owned.
        let _ = self._lock.unlock();
    }
}

fn write_json(path: &Path, value: &impl Serialize) -> Result<()> {
    let mut file = File::create(path).map_err(|e| e.to_string())?;
    serde_json::to_writer_pretty(&mut file, value).map_err(|e| e.to_string())?;
    file.write_all(b"\n").map_err(|e| e.to_string())?;
    file.sync_all().map_err(|e| e.to_string())
}

fn lock(directory: &Path) -> Result<File> {
    let file = OpenOptions::new()
        .create(true)
        .truncate(false)
        .read(true)
        .write(true)
        .open(directory.join("writer.lock"))
        .map_err(|e| e.to_string())?;
    file.try_lock()
        .map_err(|e| format!("another harness may own this run: {e}"))?;
    Ok(file)
}

impl Session {
    /// Optional cooperating-host boundary. The existing owner checker must validate
    /// adoption and finding discharge before supplying this binding. No model is called.
    pub fn adopt_current_use(&mut self, binding: crate::current_use::CurrentUse) -> Result<()> {
        binding.verify_saved()?;
        if let Some(previous) = &self.current_use.adopted {
            binding.carries(previous)?;
        }
        let previous = self.current_use.clone();
        self.current_use.adopted = Some(binding);
        if let Err(error) = self.persist(&self.runtime) {
            self.current_use = previous;
            return Err(error);
        }
        Ok(())
    }

    fn require_current_use_ready(&self) -> Result<()> {
        if let Some(binding) = &self.current_use.adopted {
            binding.require_ready()?;
        }
        Ok(())
    }

    /// External dispatchers must present the actual queued request they will consume.
    pub fn verify_queued_current_use(&self, request: &Invocation) -> Result<()> {
        let pending = self.runtime.outstanding().ok_or("no queued work")?;
        if serde_json::to_value(request).map_err(|e| e.to_string())?
            != serde_json::to_value(pending).map_err(|e| e.to_string())?
        {
            return Err("dispatcher supplied an obsolete or different queued request".into());
        }
        self.verify_current_use_consumption()
    }

    /// Verify at actual Session consumption, including a request prepared earlier.
    /// External hosts use `verify_queued_current_use` with their actual request.
    pub fn verify_current_use_consumption(&self) -> Result<()> {
        let Some(request) = self
            .runtime
            .outstanding()
            .filter(|r| r.role == Role::Worker)
        else {
            return Ok(());
        };
        if let Some(binding) = &self.current_use.adopted {
            binding.require_ready()?;
            if self.current_use.queued.as_ref() != Some(&(request.invocation_id, binding.clone())) {
                return Err(
                    "queued work references an older adoption; replace it through its owner".into(),
                );
            }
        }
        Ok(())
    }

    /// Replace only unstarted queued work after its existing owner adopts a correction.
    /// Already started effects must be reconciled through their existing execution.
    pub fn replace_queued_work(&mut self, assignment: String) -> Result<Invocation> {
        crate::contract::nonempty(&assignment, "corrected assignment")?;
        let request = self.runtime.outstanding().ok_or("no queued work")?;
        if request.role != Role::Worker
            || self.runtime.execution().is_some()
            || self.host_binding()?.is_some()
            || self
                .directory
                .join(format!("stdout-{}.json", request.invocation_id))
                .exists()
        {
            return Err(
                "replace only unstarted worker requests; reconcile existing effects first".into(),
            );
        }
        self.require_current_use_ready()?;
        let current_sources = crate::source_contents(&self.runtime.task)?;
        let replacement_id = self
            .runtime
            .next_id
            .checked_add(1)
            .ok_or("invocation id overflow")?;
        let previous_runtime = self.runtime.clone();
        let previous_binding = self.current_use.clone();
        self.runtime.assignment = format!(
            "This assignment supersedes the earlier queued restriction and task.\n{assignment}"
        );
        self.runtime.outstanding = None;
        self.runtime.next_id = replacement_id;
        // This explicit owner operation adopts the corrected saved task inputs.
        self.runtime.selected_sources = current_sources;
        self.current_use.queued = None;
        match self.request() {
            Ok(request) => Ok(request),
            Err(error) => {
                self.runtime = previous_runtime;
                self.current_use = previous_binding;
                Err(error)
            }
        }
    }

    pub fn directory(&self) -> &Path {
        &self.directory
    }

    /// An external pause only withholds work and does not require the writer lock.
    pub fn request_pause(directory: &Path, reason: String) -> Result<()> {
        crate::contract::nonempty(&reason, "pause reason")?;
        if !directory.join("state.json").is_file() {
            return Err("run does not exist".into());
        }
        let mut file = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(directory.join("pause-request.json"))
            .map_err(|e| e.to_string())?;
        serde_json::to_writer(&mut file, &reason).map_err(|e| e.to_string())?;
        file.sync_all().map_err(|e| e.to_string())
    }

    fn observe_pause(&mut self) -> Result<()> {
        let path = self.directory.join("pause-request.json");
        if path.exists() {
            let reason: String =
                serde_json::from_slice(&fs::read(path).map_err(|e| e.to_string())?)
                    .map_err(|_| "pause request incomplete; withhold new work".to_string())?;
            self.pause(reason)?;
        }
        Ok(())
    }
    /// Persist every control transition before allowing a backend to continue.
    pub fn begin_execution(&mut self, capabilities: Capabilities) -> Result<()> {
        self.observe_pause()?;
        self.verify_current_use_consumption()?;
        let mut next = self.runtime.clone();
        next.begin_execution(capabilities)?;
        self.persist(&next)?;
        self.runtime = next;
        Ok(())
    }

    pub fn event(&mut self, event: Event) -> Result<bool> {
        let mut next = self.runtime.clone();
        let changed = next.event(event.clone())?;
        if changed {
            self.persist(&next)?;
            self.runtime = next;
            self.record(serde_json::json!({"event":"backend_event","value":event}))?;
        }
        Ok(changed)
    }

    /// Changed current use withholds more work, but must not prevent an already
    /// started backend from completing its existing return and settlement handshake.
    fn observe_current_use_return(&self, next: &mut Runtime) -> Result<()> {
        if let Err(reason) = self.verify_current_use_consumption() {
            if next.execution().is_none() {
                return Err(reason);
            }
            next.execution_mut()?.require_return(format!(
                "Current-use owner reconciliation required before more work: {reason}"
            ));
        }
        Ok(())
    }

    pub fn continuation(&mut self) -> Result<Continuation> {
        self.observe_pause()?;
        let mut next = self.runtime.clone();
        self.observe_current_use_return(&mut next)?;
        let decision = next.continuation()?;
        self.persist(&next)?;
        self.runtime = next;
        self.record(serde_json::json!({"event":"continuation_decision","decision":decision}))?;
        Ok(decision)
    }

    /// Persist the same selected return conditions at a host's pre-dispatch seam.
    /// No host identity, tool name, or effect-settlement inference enters the core.
    pub fn check_action(&mut self) -> Result<Continuation> {
        self.observe_pause()?;
        let mut next = self.runtime.clone();
        self.observe_current_use_return(&mut next)?;
        let decision = next.check_action()?;
        self.persist(&next)?;
        self.runtime = next;
        self.record(serde_json::json!({"event":"action_decision","decision":decision}))?;
        Ok(decision)
    }

    pub fn pause(&mut self, reason: String) -> Result<()> {
        let mut next = self.runtime.clone();
        next.pause(reason)?;
        self.persist(&next)?;
        self.runtime = next;
        Ok(())
    }

    pub fn unpause(&mut self) -> Result<()> {
        let mut next = self.runtime.clone();
        next.unpause()?;
        self.persist(&next)?;
        self.runtime = next;
        let path = self.directory.join("pause-request.json");
        if path.exists() {
            fs::remove_file(path).map_err(|e| e.to_string())?;
        }
        Ok(())
    }

    pub fn cancel(&mut self, backend: &mut impl Adapter, reason: String) -> Result<Cancellation> {
        self.pause(reason)?;
        let request = self.runtime.outstanding().ok_or("no pending invocation")?;
        let result = if backend.capabilities().cooperative_cancel {
            backend
                .cancel(request.invocation_id)
                .unwrap_or(Cancellation::Unknown)
        } else {
            Cancellation::Unsupported
        };
        let mut next = self.runtime.clone();
        next.cancellation(result.clone())?;
        self.persist(&next)?;
        self.runtime = next;
        Ok(result)
    }

    /// Start once and enforce the adapter continuation handshake. No project
    /// commands or model-provider APIs are embedded in the runtime.
    pub fn drive(&mut self, backend: &mut impl Adapter) -> Result<Response> {
        if self.host_binding()?.is_some() {
            return Err("invocation already belongs to a host call".into());
        }
        let request = self
            .runtime
            .outstanding()
            .ok_or("no pending invocation")?
            .clone();
        if self
            .directory
            .join(format!("stdout-{}.json", request.invocation_id))
            .exists()
        {
            return Err("legacy dispatch may exist; reconcile before changing transports".into());
        }
        self.begin_execution(backend.capabilities())?;
        // A failure after this durable dispatch intent is unknown, never retryable.
        backend.invoke(&request)?;
        self.collect(backend)
    }

    fn collect(&mut self, backend: &mut impl Adapter) -> Result<Response> {
        loop {
            match backend.next()? {
                Message::Event { event } => {
                    let boundary = matches!(event.event, EventKind::Boundary { .. });
                    if self.event(event)? && boundary {
                        let decision = self.continuation()?;
                        backend.continue_work(&decision)?;
                    }
                }
                Message::Return { response } => {
                    let response = *response;
                    let request = self.runtime.outstanding().ok_or("no pending invocation")?;
                    if response.invocation_id != request.invocation_id
                        || response.role != request.role
                    {
                        return Err("backend return has wrong invocation or role".into());
                    }
                    write_json(
                        &self
                            .directory
                            .join(format!("received-{}.json", response.invocation_id)),
                        &response,
                    )?;
                    self.accept(response.clone())?;
                    return Ok(response);
                }
            }
        }
    }

    pub fn recover_backend(&mut self, backend: &mut impl Adapter) -> Result<Recovery> {
        let id = self
            .runtime
            .outstanding()
            .ok_or("no pending invocation")?
            .invocation_id;
        if self.runtime.execution().is_none() {
            return Err("no registered execution to recover".into());
        }
        let recovery = if backend.capabilities().recovery {
            backend.recover(id)?
        } else {
            Recovery::Unsupported
        };
        if let Recovery::Terminal {
            response,
            effects_settled,
        } = &recovery
        {
            let request = self.runtime.outstanding().unwrap();
            if response.invocation_id != request.invocation_id || response.role != request.role {
                return Err("recovered terminal receipt has wrong invocation or role".into());
            }
            let execution = self.runtime.execution().unwrap();
            if !execution.stopped {
                self.event(Event {
                    invocation_id: id,
                    sequence: execution.events.len() as u64 + 1,
                    event: EventKind::Stopped {
                        effects_settled: *effects_settled,
                    },
                })?;
            }
            // An unresolved stopped receipt cannot be cleared by a later label.
            self.accept(*response.clone())?;
            self.recover_for_adoption()?;
        }
        // Running, not-started and unknown never invoke or resend a continuation.
        Ok(recovery)
    }
    pub fn host_binding(&self) -> Result<Option<HostBinding>> {
        let Some(request) = self.runtime.outstanding() else {
            return Ok(None);
        };
        let path = self
            .directory
            .join(format!("host-{}.json", request.invocation_id));
        match fs::read(path) {
            Ok(bytes) => serde_json::from_slice(&bytes)
                .map(Some)
                .map_err(|e| e.to_string()),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(None),
            Err(e) => Err(e.to_string()),
        }
    }

    /// Record the handle returned by an existing host tool, without calling another backend.
    pub fn bind_host(&self, binding: HostBinding) -> Result<()> {
        let request = self.runtime.outstanding().ok_or("no pending invocation")?;
        if binding.invocation_id != request.invocation_id
            || binding.backend_handle.trim().is_empty()
        {
            return Err(
                "host binding needs the pending invocation ID and actual backend handle".into(),
            );
        }
        if self
            .directory
            .join(format!("stdout-{}.json", request.invocation_id))
            .exists()
        {
            return Err("a process dispatch may already have started; reconcile it instead of changing transports".into());
        }
        if let Some(existing) = self.host_binding()? {
            return if existing == binding {
                Ok(())
            } else {
                Err("this invocation already has a different host handle".into())
            };
        }
        let temporary = self
            .directory
            .join(format!("host-{}.next.json", request.invocation_id));
        write_json(&temporary, &binding)?;
        // The run's exclusive lock serializes publication, as for the checkpoint.
        fs::rename(
            temporary,
            self.directory
                .join(format!("host-{}.json", request.invocation_id)),
        )
        .map_err(|e| e.to_string())?;
        #[cfg(unix)]
        File::open(&self.directory)
            .and_then(|file| file.sync_all())
            .map_err(|e| e.to_string())?;
        self.record(serde_json::json!({"event":"host_binding","binding":binding}))
    }

    pub fn accept_host_return(&mut self, backend_handle: &str, response: Response) -> Result<()> {
        let binding = self
            .host_binding()?
            .ok_or("no host dispatch has been recorded")?;
        if binding.backend_handle != backend_handle
            || binding.invocation_id != response.invocation_id
        {
            return Err("return does not match the recorded host invocation".into());
        }
        self.adopt(response)
    }

    pub fn create(task: Task, directory: &Path) -> Result<Self> {
        let runtime = Runtime::new(task)?;
        fs::create_dir(directory).map_err(|e| format!("new run directory required: {e}"))?;
        let session = Self {
            runtime,
            decisions: Default::default(),
            current_use: Default::default(),
            directory: directory.to_path_buf(),
            _lock: lock(directory)?,
        };
        session.persist(&session.runtime)?;
        Ok(session)
    }

    pub fn open(directory: &Path) -> Result<Self> {
        let lock = lock(directory)?;
        let checkpoint: Checkpoint = serde_json::from_slice(
            &fs::read(directory.join("state.json")).map_err(|e| e.to_string())?,
        )
        .map_err(|e| format!("invalid saved state; do not replay this run: {e}"))?;
        if checkpoint.format_version != 1 {
            return Err("unsupported saved state; no automatic migration or replay".into());
        }
        Ok(Self {
            runtime: checkpoint.runtime,
            decisions: checkpoint.decisions,
            current_use: checkpoint.current_use,
            directory: directory.to_path_buf(),
            _lock: lock,
        })
    }

    fn persist(&self, runtime: &Runtime) -> Result<()> {
        let temporary = self.directory.join("state.next.json");
        write_json(
            &temporary,
            &Checkpoint {
                format_version: 1,
                runtime: runtime.clone(),
                decisions: self.decisions.clone(),
                current_use: self.current_use.clone(),
            },
        )?;
        fs::rename(temporary, self.directory.join("state.json")).map_err(|e| e.to_string())?;
        // Directory synchronization is available on Unix. Other platforms still get
        // file synchronization and rename, not a claimed power-loss guarantee.
        #[cfg(unix)]
        File::open(&self.directory)
            .and_then(|file| file.sync_all())
            .map_err(|e| e.to_string())?;
        Ok(())
    }

    fn record(&self, event: serde_json::Value) -> Result<()> {
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(self.directory.join("events.jsonl"))
            .map_err(|e| e.to_string())?;
        writeln!(file, "{event}").map_err(|e| e.to_string())?;
        file.sync_all().map_err(|e| e.to_string())
    }

    pub fn request(&mut self) -> Result<Invocation> {
        self.expire_decision()?;
        if self.decisions.holds() {
            return Err("decision or publication is pending; inspect host decision-status".into());
        }
        self.observe_pause()?;
        if let Some(publication) = &self.decisions.publication {
            publication.verify()?;
        }
        let mut next = self.runtime.clone();
        let mut request = next.request()?;
        if request.role == Role::Worker
            && let Some(binding) = &self.current_use.adopted
        {
            binding.require_ready()?;
            if let Some((id, queued)) = &self.current_use.queued
                && *id == request.invocation_id
                && queued != binding
            {
                return Err(
                    "queued work references an older adoption; replace it through its owner".into(),
                );
            }
            request.prompt.push_str(&format!(
                "\nCurrent-use owner: {}. Retained correction references: {}. Use the current saved affected objects for this assignment: {}. The existing owner adopted this scoped use; these references are not a new semantic verdict.\n",
                binding.owner.display(),
                serde_json::to_string(&binding.correction_ids).map_err(|e| e.to_string())?,
                serde_json::to_string(&binding.files.iter().map(|file| &file.path).collect::<Vec<_>>()).map_err(|e| e.to_string())?
            ));
            next.outstanding = Some(request.clone());
            self.current_use.queued = Some((request.invocation_id, binding.clone()));
        }
        // Deliver the policy to the existing owner/resolver, not a second reviewer.
        if matches!(request.role, Role::Coordinator | Role::Resolver)
            && let Some(config) = self
                .decisions
                .config
                .as_ref()
                .filter(|c| c.mode != crate::decision::Mode::Disabled)
        {
            const MARKER: &str = "\nParticipating investment policy:\n";
            if !request.prompt.contains(MARKER) {
                request.prompt.push_str(MARKER);
                match fs::read_to_string(&config.policy) {
                        Ok(policy) => request.prompt.push_str(&format!("{policy}\nApply this in the existing investment judgment once. Coordinator: reuse an applicable accepted Resolver response via update.resolved_invocation, or supplied independent sources via resolved_by. Set investment_changed only for a new or materially changed investment, not progress or rewritten rationale. Reuse asserts applicability; it is not a new checker verdict.\n")),
                        Err(_) => request.prompt.push_str("\nOptional decision policy unavailable; coverage is degraded, not passed.\n"),
                    }
                next.outstanding = Some(request.clone());
            }
        }
        write_json(
            &self
                .directory
                .join(format!("request-{}.json", request.invocation_id)),
            &request,
        )?;
        let mut guard = self.decisions.clone();
        guard.publication = None;
        self.save_decisions(guard, next)?;
        self.record(serde_json::json!({"event":"invocation_pending","request":request}))?;
        Ok(request)
    }

    pub fn accept(&mut self, response: Response) -> Result<()> {
        if self.host_binding()?.is_some() {
            return Err(
                "pending invocation is host-bound; use host return with the actual backend handle"
                    .into(),
            );
        }
        self.adopt(response)
    }

    fn adopt(&mut self, response: Response) -> Result<()> {
        if self.decisions.holds() {
            return Err("use the pending decision's result or owner disposition; do not resubmit the invocation".into());
        }
        let mut next = self.runtime.clone();
        next.accept(response.clone())?;
        if next.role == Role::Worker {
            self.require_current_use_ready()?;
        }
        let mut guard = self.decisions.clone();
        if next.role == crate::Role::Worker
            && guard.consider(
                &response,
                crate::source_contents(&self.runtime.task)?,
                self.runtime
                    .outstanding()
                    .map(|i| i.prompt.clone())
                    .unwrap_or_default(),
            )?
        {
            return self.save_decisions(guard, self.runtime.clone());
        }
        self.decisions = guard;
        write_json(
            &self
                .directory
                .join(format!("response-{}.json", response.invocation_id)),
            &response,
        )?;
        self.persist(&next)?;
        self.runtime = next;
        self.record(serde_json::json!({"event":"response_accepted","response":response}))
    }

    fn save_decisions(&mut self, guard: crate::decision::Guard, runtime: Runtime) -> Result<()> {
        let previous = std::mem::replace(&mut self.decisions, guard);
        if let Err(error) = self.persist(&runtime) {
            self.decisions = previous;
            return Err(error);
        }
        self.runtime = runtime;
        Ok(())
    }

    pub fn configure_decisions(&mut self, config: crate::decision::Config) -> Result<()> {
        use crate::decision::Mode;
        if config.mode == Mode::Disabled {
            let mut guard = self.decisions.clone();
            if guard.pending.as_ref().is_some_and(|p| {
                p.result
                    .as_ref()
                    .is_some_and(|r| r.verdict == crate::decision::Verdict::Revise)
            }) {
                return Err("address the concrete finding before disabling its check".into());
            }
            if let Some(mut p) = guard.pending.take() {
                p.result = Some(crate::decision::CheckReturn {
                    check_id: p.check_id,
                    backend_handle: p.backend_handle.clone().unwrap_or_default(),
                    verdict: crate::decision::Verdict::Unavailable,
                    reason: "Owner disabled optional coverage; proposal returned without adoption"
                        .into(),
                    findings: vec![],
                    model_tokens: None,
                });
                guard.receipts.push(p);
            }
            guard.config = Some(config);
            return self.save_decisions(guard, self.runtime.clone());
        }
        if self.decisions.pending.is_some() || self.decisions.holds() {
            return Err("resolve the current decision before changing its configuration".into());
        }
        if config.mode != Mode::Disabled {
            if !config.policy.is_absolute() || !config.policy.is_file() || config.timeout_ms == 0 {
                return Err(
                    "policy must be an existing absolute file and timeout must be positive".into(),
                );
            }
            if self.runtime.task.research.is_none() {
                return Err("decision coverage requires the existing research protocol".into());
            }
            if let Some(path) = &config.publication
                && (!path.is_absolute() || !path.starts_with(self.runtime.workspace()))
            {
                return Err("publication must be a path within the participating workspace".into());
            }
        }
        let mut guard = self.decisions.clone();
        guard.config = Some(config);
        self.save_decisions(guard, self.runtime.clone())
    }

    /// The host must bind the actual checker before accepting its reply.
    pub fn bind_decision(&mut self, check_id: u64, handle: String) -> Result<()> {
        crate::contract::nonempty(&handle, "checker handle")?;
        let mut guard = self.decisions.clone();
        let p = guard.pending.as_mut().ok_or("no pending check")?;
        if p.check_id != check_id || p.result.is_some() {
            return Err("check is stale or already returned".into());
        }
        if p.backend_handle.as_ref().is_some_and(|h| h != &handle) {
            return Err("check already bound; reconcile the existing host call".into());
        }
        p.backend_handle = Some(handle);
        self.save_decisions(guard, self.runtime.clone())
    }

    pub fn decision_result(&mut self, result: crate::decision::CheckReturn) -> Result<()> {
        use crate::decision::Verdict;
        crate::contract::nonempty(&result.reason, "check reason")?;
        self.expire_decision()?;
        let mut guard = self.decisions.clone();
        if let Some(receipt) = guard
            .receipts
            .iter_mut()
            .find(|p| p.check_id == result.check_id)
        {
            if receipt.backend_handle.as_ref() == Some(&result.backend_handle)
                && receipt
                    .result
                    .as_ref()
                    .is_some_and(|r| r.verdict == Verdict::Unavailable)
                && receipt.late_returns.is_empty()
            {
                receipt.late_returns.push(result);
                return self.save_decisions(guard, self.runtime.clone());
            }
            return Err("stale or duplicate check return".into());
        }
        let p = guard.pending.as_mut().ok_or("no pending check")?;
        if p.check_id != result.check_id
            || p.backend_handle.as_ref() != Some(&result.backend_handle)
            || p.result.is_some()
        {
            return Err("stale, duplicate or unbound check return".into());
        }
        let text = format!(
            "{}\n{}\n{}",
            p.proposal.summary,
            p.proposal.assignment,
            serde_json::to_string(&p.proposal.update).map_err(|e| e.to_string())?
        );
        if (result.verdict == Verdict::Revise) == result.findings.is_empty() {
            return Err(
                "revise requires concrete findings; other verdicts must not carry findings".into(),
            );
        }
        for f in &result.findings {
            crate::contract::nonempty(&f.policy_excerpt, "policy excerpt")?;
            crate::contract::nonempty(&f.decision_excerpt, "decision excerpt")?;
            crate::contract::nonempty(&f.correction, "correction")?;
            if !p.policy.contains(&f.policy_excerpt) || !text.contains(&f.decision_excerpt) {
                return Err(
                    "finding excerpts must occur in the supplied policy and proposal".into(),
                );
            }
        }
        p.result = Some(result);
        let release = p.observed_only
            || p.result
                .as_ref()
                .is_some_and(|r| r.verdict != Verdict::Revise);
        if release {
            self.release_decision(guard)
        } else {
            self.save_decisions(guard, self.runtime.clone())
        }
    }

    pub fn resolve_decision(&mut self, owner: crate::decision::OwnerReturn) -> Result<()> {
        use crate::decision::{Disposition, Verdict};
        crate::contract::nonempty(&owner.reason, "owner reason or exact boundary")?;
        if owner.evidence.is_empty()
            || owner
                .evidence
                .iter()
                .any(|p| !p.is_absolute() || !p.is_file())
        {
            return Err("owner disposition needs existing absolute evidence references".into());
        }
        let mut guard = self.decisions.clone();
        let p = guard.pending.as_mut().ok_or("no pending check")?;
        if p.check_id != owner.check_id
            || p.owner.is_some()
            || !p
                .result
                .as_ref()
                .is_some_and(|r| r.verdict == Verdict::Revise)
        {
            return Err("owner must address the current concrete finding exactly once".into());
        }
        if owner.disposition == Disposition::Revised {
            let response = owner
                .proposal
                .as_ref()
                .ok_or("revised disposition needs corrected proposal")?;
            if response.invocation_id != p.proposal.invocation_id
                || response.role != Role::Coordinator
            {
                return Err("revision changes the owning invocation".into());
            }
            self.runtime.clone().accept(response.clone())?;
        } else if owner.proposal.is_some() {
            return Err("only a revised disposition replaces the proposal".into());
        }
        p.owner = Some(owner);
        self.release_decision(guard)
    }

    /// Expiry never turns a concrete finding into a pass and never reruns a checker.
    pub fn expire_decision(&mut self) -> Result<()> {
        use crate::decision::{CheckReturn, Verdict};
        let mut guard = self.decisions.clone();
        let Some(p) = guard.pending.as_mut() else {
            return Ok(());
        };
        if p.result.is_some() || crate::decision::now_ms()? < p.deadline_ms {
            return Ok(());
        }
        p.result = Some(CheckReturn { check_id: p.check_id,
            backend_handle: p.backend_handle.clone().unwrap_or_default(),
            verdict: Verdict::Unavailable, reason: "Check deadline expired; coverage degraded. Do not repeat an uncertain host invocation.".into(),
            findings: vec![], model_tokens: None });
        self.release_decision(guard)
    }

    fn release_decision(&mut self, mut guard: crate::decision::Guard) -> Result<()> {
        use crate::decision::{Disposition, Publication};
        let p = guard.pending.take().ok_or("no pending check")?;
        let boundary = p
            .owner
            .as_ref()
            .is_some_and(|o| o.disposition == Disposition::Boundary);
        let proposal = p
            .owner
            .as_ref()
            .and_then(|o| o.proposal.as_ref())
            .unwrap_or(&p.proposal);
        let mut next = self.runtime.clone();
        if !p.observed_only {
            if p.owner.is_none()
                && (crate::source_contents(&self.runtime.task).ok().as_ref() != Some(&p.sources)
                    || std::fs::read_to_string(
                        &guard.config.as_ref().ok_or("missing config")?.policy,
                    )
                    .ok()
                    .as_ref()
                        != Some(&p.policy))
            {
                // Preserve the receipt, but never adopt a proposal checked against stale inputs.
                // Its original Coordinator invocation remains available for reconciliation.
                guard.receipts.push(p);
                return self.save_decisions(guard, next);
            }
            if boundary {
                // Ordinary owner reconciliation remains possible; never invent Finish.
                let mut returned = proposal.clone();
                returned.decision = crate::Decision::Reconsider;
                next.accept(returned)?;
                next.pause(p.owner.as_ref().unwrap().reason.clone())?;
            } else {
                next.accept(proposal.clone())?;
                if next.role == Role::Worker {
                    self.require_current_use_ready()?;
                }
                if next.role == Role::Worker {
                    guard.last_commitment = Some(crate::decision::commitment(proposal)?);
                    guard.last_policy = Some(p.policy.clone());
                    if let Some(path) = guard.config.as_ref().and_then(|c| c.publication.clone()) {
                        guard.publication = Some(Publication {
                            check_id: p.check_id,
                            path,
                            proposal: serde_json::to_value(proposal).map_err(|e| e.to_string())?,
                            confirmed: false,
                        });
                    }
                }
            }
        }
        guard.receipts.push(p);
        self.save_decisions(guard, next)
    }

    /// Discard only stale proposals; do not make a concrete finding disappear.
    pub fn abandon_decision(&mut self, reason: String) -> Result<()> {
        crate::contract::nonempty(&reason, "stale-proposal reason")?;
        let mut guard = self.decisions.clone();
        let p = guard.pending.as_ref().ok_or("no pending check")?;
        if p.result
            .as_ref()
            .is_some_and(|r| r.verdict == crate::decision::Verdict::Revise)
        {
            return Err("a concrete finding needs its owner disposition, not abandonment".into());
        }
        if crate::source_contents(&self.runtime.task).ok().as_ref() == Some(&p.sources)
            && std::fs::read_to_string(&guard.config.as_ref().unwrap().policy)
                .ok()
                .as_ref()
                == Some(&p.policy)
        {
            return Err("proposal is not stale; use its normal outcome".into());
        }
        let mut p = guard.pending.take().unwrap();
        p.result = Some(crate::decision::CheckReturn {
            check_id: p.check_id,
            backend_handle: p.backend_handle.clone().unwrap_or_default(),
            verdict: crate::decision::Verdict::Unavailable,
            reason,
            findings: vec![],
            model_tokens: None,
        });
        guard.receipts.push(p);
        self.save_decisions(guard, self.runtime.clone())
    }

    pub fn confirm_publication(&mut self, check_id: u64) -> Result<()> {
        let mut guard = self.decisions.clone();
        let p = guard
            .publication
            .as_mut()
            .ok_or("no publication expected")?;
        if p.check_id != check_id {
            return Err("publication check is stale".into());
        }
        p.verify()?;
        p.confirmed = true;
        self.save_decisions(guard, self.runtime.clone())
    }

    pub fn recover_for_adoption(&mut self) -> Result<()> {
        let mut next = self.runtime.clone();
        next.recover_for_adoption()?;
        self.persist(&next)?;
        self.runtime = next;
        Ok(())
    }

    /// This is a terminal process receipt, not proof that all external effects settled.
    pub fn collected_response(&self) -> Result<Response> {
        let request = self.runtime.outstanding().ok_or("no pending invocation")?;
        let receipt: ProcessReceipt = serde_json::from_slice(
            &fs::read(
                self.directory
                    .join(format!("process-{}.json", request.invocation_id)),
            )
            .map_err(|_| {
                "pending invocation has no terminal receipt; reconcile it without redispatch"
                    .to_string()
            })?,
        )
        .map_err(|e| e.to_string())?;
        if receipt.invocation_id != request.invocation_id || !receipt.success {
            return Err("process did not return successfully; preserve outputs and reconcile, do not retry the work".into());
        }
        serde_json::from_slice(
            &fs::read(self.directory.join(format!("stdout-{}.json", request.invocation_id)))
                .map_err(|e| e.to_string())?,
        )
        .map_err(|e| format!("invalid process response; retain pending state and correct the return, not rerun work: {e}"))
    }

    pub fn invoke(&self, adapter: &ProcessAdapter) -> Result<Response> {
        self.verify_current_use_consumption()?;
        let request = self.runtime.outstanding().ok_or("no pending invocation")?;
        if request.protocol != "workflow-invocation/1" {
            return Err(
                "legacy process adapter cannot execute the controlled research protocol".into(),
            );
        }
        if self.host_binding()?.is_some() {
            return Err(
                "this invocation belongs to an existing host call; do not dispatch a process"
                    .into(),
            );
        }
        if !adapter.program.is_absolute() || !adapter.program.is_file() {
            return Err("adapter program must be an existing absolute file".into());
        }
        let stdout = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(
                self.directory
                    .join(format!("stdout-{}.json", request.invocation_id)),
            )
            .map_err(|e| {
                format!("invocation output already exists or cannot be created; do not replay: {e}")
            })?;
        let stderr = OpenOptions::new()
            .create_new(true)
            .write(true)
            .open(
                self.directory
                    .join(format!("stderr-{}.txt", request.invocation_id)),
            )
            .map_err(|e| e.to_string())?;
        let input = File::open(
            self.directory
                .join(format!("request-{}.json", request.invocation_id)),
        )
        .map_err(|e| e.to_string())?;
        let backend_directory = fs::canonicalize(&self.directory)
            .map_err(|e| e.to_string())?
            .join(format!("backend-{}", request.invocation_id));
        fs::create_dir(&backend_directory).map_err(|e| e.to_string())?;
        // Files avoid pipe-buffer deadlocks and preserve partial output on interruption.
        // Arguments are passed directly, never interpreted through a shell.
        let status = Command::new(&adapter.program)
            .args(&adapter.args)
            .current_dir(self.runtime.workspace())
            .env("WORKFLOW_INVOCATION_DIRECTORY", backend_directory)
            .stdin(Stdio::from(input))
            .stdout(Stdio::from(stdout.try_clone().map_err(|e| e.to_string())?))
            .stderr(Stdio::from(stderr.try_clone().map_err(|e| e.to_string())?))
            .status()
            .map_err(|e| {
                format!("adapter invocation failed; pending work requires reconciliation: {e}")
            })?;
        stdout.sync_all().map_err(|e| e.to_string())?;
        stderr.sync_all().map_err(|e| e.to_string())?;
        write_json(
            &self
                .directory
                .join(format!("process-{}.json", request.invocation_id)),
            &ProcessReceipt {
                invocation_id: request.invocation_id,
                success: status.success(),
                exit_code: status.code(),
            },
        )?;
        self.collected_response()
    }
}

#[derive(Deserialize, Serialize)]
struct ProcessReceipt {
    invocation_id: usize,
    success: bool,
    exit_code: Option<i32>,
}
