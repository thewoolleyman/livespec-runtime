"""Tests for `livespec_runtime.spec_governance`."""

import json
from pathlib import Path
from typing import Any

import pytest
from returns.result import Failure, Success

from livespec_runtime import spec_governance
from livespec_runtime.spec_governance import (
    BlockDrift,
    documented_defaults,
    manifest_rows,
    verify_default_block,
    verify_livespec_jsonc_default_block,
)

__all__: list[str] = []


def test_manifest_hosts_current_spec_governance_keys() -> None:
    assert [row.key for row in manifest_rows()] == [
        "propose_change_mode",
        "critique_mode",
        "in_flight_alignment",
        "doctor_dispositions",
        "revise_decision_mode",
        "drift_acceptance_mode",
        "ratification_review",
        "ratification_reviewer_model",
        "ratification_min_review_age_seconds",
        "spec_pr_merge",
    ]


def test_documented_defaults_uses_self_delimiting_brace_balance_parse() -> None:
    assert documented_defaults(text=_livespec_jsonc_text()) == _expected_defaults()


def test_correct_commented_default_block_verifies_ok(tmp_path: Path) -> None:
    source_path = tmp_path / ".livespec.jsonc"
    _ = source_path.write_text(_livespec_jsonc_text(), encoding="utf-8")

    result = verify_livespec_jsonc_default_block(path=source_path)

    assert isinstance(result, Success)
    assert result.unwrap() == {
        "check_id": "spec-governance-default-block-ok",
        "path": str(source_path),
        "key_count": len(manifest_rows()),
    }


def test_negative_control_deleted_key_reports_missing_key(tmp_path: Path) -> None:
    source_path = tmp_path / ".livespec.jsonc"
    _ = source_path.write_text(
        _livespec_jsonc_text().replace(
            '  //   "ratification_reviewer_model": null,\n',
            "",
        ),
        encoding="utf-8",
    )

    result = verify_livespec_jsonc_default_block(path=source_path)

    assert isinstance(result, Failure)
    assert result.failure() == json.dumps(
        {
            "check_id": "spec-governance-default-block-drift",
            "path": str(source_path),
            "missing": ["ratification_reviewer_model"],
            "extra": [],
            "default_drift": [],
            "hint": (
                "Update the commented spec_governance block so it lists every "
                "installed core manifest key at its safe default, or run with no "
                "block if this repo does not intentionally carry the documentation."
            ),
        },
        sort_keys=True,
    )


def test_verify_default_block_matches_core_projection_on_drift() -> None:
    verification = verify_default_block(
        text=_livespec_jsonc_text().replace(
            '  //   "revise_decision_mode": "manual",\n',
            '  //   "revise_decision_mode": "delegated",\n',
        ),
        manifest=manifest_rows(),
    )

    assert verification.drift == BlockDrift(
        missing=[],
        extra=[],
        default_drift=["revise_decision_mode"],
    )


def test_missing_commented_block_reports_every_manifest_key_missing() -> None:
    verification = verify_default_block(text="{}", manifest=manifest_rows())

    assert verification.drift == BlockDrift(
        missing=sorted(row.key for row in manifest_rows()),
        extra=[],
        default_drift=[],
    )


def test_empty_and_non_object_spec_governance_blocks_are_absent() -> None:
    assert (
        documented_defaults(
            text="""{
  // Optional — spec_governance:
  // "spec_governance": {}
}
"""
        )
        is None
    )
    assert (
        documented_defaults(
            text="""{
  // Optional — spec_governance:
  // "spec_governance": null
}
"""
        )
        is None
    )


def test_unterminated_commented_block_raises_structural_error() -> None:
    assert hasattr(spec_governance, "UnterminatedGovernanceBlockError")
    error_type = spec_governance.UnterminatedGovernanceBlockError
    assert isinstance(error_type, type)
    assert issubclass(error_type, Exception)

    with pytest.raises(
        error_type,
        match="unterminated spec_governance comment block",
    ):
        documented_defaults(
            text="""{
  // Optional — spec_governance:
  // // generated comment
  // "spec_governance": {
  //   "propose_change_mode": "interactive"
"""
        )


def test_no_commented_block_is_absent() -> None:
    assert documented_defaults(text="{}") is None


def test_malformed_json_inside_balanced_block_still_raises_json_decode_error() -> None:
    with pytest.raises(json.JSONDecodeError):
        documented_defaults(
            text="""{
  // Optional — spec_governance:
  // "spec_governance": {
  //   "propose_change_mode": "interactive",
  // }
}
"""
        )


def test_parser_ignores_non_comment_lines_inside_balanced_block() -> None:
    text = _livespec_jsonc_text().replace(
        '  //   "doctor_dispositions": {},\n',
        '  //   "doctor_dispositions": {},\n  "uncommented": "ignored",\n',
    )

    assert documented_defaults(text=text) == _expected_defaults()


def test_braces_and_escaped_quotes_inside_strings_do_not_close_block() -> None:
    text = _livespec_jsonc_text().replace(
        '  //   "spec_pr_merge": "manual"\n',
        "".join(
            [
                '  //   "spec_pr_merge": "manual",\n',
                '  //   "extra_documented_key": "c:\\\\tmp { } still string"\n',
            ]
        ),
    )

    verification = verify_default_block(text=text, manifest=manifest_rows())

    assert verification.drift == BlockDrift(
        missing=[],
        extra=["extra_documented_key"],
        default_drift=[],
    )


def test_missing_source_reports_core_equivalent_message(tmp_path: Path) -> None:
    source_path = tmp_path / ".livespec.jsonc"

    result = verify_livespec_jsonc_default_block(path=source_path)

    assert isinstance(result, Failure)
    assert result.failure() == (
        "spec-governance-default-block-missing-source: "
        f"default-block source not found: {source_path}"
    )


def test_module_exposes_stable_public_entry_point() -> None:
    assert hasattr(spec_governance, "verify_livespec_jsonc_default_block")


def _expected_defaults() -> dict[str, Any]:
    return {row.key: row.safe_default for row in manifest_rows()}


def _livespec_jsonc_text() -> str:
    return """{
  // Optional — spec_governance:
  // "spec_governance": {
  //   "propose_change_mode": "interactive",
  //   "critique_mode": "interactive",
  //   "in_flight_alignment": "prompt",
  //   "doctor_dispositions": {},
  //   "revise_decision_mode": "manual",
  //   "drift_acceptance_mode": "human",
  //   "ratification_review": "manual-spawn",
  //   "ratification_reviewer_model": null,
  //   "ratification_min_review_age_seconds": 1,
  //   "spec_pr_merge": "manual"
  // }
  // Optional — credential_wrapper:
  "required_secret_env": []
}
"""
