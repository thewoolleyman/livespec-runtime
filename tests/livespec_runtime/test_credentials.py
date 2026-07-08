"""Tests for `livespec_runtime.credentials`.

Verifies the pure `decide_credentials` self-heal brain (design §1) across
its four decision branches — present -> `Proceed`; missing + no sentinel +
wrapper -> `Reexec` with the exact wrapper-prefixed argv; missing +
sentinel -> `Fail`; missing + no wrapper -> `Fail` — plus the frozen
discriminated-union variants and Hypothesis property coverage on the
present-always-proceeds and missing-always-reexecs invariants.

Design reference: livespec/plan/credential-wrapper/research/01-design.md §1.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from livespec_runtime import credentials
from livespec_runtime.credentials import (
    CREDENTIAL_REEXEC_SENTINEL,
    Fail,
    Proceed,
    Reexec,
    decide_credentials,
)

__all__: list[str] = []


def test_credential_reexec_sentinel_value() -> None:
    assert CREDENTIAL_REEXEC_SENTINEL == "LIVESPEC_CREDENTIAL_REEXEC"


def test_all_present_returns_proceed() -> None:
    decision = decide_credentials(
        required=["BEADS_DOLT_PASSWORD", "GH_TOKEN"],
        credential_wrapper=["/usr/local/bin/with-livespec-env.sh", "--"],
        environ={"BEADS_DOLT_PASSWORD": "secret", "GH_TOKEN": "ghp_x"},
        executable="/usr/bin/python3",
        argv=["/plugin/bin/next.py", "--json"],
    )
    assert isinstance(decision, Proceed)
    assert decision.kind == "proceed"


def test_missing_without_sentinel_with_wrapper_returns_reexec_exact_argv() -> None:
    decision = decide_credentials(
        required=["BEADS_DOLT_PASSWORD"],
        credential_wrapper=["/usr/local/bin/with-livespec-env.sh", "--"],
        environ={},
        executable="/usr/bin/python3",
        argv=["/plugin/bin/next.py", "--json"],
    )
    assert isinstance(decision, Reexec)
    assert decision.kind == "reexec"
    assert decision.argv == (
        "/usr/local/bin/with-livespec-env.sh",
        "--",
        "/usr/bin/python3",
        "/plugin/bin/next.py",
        "--json",
    )


def test_empty_string_value_treated_as_missing_triggers_reexec() -> None:
    decision = decide_credentials(
        required=["BEADS_DOLT_PASSWORD"],
        credential_wrapper=["env"],
        environ={"BEADS_DOLT_PASSWORD": ""},
        executable="/usr/bin/python3",
        argv=["/plugin/bin/next.py"],
    )
    assert isinstance(decision, Reexec)
    assert decision.argv == ("env", "/usr/bin/python3", "/plugin/bin/next.py")


def test_missing_with_sentinel_returns_fail() -> None:
    decision = decide_credentials(
        required=["BEADS_DOLT_PASSWORD"],
        credential_wrapper=["/usr/local/bin/with-livespec-env.sh", "--"],
        environ={CREDENTIAL_REEXEC_SENTINEL: "1"},
        executable="/usr/bin/python3",
        argv=["/plugin/bin/next.py"],
    )
    assert isinstance(decision, Fail)
    assert decision.kind == "fail"
    assert "BEADS_DOLT_PASSWORD" in decision.message
    assert "even after re-exec" in decision.message
    assert "with-livespec-env.sh" in decision.message


def test_missing_without_wrapper_returns_fail() -> None:
    decision = decide_credentials(
        required=["BEADS_DOLT_PASSWORD"],
        credential_wrapper=[],
        environ={},
        executable="/usr/bin/python3",
        argv=["/plugin/bin/next.py"],
    )
    assert isinstance(decision, Fail)
    assert "BEADS_DOLT_PASSWORD" in decision.message
    assert "no credential_wrapper configured in .livespec.jsonc" in decision.message


def test_wrapper_launch_failure_message_is_actionable() -> None:
    assert hasattr(credentials, "wrapper_launch_failure")

    decision = credentials.wrapper_launch_failure(
        required=["BEADS_DOLT_PASSWORD", "GH_TOKEN"],
        credential_wrapper=["credential_wrapper", "--profile", "livespec"],
    )

    assert isinstance(decision, Fail)
    assert decision.kind == "fail"
    assert "credential_wrapper could not run in this environment" in decision.message
    assert "sandbox" in decision.message
    assert "sudo" in decision.message
    assert "no_new_privs" in decision.message
    assert "BEADS_DOLT_PASSWORD" in decision.message
    assert "GH_TOKEN" in decision.message
    assert "already present" in decision.message
    assert "--dangerously-bypass-approvals-and-sandbox" in decision.message


def test_proceed_variant_is_frozen() -> None:
    decision = Proceed()
    with pytest.raises(AttributeError):
        decision.kind = "reexec"  # type: ignore[misc]


def test_reexec_variant_is_frozen() -> None:
    decision = Reexec(argv=("env", "python"))
    with pytest.raises(AttributeError):
        decision.argv = ()  # type: ignore[misc]


def test_fail_variant_is_frozen() -> None:
    decision = Fail(message="boom")
    with pytest.raises(AttributeError):
        decision.message = "other"  # type: ignore[misc]


@settings(deadline=None)
@given(
    names=st.lists(st.text(min_size=1), min_size=1, max_size=5, unique=True),
    credential_wrapper=st.lists(st.text(min_size=1), max_size=4),
    executable=st.text(min_size=1),
    argv=st.lists(st.text(), max_size=4),
)
def test_all_present_always_proceeds(
    names: list[str],
    credential_wrapper: list[str],
    executable: str,
    argv: list[str],
) -> None:
    environ = {name: "present-value" for name in names}
    decision = decide_credentials(
        required=names,
        credential_wrapper=credential_wrapper,
        environ=environ,
        executable=executable,
        argv=argv,
    )
    assert isinstance(decision, Proceed)


@settings(deadline=None)
@given(
    missing_name=st.text(min_size=1),
    credential_wrapper=st.lists(st.text(min_size=1), min_size=1, max_size=4),
    executable=st.text(min_size=1),
    argv=st.lists(st.text(), max_size=4),
)
def test_missing_without_sentinel_reexecs_with_prefixed_argv(
    missing_name: str,
    credential_wrapper: list[str],
    executable: str,
    argv: list[str],
) -> None:
    decision = decide_credentials(
        required=[missing_name],
        credential_wrapper=credential_wrapper,
        environ={},
        executable=executable,
        argv=argv,
    )
    assert isinstance(decision, Reexec)
    assert decision.argv == (*credential_wrapper, executable, *argv)
