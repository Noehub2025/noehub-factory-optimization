"""Result publication must preserve the meaning of an adopted continuing grant."""

import copy

import pytest

from test_validate_batch_result import MODULE, write_project_dispatch_fixture


@pytest.mark.parametrize("family,stage,uppercase_plan", [
    ("current", "spend-readiness", False),
    ("current", "spend-readiness", True),
    ("current", "authorization-readiness", False),
    ("legacy", "authorization-readiness", False),
])
def test_readiness_dispatch_round_trip(tmp_path, family, stage, uppercase_plan):
    packet, result, _ = write_project_dispatch_fixture(tmp_path, family, entry_stage=stage, uppercase_plan=uppercase_plan)
    draft = MODULE.validate(result, "draft", packet, repo_root=tmp_path, check_dispatch=True)
    assert draft["result_structure_ready"], draft["findings"]
    frozen = copy.deepcopy(result)
    frozen["result_packet_id"] = draft["computed_result_packet_id"]
    assert MODULE.validate(frozen, "frozen", packet, repo_root=tmp_path, check_dispatch=True) == draft


@pytest.mark.parametrize("options,expected", [
    ({"missing_basis": True}, "adopted continuing authorization"),
    ({"entry_result": "AUTHORIZATION_READY"}, "does not match spend-readiness"),
    ({"entry_stage": "authorization-readiness", "entry_result": "ENTRY_READY"}, "does not match authorization-readiness"),
    ({"report_change": "decision_root"}, "exact reviewed decision"),
    ({"report_change": "review_id"}, "exact reviewed decision"),
    ({"report_change": "review_result"}, "exact reviewed decision"),
    ({"report_change": "not-attested"}, "attested review content"),
])
@pytest.mark.parametrize("phase", ["draft", "frozen"])
def test_readiness_dispatch_rejects_missing_or_mismatched_proof(tmp_path, options, expected, phase):
    options = {"entry_stage": "spend-readiness", **options}
    packet, result, _ = write_project_dispatch_fixture(tmp_path, "current", **options)
    if phase == "frozen":
        import hashlib
        result["result_packet_id"] = MODULE.computed_result_id(
            result, hashlib.sha256(MODULE.canonical_payload(result)).hexdigest()
        )
    validation = MODULE.validate(result, phase, packet, repo_root=tmp_path, check_dispatch=True)
    assert not validation["result_structure_ready"]
    assert any(expected in item["detail"] for item in validation["findings"]), validation["findings"]
