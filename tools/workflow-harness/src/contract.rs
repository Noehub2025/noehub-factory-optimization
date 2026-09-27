//! Research inputs and cost accounting, independent of any Agent host.
//! Validation checks delivery and shape, never scientific value or truth.

use crate::{Result, Role, Task};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use std::path::PathBuf;

#[derive(Clone, Debug, Default, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct Usage {
    pub elapsed_ms: Option<u64>,
    pub model_tokens: Option<u64>,
    pub active_compute_ms: Option<u64>,
    /// Values are currency minor units; different currencies are never combined.
    #[serde(default)]
    pub spending: BTreeMap<String, Option<u64>>,
}

impl Usage {
    /// A missing measurement stays unknown, including after known measurements.
    pub fn plus(&self, other: &Self) -> Result<Self> {
        fn add(a: Option<u64>, b: Option<u64>) -> Result<Option<u64>> {
            match (a, b) {
                (Some(a), Some(b)) => a.checked_add(b).map(Some).ok_or("usage overflow".into()),
                _ => Ok(None),
            }
        }
        let mut spending = BTreeMap::new();
        for key in self.spending.keys().chain(other.spending.keys()) {
            spending.insert(
                key.clone(),
                add(
                    self.spending.get(key).copied().flatten(),
                    other.spending.get(key).copied().flatten(),
                )?,
            );
        }
        Ok(Self {
            elapsed_ms: add(self.elapsed_ms, other.elapsed_ms)?,
            model_tokens: add(self.model_tokens, other.model_tokens)?,
            active_compute_ms: add(self.active_compute_ms, other.active_compute_ms)?,
            spending,
        })
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct WorkItem {
    pub work: String,
    pub estimate: Usage,
    /// Nonempty means this is conditional later work, excluded from immediate cost.
    #[serde(default)]
    pub condition: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Prerequisite {
    pub reason: String,
    /// Index of a supplied source, not an unverified claim that a source was read.
    pub source: usize,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct OptionPlan {
    pub name: String,
    pub question: String,
    pub mechanism: String,
    pub useful_result: String,
    pub work: Vec<WorkItem>,
    #[serde(default)]
    pub prerequisites: Vec<Prerequisite>,
}

impl OptionPlan {
    pub fn immediate_cost(&self) -> Result<Option<Usage>> {
        let mut total: Option<Usage> = None;
        for item in self
            .work
            .iter()
            .filter(|item| item.condition.trim().is_empty())
        {
            total = Some(match total {
                None => item.estimate.clone(),
                Some(total) => total.plus(&item.estimate)?,
            });
        }
        Ok(total)
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RoleContract {
    pub role: Role,
    pub method_source: usize,
    pub required_purposes: Vec<String>,
    pub write_scope: String,
    pub fresh_context: bool,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Research {
    pub question: String,
    pub missing_observation: String,
    pub rationale: String,
    pub remaining_work: Vec<WorkItem>,
    #[serde(default)]
    pub alternatives: Vec<OptionPlan>,
    pub roles: Vec<RoleContract>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Segment {
    pub observation: String,
    pub return_when: String,
    /// Optional observation signals, not universal time or token budgets.
    pub elapsed_ms: Option<u64>,
    pub model_tokens: Option<u64>,
    #[serde(default)]
    pub return_on_change: Vec<PathBuf>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct WorkUpdate {
    /// Invocations whose return conditions were addressed in this adoption.
    #[serde(default)]
    pub addresses: Vec<usize>,
    pub remaining_work: Vec<WorkItem>,
    pub interpretation: String,
    #[serde(default)]
    pub options: Vec<OptionPlan>,
    #[serde(default)]
    pub selected: String,
    #[serde(default)]
    pub rationale: String,
    #[serde(default)]
    pub reverse_when: String,
    pub segment: Option<Segment>,
    /// An already applicable resolution can avoid a redundant resolver call.
    #[serde(default)]
    pub resolved_by: Vec<usize>,
    /// Existing investment trigger; prose edits and ordinary progress leave this false.
    #[serde(default)]
    pub investment_changed: bool,
    /// Reuse an accepted Resolver invocation, rather than requesting another judgment.
    #[serde(default)]
    pub resolved_invocation: Option<usize>,
}

pub fn nonempty(value: &str, name: &str) -> Result<()> {
    if value.trim().is_empty() {
        Err(format!("{name} must not be empty"))
    } else {
        Ok(())
    }
}

fn validate_work(work: &[WorkItem]) -> Result<()> {
    for item in work {
        nonempty(&item.work, "remaining work")?;
    }
    Ok(())
}

pub fn validate_options(options: &[OptionPlan], task: &Task, role: Role) -> Result<()> {
    let mut names = BTreeSet::new();
    for option in options {
        for value in [
            &option.name,
            &option.question,
            &option.mechanism,
            &option.useful_result,
        ] {
            nonempty(value, "option input")?;
        }
        if !names.insert(&option.name) {
            return Err("option names must be unique".into());
        }
        validate_work(&option.work)?;
        if !option
            .work
            .iter()
            .any(|item| item.condition.trim().is_empty())
        {
            return Err("each option needs its next sufficient immediate work".into());
        }
        for prerequisite in &option.prerequisites {
            nonempty(&prerequisite.reason, "prerequisite reason")?;
            supplied(task, prerequisite.source, role)?;
        }
        option.immediate_cost()?;
    }
    Ok(())
}

pub fn supplied(task: &Task, index: usize, role: Role) -> Result<()> {
    if task
        .sources
        .get(index)
        .is_some_and(|source| source.roles.contains(&role))
    {
        Ok(())
    } else {
        Err("decision source must be supplied to the receiving role".into())
    }
}

impl Research {
    pub fn validate(&self, task: &Task) -> Result<()> {
        for value in [&self.question, &self.missing_observation, &self.rationale] {
            nonempty(value, "research input")?;
        }
        validate_work(&self.remaining_work)?;
        for role in [Role::Coordinator, Role::Resolver, Role::Worker] {
            let contracts: Vec<_> = self
                .roles
                .iter()
                .filter(|entry| entry.role == role)
                .collect();
            if contracts.len() != 1 {
                return Err("one input contract is required for each used role".into());
            }
            let contract = contracts[0];
            supplied(task, contract.method_source, role)?;
            nonempty(&contract.write_scope, "role write scope")?;
            for purpose in &contract.required_purposes {
                nonempty(purpose, "required input purpose")?;
                if !task
                    .sources
                    .iter()
                    .any(|source| source.purpose == *purpose && source.roles.contains(&role))
                {
                    return Err(format!("missing required input purpose: {purpose}"));
                }
            }
        }
        validate_options(&self.alternatives, task, Role::Resolver)
    }
}

impl WorkUpdate {
    pub fn validate(&self, task: &Task, role: Role, selecting_work: bool) -> Result<()> {
        nonempty(&self.interpretation, "outcome interpretation")?;
        validate_work(&self.remaining_work)?;
        validate_options(&self.options, task, role)?;
        for &source in &self.resolved_by {
            supplied(task, source, role)?;
        }
        if selecting_work {
            nonempty(&self.rationale, "continuation rationale")?;
            nonempty(&self.reverse_when, "reversal condition")?;
            let segment = self
                .segment
                .as_ref()
                .ok_or("selected work needs a return boundary")?;
            nonempty(&segment.observation, "next observation")?;
            nonempty(&segment.return_when, "return condition")?;
            if segment.elapsed_ms == Some(0) || segment.model_tokens == Some(0) {
                return Err("observation thresholds must be positive when selected".into());
            }
            for path in &segment.return_on_change {
                if !path.is_absolute() {
                    return Err("watched observation paths must be absolute".into());
                }
            }
            if !self.options.is_empty()
                && !self
                    .options
                    .iter()
                    .any(|option| option.name == self.selected)
            {
                return Err("selected option is missing from the comparison".into());
            }
            if role == Role::Resolver && self.options.is_empty() {
                return Err("resolver must return the affected comparison".into());
            }
        }
        Ok(())
    }
}
