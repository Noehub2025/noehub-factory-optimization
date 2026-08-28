#!/usr/bin/env python3
"""Focused tests for evaluation-source identity bindings."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from evaluation_target_contract import validate_experiment_source
from validate_batch_result import validate_evaluation_target_sources


def identified_source(
    field: str,
    prefix: str,
    payload: bytes = b"mode: diagnostic\n",
) -> tuple[bytes, str]:
    rule = (
        f"identity_rule: {prefix.removesuffix(':')} of exact UTF-8 bytes "
        f"with the complete {field} line omitted\n"
    ).encode()
    remaining = rule + payload
    identity = prefix + hashlib.sha256(remaining).hexdigest()
    return f"{field}: {identity}\n".encode() + remaining, identity


class EvaluationSourceIdentityTests(unittest.TestCase):
    def validate_source(
        self,
        raw: bytes,
        declared_id: str,
        *,
        expected_sha256: str | None = None,
    ) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        validate_experiment_source(
            {
                "path": "entry/source.yaml",
                "experiment_id": declared_id,
                "file_sha256": expected_sha256 or hashlib.sha256(raw).hexdigest(),
            },
            logical_name="entry/source.yaml",
            raw=raw,
            findings=findings,
        )
        return findings

    def assert_identity_rejected(self, findings: list[dict[str, str]]) -> None:
        self.assertIn(
            "EXPERIMENT_IDENTITY_MISMATCH",
            {finding["code"] for finding in findings},
        )

    def test_standard_identity_field_passes(self) -> None:
        raw, identity = identified_source(
            "experiment_id", "B900-experiment-sha256:"
        )
        self.assertEqual(self.validate_source(raw, identity), [])

    def test_descriptive_identity_field_passes_end_to_end(self) -> None:
        raw, identity = identified_source("matrix_id", "B900-matrix-sha256:")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "entry/state-matrix.yaml"
            source.parent.mkdir(parents=True)
            source.write_bytes(raw)
            target = {
                "mode": "diagnostic-only",
                "experiment": {
                    "path": "entry/state-matrix.yaml",
                    "experiment_id": identity,
                    "file_sha256": hashlib.sha256(raw).hexdigest(),
                },
            }
            findings: list[dict[str, str]] = []
            validate_evaluation_target_sources(
                {"evaluation_target": target}, root, findings
            )
        self.assertEqual(findings, [])

    def test_rule_does_not_guess_another_equal_valued_field(self) -> None:
        raw, identity = identified_source("matrix_id", "B900-matrix-sha256:")
        raw = raw.replace(
            b"with the complete matrix_id line omitted",
            b"with the complete missing_id line omitted",
            1,
        ) + f"experiment_id: {identity}\n".encode()
        self.assert_identity_rejected(self.validate_source(raw, identity))

    def test_duplicate_declared_identity_field_is_rejected(self) -> None:
        raw, identity = identified_source("matrix_id", "B900-matrix-sha256:")
        raw = f"matrix_id: {identity}\n".encode() + raw
        self.assert_identity_rejected(self.validate_source(raw, identity))

    def test_byte_derived_identity_mismatch_is_rejected(self) -> None:
        raw, identity = identified_source("matrix_id", "B900-matrix-sha256:")
        raw += b"changed: true\n"
        self.assert_identity_rejected(self.validate_source(raw, identity))

    def test_file_digest_mismatch_is_rejected(self) -> None:
        raw, identity = identified_source("matrix_id", "B900-matrix-sha256:")
        self.assert_identity_rejected(
            self.validate_source(raw, identity, expected_sha256="0" * 64)
        )


if __name__ == "__main__":
    unittest.main()
