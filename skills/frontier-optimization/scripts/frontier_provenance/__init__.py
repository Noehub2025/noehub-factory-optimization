"""Task- and technology-neutral legacy Frontier provenance interface.

Imports stay lazy so current workflow validation does not load the historical
execution and identity stack. Existing callers keep the same public names.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from .content import (
    CONTENT_CONTRACT,
    CONTENT_ROOT_PREFIX,
    ProvenanceError,
    artifact_entry,
    build_manifest,
    verify_manifest,
)

_LAZY_EXPORTS = {
    "attest": (".facade", "attest"),
    "bind_authority": (".facade", "bind_authority"),
    "export_chain": (".facade", "export_chain"),
    "freeze_decision": (".facade", "freeze_decision"),
    "freeze_execution": (".facade", "freeze_execution"),
    "record_outcome": (".facade", "record_outcome"),
    "verify_for": (".facade", "verify_for"),
    "NODE_CONTRACT": (".graph", "NODE_CONTRACT"),
    "verify_chain": (".graph", "verify_chain"),
    "verify_node": (".graph", "verify_node"),
    "NodeRepository": (".repository", "NodeRepository"),
    "SlotConsumptionIndex": (".repository", "SlotConsumptionIndex"),
}


def __getattr__(name: str) -> Any:
    binding = _LAZY_EXPORTS.get(name)
    if binding is None:
        raise AttributeError(name)
    module_name, attribute = binding
    value = getattr(import_module(module_name, __name__), attribute)
    globals()[name] = value
    return value

__all__ = [
    "CONTENT_CONTRACT",
    "CONTENT_ROOT_PREFIX",
    "NODE_CONTRACT",
    "NodeRepository",
    "SlotConsumptionIndex",
    "ProvenanceError",
    "artifact_entry",
    "attest",
    "bind_authority",
    "build_manifest",
    "export_chain",
    "freeze_decision",
    "freeze_execution",
    "record_outcome",
    "verify_chain",
    "verify_for",
    "verify_manifest",
    "verify_node",
]
