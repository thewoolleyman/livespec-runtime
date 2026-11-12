"""Regression coverage for this repository's delegated pre-push wiring."""

from __future__ import annotations

import re
from pathlib import Path

from livespec_dev_tooling import check_purity
from returns.pipeline import is_successful
from returns.unsafe import unsafe_perform_io

_ROOT = Path(__file__).parent.parent
_DELEGATE_MODULE = "livespec_dev_tooling.gate_remote_delegate"
_CHECK_SCRIPT = _ROOT / ".github/scripts/check.sh"


_TAG_PIN = re.compile(r'^livespec-dev-tooling = \{[^}]*\btag = "v\d+\.\d+\.\d+"', re.MULTILINE)
_TARGET = re.compile(r"^    (check-[a-z0-9-]+)$", re.MULTILINE)


def _aggregate_targets() -> tuple[str, ...]:
    """Return the check aggregate's members in their declared execution order."""
    return tuple(_TARGET.findall(_CHECK_SCRIPT.read_text(encoding="utf-8")))


def _declares_delegated_gate(*, pyproject: str) -> bool:
    """Report whether the text pins a dev-tooling release tag and opts into the gate."""
    if _TAG_PIN.search(pyproject) is None:
        return False
    _, separator, tooling_block = pyproject.partition("[tool.livespec_dev_tooling]")
    return bool(separator) and "delegated_gate = true" in tooling_block


def _fixture_pyproject(*, source: str, tooling: str) -> str:
    return f"[tool.uv.sources]\n{source}\n\n[tool.livespec_dev_tooling]\n{tooling}\n"


def test_runtime_declares_the_delegated_gate_client_opt_in() -> None:
    """The remote-gate client and repository switch travel in versioned config."""
    pyproject = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert _declares_delegated_gate(pyproject=pyproject)


def test_delegated_gate_declaration_is_independent_of_the_pinned_release() -> None:
    """Any released tag satisfies the declaration; only a missing tag or switch fails."""
    git = '{ git = "https://example.invalid/tooling.git", tag = "%s" }'
    pinned = _fixture_pyproject(
        source=f"livespec-dev-tooling = {git % 'v9.8.7'}",
        tooling="delegated_gate = true",
    )
    untagged = _fixture_pyproject(
        source='livespec-dev-tooling = { git = "https://example.invalid/tooling.git" }',
        tooling="delegated_gate = true",
    )
    switch_dropped = _fixture_pyproject(
        source=f"livespec-dev-tooling = {git % 'v9.8.7'}",
        tooling="other = true",
    )

    assert _declares_delegated_gate(pyproject=pinned)
    assert not _declares_delegated_gate(pyproject=untagged)
    assert not _declares_delegated_gate(pyproject=switch_dropped)
    assert not _declares_delegated_gate(pyproject="")


def test_pre_push_execs_the_delegated_client_before_the_local_aggregate() -> None:
    """A selected remote gate cannot fall through to a local aggregate."""
    script = (_ROOT / ".github/scripts/check-pre-push.sh").read_text(encoding="utf-8")
    delegate = "\n".join(
        [
            f"if uv run python -m {_DELEGATE_MODULE} enabled; then",
            '    echo ":: pre-push: delegated gate is enabled for this repo; gating on the cluster"',
            f"    exec uv run python -m {_DELEGATE_MODULE} run",
            "fi",
        ]
    )

    assert delegate in script
    assert script.index("livespec_dev_tooling.green_token check") < script.index(delegate)
    assert script.index(delegate) < script.rindex("just check")


def test_every_aggregate_member_carries_a_purity_declaration() -> None:
    """A matching green token may memoize only members declared tree-pure."""
    outcome = check_purity.audit_check_purity(targets=_aggregate_targets(), repo_root=_ROOT)

    assert is_successful(outcome)
    assert unsafe_perform_io(outcome.unwrap()).undeclared == ()


def test_aggregate_refuses_to_run_with_an_undeclared_member() -> None:
    """The aggregate delegates the fail-closed declaration audit before its member loop."""
    script = _CHECK_SCRIPT.read_text(encoding="utf-8")
    declaration_audit = (
        'uv run python -m livespec_dev_tooling.green_token undeclared "${targets[@]}"'
    )

    assert declaration_audit in script
    assert script.index(declaration_audit) < script.index('for target in "${targets[@]}"')
