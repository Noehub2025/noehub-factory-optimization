"""Task- and technology-neutral Frontier provenance interface."""

from .content import (
    CONTENT_CONTRACT,
    CONTENT_ROOT_PREFIX,
    ProvenanceError,
    artifact_entry,
    build_manifest,
    verify_manifest,
)
from .facade import (
    attest,
    bind_authority,
    export_chain,
    freeze_decision,
    freeze_execution,
    record_outcome,
    verify_for,
)
from .graph import NODE_CONTRACT, verify_chain, verify_node
from .repository import NodeRepository, SlotConsumptionIndex

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
