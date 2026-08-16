#!/usr/bin/env python3
"""Validate and derive exact reviewed post-adoption repository state."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Callable


CONTRACT_VERSION = "frontier-post-adoption-state/1"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
CONTRACT_FIELDS = {"contract_version", "files"}
FILE_FIELDS = {"path", "pre_sha256", "post_source"}
POST_SOURCE_FIELDS = {"path", "file_sha256"}


class PostAdoptionStateError(ValueError):
    """Raised when reviewed post-adoption state cannot be derived exactly."""


@dataclass(frozen=True)
class ReviewedFileState:
    path: str
    pre_sha256: str
    post_source_path: str
    post_sha256: str
    post_bytes: bytes


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require_exact_fields(value: dict[str, Any], expected: set[str], field: str) -> None:
    observed = set(value)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise PostAdoptionStateError(
            f"{field} fields differ: missing={missing}, unsupported={extra}"
        )


def load_reviewed_files(
    contract: Any,
    *,
    read_source: Callable[[str], bytes],
    pre_sha256_for: Callable[[str], str],
) -> list[ReviewedFileState]:
    """Return exact reviewed file states after validating every source binding."""
    if not isinstance(contract, dict):
        raise PostAdoptionStateError("post_adoption_state must be a mapping")
    require_exact_fields(contract, CONTRACT_FIELDS, "post_adoption_state")
    if contract.get("contract_version") != CONTRACT_VERSION:
        raise PostAdoptionStateError(
            f"post_adoption_state.contract_version must be {CONTRACT_VERSION}"
        )
    files = contract.get("files")
    if not isinstance(files, list):
        raise PostAdoptionStateError("post_adoption_state.files must be a list")

    reviewed: list[ReviewedFileState] = []
    seen_paths: set[str] = set()
    for index, item in enumerate(files):
        field = f"post_adoption_state.files[{index}]"
        if not isinstance(item, dict):
            raise PostAdoptionStateError(f"{field} must be a mapping")
        require_exact_fields(item, FILE_FIELDS, field)
        path = item.get("path")
        pre_sha256 = item.get("pre_sha256")
        post_source = item.get("post_source")
        if not isinstance(path, str) or not path:
            raise PostAdoptionStateError(f"{field}.path must be a nonempty path")
        if path in seen_paths:
            raise PostAdoptionStateError(f"duplicate post-adoption path: {path}")
        seen_paths.add(path)
        if not isinstance(pre_sha256, str) or not SHA256_PATTERN.fullmatch(pre_sha256):
            raise PostAdoptionStateError(
                f"{field}.pre_sha256 must be a lowercase SHA-256"
            )
        if not isinstance(post_source, dict):
            raise PostAdoptionStateError(f"{field}.post_source must be a mapping")
        require_exact_fields(post_source, POST_SOURCE_FIELDS, f"{field}.post_source")
        post_source_path = post_source.get("path")
        declared_post_sha256 = post_source.get("file_sha256")
        if not isinstance(post_source_path, str) or not post_source_path:
            raise PostAdoptionStateError(
                f"{field}.post_source.path must be a nonempty path"
            )
        if post_source_path == path:
            raise PostAdoptionStateError(
                f"{field}.post_source.path must differ from the live target path"
            )
        if (
            not isinstance(declared_post_sha256, str)
            or not SHA256_PATTERN.fullmatch(declared_post_sha256)
        ):
            raise PostAdoptionStateError(
                f"{field}.post_source.file_sha256 must be a lowercase SHA-256"
            )
        observed_pre_sha256 = pre_sha256_for(path)
        if observed_pre_sha256 != pre_sha256:
            raise PostAdoptionStateError(
                f"{field}.pre_sha256 expected {pre_sha256}, observed {observed_pre_sha256}"
            )
        post_bytes = read_source(post_source_path)
        observed_post_sha256 = sha256_bytes(post_bytes)
        if observed_post_sha256 != declared_post_sha256:
            raise PostAdoptionStateError(
                f"{field}.post_source expected {declared_post_sha256}, observed {observed_post_sha256}"
            )
        reviewed.append(
            ReviewedFileState(
                path=path,
                pre_sha256=pre_sha256,
                post_source_path=post_source_path,
                post_sha256=observed_post_sha256,
                post_bytes=post_bytes,
            )
        )
    return reviewed


def expected_receipt(
    files: list[ReviewedFileState],
    *,
    target_id: str,
    adoption_id: str,
    user_result_id: str,
) -> dict[str, Any]:
    """Build the only receipt accepted for the reviewed transition."""
    return {
        "contract_version": CONTRACT_VERSION,
        "target_id": target_id,
        "adoption_id": adoption_id,
        "user_result_id": user_result_id,
        "files": [
            {
                "path": item.path,
                "pre_sha256": item.pre_sha256,
                "post_sha256": item.post_sha256,
            }
            for item in files
        ],
    }
