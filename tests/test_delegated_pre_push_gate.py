"""Regression coverage for this repository's delegated pre-push wiring."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).parent.parent
_DELEGATE_MODULE = "livespec_dev_tooling.gate_remote_delegate"


def test_runtime_declares_the_delegated_gate_client_opt_in() -> None:
    """The remote-gate client and repository switch travel in versioned config."""
    pyproject = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'tag = "v1.134.2"' in pyproject
    tooling_block = pyproject.split("[tool.livespec_dev_tooling]", maxsplit=1)[1]
    assert "delegated_gate = true" in tooling_block


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
