//! Observable work-segment control. A backend must wait at continuation points.
//! This is not a sandbox for unrelated tools or arbitrary background processes.

use crate::contract::{Segment, Usage, nonempty};
use crate::{Invocation, Response, Result};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

pub fn now_ms() -> Result<u64> {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|e| e.to_string())?
        .as_millis()
        .try_into()
        .map_err(|_| "clock overflow".into())
}

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Capabilities {
    pub events: bool,
    pub controlled_continuation: bool,
    pub cooperative_cancel: bool,
    pub recovery: bool,
    pub fresh_context: bool,
    /// A descriptive, verifiable scope; not a self-issued permission.
    pub isolation: String,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum EventKind {
    Usage {
        total: Usage,
    },
    Progress {
        summary: String,
        evidence: Vec<PathBuf>,
    },
    Challenge {
        reason: String,
    },
    /// The backend is idle here and cannot issue more work until instructed.
    Boundary {
        reason: String,
        return_due: bool,
        effects_settled: bool,
    },
    Stopped {
        effects_settled: bool,
    },
    Reconciled {
        summary: String,
        evidence: Vec<PathBuf>,
    },
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Event {
    pub invocation_id: usize,
    pub sequence: u64,
    pub event: EventKind,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(tag = "decision", rename_all = "snake_case")]
pub enum Continuation {
    Continue,
    Return { reasons: Vec<String> },
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(tag = "status", rename_all = "snake_case")]
pub enum Cancellation {
    Unsupported,
    Pending,
    Unknown,
    Confirmed { effects_settled: bool },
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(tag = "status", rename_all = "snake_case")]
pub enum Recovery {
    Running,
    Terminal {
        response: Box<Response>,
        effects_settled: bool,
    },
    NotStarted,
    Unknown,
    Unsupported,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(tag = "message", rename_all = "snake_case")]
pub enum Message {
    Event { event: Event },
    Return { response: Box<Response> },
}

/// A controlled backend owns its native tools. It MUST NOT continue past a
/// Boundary until the driver calls continue_work, and Return permits no new
/// discretionary work. Capability declarations alone do not prove compliance.
pub trait Adapter {
    fn capabilities(&self) -> Capabilities;
    fn invoke(&mut self, invocation: &Invocation) -> Result<()>;
    fn next(&mut self) -> Result<Message>;
    fn continue_work(&mut self, decision: &Continuation) -> Result<()>;
    fn cancel(&mut self, invocation_id: usize) -> Result<Cancellation>;
    fn recover(&mut self, invocation_id: usize) -> Result<Recovery>;
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
struct Stamp {
    length: u64,
    modified_ns: u128,
}

fn stamp(path: &PathBuf) -> Result<Option<Stamp>> {
    match fs::metadata(path) {
        Ok(value) => Ok(Some(Stamp {
            length: value.len(),
            modified_ns: value
                .modified()
                .map_err(|e| e.to_string())?
                .duration_since(UNIX_EPOCH)
                .map_err(|e| e.to_string())?
                .as_nanos(),
        })),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(e) => Err(e.to_string()),
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Execution {
    pub invocation_id: usize,
    pub capabilities: Capabilities,
    pub started_ms: u64,
    #[serde(default)]
    pub observed_elapsed_ms: u64,
    pub usage: Usage,
    pub events: Vec<Event>,
    pub return_reasons: Vec<String>,
    pub stopped: bool,
    pub effects_settled: bool,
    pub awaiting_continuation: bool,
    pub continuation_withheld: bool,
    pub cancellation: Option<Cancellation>,
    segment: Option<Segment>,
    watched: BTreeMap<PathBuf, Option<Stamp>>,
}

impl Execution {
    pub fn new(
        invocation_id: usize,
        capabilities: Capabilities,
        segment: Option<Segment>,
    ) -> Result<Self> {
        if segment.is_some() && (!capabilities.events || !capabilities.controlled_continuation) {
            return Err(
                "this work needs observable, controlled continuation; backend does not support it"
                    .into(),
            );
        }
        let mut watched = BTreeMap::new();
        if let Some(segment) = &segment {
            for path in &segment.return_on_change {
                watched.insert(path.clone(), stamp(path)?);
            }
        }
        Ok(Self {
            invocation_id,
            capabilities,
            started_ms: now_ms()?,
            observed_elapsed_ms: 0,
            usage: Usage::default(),
            events: vec![],
            return_reasons: vec![],
            stopped: false,
            effects_settled: false,
            awaiting_continuation: false,
            continuation_withheld: false,
            cancellation: None,
            segment,
            watched,
        })
    }

    pub fn require_return(&mut self, reason: String) {
        if !self.return_reasons.contains(&reason) {
            self.return_reasons.push(reason);
        }
    }

    pub fn observe(&mut self) -> Result<()> {
        let elapsed = now_ms()?.saturating_sub(self.started_ms);
        self.observed_elapsed_ms = self.observed_elapsed_ms.max(elapsed);
        if let Some(segment) = &self.segment
            && segment.elapsed_ms.is_some_and(|limit| elapsed >= limit)
        {
            self.require_return("Selected elapsed-time observation point reached".into());
        }
        let changed = self
            .watched
            .iter()
            .map(|(path, previous)| Ok((path, stamp(path)? != *previous)))
            .collect::<Result<Vec<_>>>()?;
        let reasons: Vec<_> = changed
            .into_iter()
            .filter(|(_, changed)| *changed)
            .map(|(path, _)| format!("Selected observation output changed: {}", path.display()))
            .collect();
        for reason in reasons {
            self.require_return(reason);
        }
        Ok(())
    }

    pub fn event(&mut self, event: Event) -> Result<bool> {
        if event.invocation_id != self.invocation_id {
            return Err("event has wrong invocation".into());
        }
        if let Some(previous) = self
            .events
            .iter()
            .find(|value| value.sequence == event.sequence)
        {
            return if *previous == event {
                Ok(false)
            } else {
                Err("event sequence was reused with different content".into())
            };
        }
        if self.stopped && !matches!(event.event, EventKind::Reconciled { .. }) {
            return Err("stopped execution cannot emit new work events".into());
        }
        if event.sequence != self.events.len() as u64 + 1 {
            return Err("event sequence has a gap or is out of order".into());
        }
        match &event.event {
            EventKind::Usage { total } => {
                fn increasing(old: Option<u64>, new: Option<u64>) -> bool {
                    match (old, new) {
                        (Some(old), Some(new)) => new >= old,
                        (Some(_), None) => false,
                        _ => true,
                    }
                }
                if !increasing(self.usage.model_tokens, total.model_tokens)
                    || !increasing(self.usage.active_compute_ms, total.active_compute_ms)
                    || !increasing(self.usage.elapsed_ms, total.elapsed_ms)
                    || self.usage.spending.iter().any(|(currency, old)| {
                        !increasing(*old, total.spending.get(currency).copied().flatten())
                    })
                {
                    return Err(
                        "cumulative usage cannot decrease or erase known measurements".into(),
                    );
                }
                self.usage = total.clone();
                if self
                    .segment
                    .as_ref()
                    .and_then(|segment| segment.model_tokens)
                    .is_some_and(|limit| total.model_tokens.is_some_and(|used| used >= limit))
                {
                    self.require_return("Selected model-usage observation point reached".into());
                }
            }
            EventKind::Progress { summary, evidence } => {
                nonempty(summary, "progress meaning")?;
                for path in evidence {
                    if !path.is_absolute() || !path.is_file() {
                        return Err("progress evidence must exist at an absolute path".into());
                    }
                }
            }
            EventKind::Challenge { reason } => {
                nonempty(reason, "material challenge")?;
                self.require_return(reason.clone());
            }
            EventKind::Boundary {
                reason,
                return_due,
                effects_settled,
            } => {
                nonempty(reason, "boundary reason")?;
                if self.awaiting_continuation || self.continuation_withheld {
                    return Err("backend attempted another boundary without continuation".into());
                }
                self.awaiting_continuation = true;
                self.effects_settled = *effects_settled;
                if *return_due {
                    self.require_return(reason.clone());
                }
            }
            EventKind::Stopped { effects_settled } => {
                self.stopped = true;
                self.effects_settled = *effects_settled;
                self.awaiting_continuation = false;
            }
            EventKind::Reconciled { summary, evidence } => {
                if !self.stopped || self.effects_settled {
                    return Err("only stopped unresolved effects need reconciliation".into());
                }
                nonempty(summary, "effect reconciliation")?;
                if evidence.is_empty()
                    || evidence
                        .iter()
                        .any(|path| !path.is_absolute() || !path.is_file())
                {
                    return Err("effect reconciliation requires existing native evidence".into());
                }
                self.effects_settled = true;
            }
        }
        self.events.push(event);
        self.observe()?;
        Ok(true)
    }

    pub fn continuation(&mut self) -> Result<Continuation> {
        if !self.awaiting_continuation || self.stopped {
            return Err("backend is not waiting at a continuation boundary".into());
        }
        self.observe()?;
        if !self.effects_settled {
            self.require_return(
                "Effects remain unresolved; reconcile without starting more work".into(),
            );
        }
        self.awaiting_continuation = false;
        if self.return_reasons.is_empty() {
            Ok(Continuation::Continue)
        } else {
            self.continuation_withheld = true;
            Ok(Continuation::Return {
                reasons: self.return_reasons.clone(),
            })
        }
    }

    /// Check a new tool dispatch without asserting that earlier effects settled.
    /// This does not satisfy the idle handshake of a stream backend.
    pub fn check_action(&mut self) -> Result<Continuation> {
        self.observe()?;
        if self.stopped || self.awaiting_continuation {
            return Err("execution is stopped or still awaiting its idle handshake".into());
        }
        if self.continuation_withheld || !self.return_reasons.is_empty() {
            self.continuation_withheld = true;
            Ok(Continuation::Return {
                reasons: self.return_reasons.clone(),
            })
        } else {
            Ok(Continuation::Continue)
        }
    }
}
