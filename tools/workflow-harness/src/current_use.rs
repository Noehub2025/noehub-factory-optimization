//! Optional current-use bindings supplied by the existing owner checker.
//! This module verifies retained identity and saved bytes, not semantic correctness.

use crate::{Result, contract::nonempty};
use serde::{Deserialize, Serialize};
use std::{fs, path::PathBuf};

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct CurrentUse {
    pub owner: PathBuf,
    /// Keep resolved and advisory references too, so transfer cannot erase history.
    pub correction_ids: Vec<String>,
    /// The existing owner checker determines which confirmed findings affect this use.
    pub blocked_ids: Vec<String>,
    pub files: Vec<SavedFile>,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct SavedFile {
    pub path: PathBuf,
    pub contents: String,
}

impl CurrentUse {
    /// Capture only after the existing owner checker has validated current adoption.
    /// A caller's status label is not a substitute for that owner operation.
    pub fn capture(
        owner: PathBuf,
        affected_sources: Vec<PathBuf>,
        correction_ids: Vec<String>,
        blocked_ids: Vec<String>,
    ) -> Result<Self> {
        let mut files = Vec::new();
        for path in std::iter::once(owner.clone()).chain(affected_sources) {
            if !path.is_absolute() {
                return Err("current-use paths must be absolute".into());
            }
            let contents = fs::read_to_string(&path).map_err(|e| e.to_string())?;
            files.push(SavedFile { path, contents });
        }
        let binding = Self {
            owner,
            correction_ids,
            blocked_ids,
            files,
        };
        binding.verify_shape()?;
        Ok(binding)
    }

    fn verify_shape(&self) -> Result<()> {
        if !self.owner.is_absolute() || !self.files.iter().any(|file| file.path == self.owner) {
            return Err("current-use binding must include its saved absolute owner".into());
        }
        for id in &self.correction_ids {
            nonempty(id, "finding reference")?;
        }
        if self
            .blocked_ids
            .iter()
            .any(|id| !self.correction_ids.contains(id))
        {
            return Err("blocking finding must remain associated with current use".into());
        }
        Ok(())
    }

    pub fn verify_saved(&self) -> Result<()> {
        self.verify_shape()?;
        for saved in &self.files {
            let path = &saved.path;
            if !path.is_absolute()
                || fs::read_to_string(path).ok().as_ref() != Some(&saved.contents)
            {
                return Err(format!(
                    "current-use source changed; return to its owner: {}",
                    path.display()
                ));
            }
        }
        Ok(())
    }

    pub fn require_ready(&self) -> Result<()> {
        self.verify_saved()?;
        if !self.blocked_ids.is_empty() {
            return Err("known current-use correction remains unresolved; return affected work to its owner".into());
        }
        Ok(())
    }

    pub fn carries(&self, previous: &Self) -> Result<()> {
        if previous
            .correction_ids
            .iter()
            .any(|id| !self.correction_ids.contains(id))
        {
            return Err(
                "current-use replacement or transfer dropped a retained finding association".into(),
            );
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
pub(crate) struct Bindings {
    pub adopted: Option<CurrentUse>,
    pub queued: Option<(usize, CurrentUse)>,
}
