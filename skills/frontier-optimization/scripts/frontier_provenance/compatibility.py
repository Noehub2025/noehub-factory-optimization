"""Persisted rollout inventory for restricted historical completion."""

from __future__ import annotations

from typing import Any

from .content import ProvenanceError


V1_COMPLETION_CONTRACT = "frontier-v1-completion-inventory/1"


def require_v1_completion(
    inventory: dict[str, Any],
    *,
    authority_root: str,
    requested_descendant: str,
    scope_root: str,
    verified_parent_role: str,
) -> None:
    """Permit a descendant only when the rollout inventory names the old authority."""

    if not isinstance(inventory, dict) or set(inventory) != {
        "contract_version",
        "rollout_cutoff",
        "active_authorities",
    }:
        raise ProvenanceError("v1 rollout inventory has an invalid shape")
    if inventory["contract_version"] != V1_COMPLETION_CONTRACT:
        raise ProvenanceError("v1 rollout inventory contract is unsupported")
    records = inventory["active_authorities"]
    if not isinstance(records, list):
        raise ProvenanceError("v1 rollout active_authorities must be a list")
    matches = [
        record
        for record in records
        if isinstance(record, dict) and record.get("authority_root") == authority_root
    ]
    if len(matches) != 1:
        raise ProvenanceError("v1 authority is not active in the rollout inventory")
    record = matches[0]
    if set(record) != {"authority_root", "contract_version", "state", "scope_root"}:
        raise ProvenanceError("v1 authority inventory record has an invalid shape")
    if record["scope_root"] != scope_root:
        raise ProvenanceError("v1 completion scope differs from the rollout inventory")
    allowed = {
        "acknowledgment": ({"authorized"}, "authority"),
        "execution-start": ({"authorized", "acknowledged"}, "acknowledgment"),
        "blocked-outcome": ({"authorized", "acknowledged"}, "authority"),
        "outcome": (
            {"authorized", "acknowledged", "started", "waiting-for-input"},
            "execution",
        ),
    }
    states, parent_role = allowed.get(requested_descendant, (set(), ""))
    if record["state"] not in states or verified_parent_role != parent_role:
        raise ProvenanceError(
            "v1 compatibility permits only completion of an inventoried authority chain"
        )
    if not isinstance(record["contract_version"], str) or not record["contract_version"]:
        raise ProvenanceError("v1 completion version must come from the inventory")
