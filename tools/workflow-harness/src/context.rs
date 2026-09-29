//! Shared immutable evidence for selected delivery, not another authored store.
use crate::Result;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{
    fs,
    io::Write,
    path::{Path, PathBuf},
};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Snapshot {
    pub path: PathBuf,
    pub sha256: String,
}

fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

impl Snapshot {
    pub fn retain(directory: &Path, value: &impl Serialize) -> Result<Self> {
        let bytes = serde_json::to_vec(value).map_err(|e| e.to_string())?;
        let sha256 = digest(&bytes);
        fs::create_dir_all(directory).map_err(|e| e.to_string())?;
        let path = directory.join(format!("{sha256}.json"));
        if path.exists() {
            if fs::read(&path).map_err(|e| e.to_string())? != bytes {
                return Err("retained context evidence changed".into());
            }
        } else {
            let nonce = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .map_err(|e| e.to_string())?
                .as_nanos();
            let temporary = directory.join(format!(".{sha256}-{}-{nonce}.tmp", std::process::id()));
            let publish = (|| -> Result<()> {
                let mut file = fs::OpenOptions::new()
                    .write(true)
                    .create_new(true)
                    .open(&temporary)
                    .map_err(|e| e.to_string())?;
                file.write_all(&bytes).map_err(|e| e.to_string())?;
                file.sync_all().map_err(|e| e.to_string())?;
                // A complete object becomes visible at once; never overwrite a
                // previously published version, including a corrupted object.
                match fs::hard_link(&temporary, &path) {
                    Ok(()) => Ok(()),
                    Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => {
                        if fs::read(&path).map_err(|e| e.to_string())? == bytes {
                            Ok(())
                        } else {
                            Err("retained context evidence changed".into())
                        }
                    }
                    Err(e) => Err(e.to_string()),
                }
            })();
            let _ = fs::remove_file(temporary);
            publish?;
        }
        Ok(Self {
            path: fs::canonicalize(path).map_err(|e| e.to_string())?,
            sha256,
        })
    }

    pub fn read(&self) -> Result<Value> {
        let bytes = fs::read(&self.path).map_err(|e| e.to_string())?;
        if digest(&bytes) != self.sha256 {
            return Err("retained context evidence changed".into());
        }
        serde_json::from_slice(&bytes).map_err(|e| e.to_string())
    }

    /// Read only the selected object; do not load all historical evidence.
    pub fn expand(&self, pointer: &str) -> Result<Value> {
        let value = self.read()?;
        let mut pieces = pointer.trim_start_matches('/').splitn(3, '/');
        let group = pieces.next().unwrap_or("");
        if matches!(group, "returns" | "full_sources" | "by_invocation") {
            if let Some(index) = pieces.next() {
                let reference = if group == "by_invocation" {
                    let position = value["return_ids"][index]
                        .as_u64()
                        .ok_or("unknown accepted invocation")?
                        as usize;
                    value["returns"].get(position)
                } else {
                    value
                        .get(group)
                        .and_then(|v| v.get(index.parse::<usize>().ok()?))
                }
                .ok_or("unknown evidence index")?;
                let source: Self =
                    serde_json::from_value(reference.clone()).map_err(|e| e.to_string())?;
                let body = source.read()?;
                return match pieces.next() {
                    Some(rest) => body
                        .pointer(&format!("/{rest}"))
                        .cloned()
                        .ok_or("unknown evidence field".into()),
                    None => Ok(body),
                };
            }
        } else if group == "current_use" {
            if value[group].is_null() {
                return Ok(Value::Null);
            }
            let source: Self =
                serde_json::from_value(value[group].clone()).map_err(|e| e.to_string())?;
            let body = source.read()?;
            let rest = pointer.strip_prefix("/current_use").unwrap_or("");
            return body
                .pointer(rest)
                .cloned()
                .ok_or("unknown evidence field".into());
        }
        value
            .pointer(pointer)
            .cloned()
            .ok_or("unknown evidence JSON pointer".into())
    }
}
