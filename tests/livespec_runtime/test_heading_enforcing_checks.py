"""Control-armed coverage for spec headings whose rule a mechanical check enforces.

These headings state an architectural rule that is upheld by a
`livespec_dev_tooling` check rather than by exercising importable
library behavior, so `tests/heading-coverage.json` maps each to the
test below that witnesses the rule. Each test is control-armed: it
asserts the check passes against this repo's real tree AND that the
same check convicts a fabricated violation, so a green result is
evidence the rule holds rather than evidence the check never ran.
"""

from __future__ import annotations

from pathlib import Path

from livespec_dev_tooling.checks import no_direct_tool_invocation

__all__: list[str] = []


def _run_no_direct_tool_invocation(*, cwd: Path, monkeypatch) -> int:
    monkeypatch.chdir(cwd)
    return no_direct_tool_invocation.main()


def test_task_runner_discipline_bans_direct_tool_invocation(monkeypatch, tmp_path) -> None:
    """Witness non-functional-requirements.md "Task-runner discipline".

    The load-bearing clause forbids direct `ruff`/`pyright`/`pytest`/
    `coverage`/`gh` invocations in `lefthook.yml` and CI YAML — every
    such call MUST route through `just <target>`. The check is
    self-contained (it reads `lefthook.yml` and `.github/workflows/*`
    directly, with no consumer role-key gating), so the control arm
    below drives it to conviction on a fabricated violation.
    """
    repo_root = Path(__file__).resolve().parents[2]
    assert _run_no_direct_tool_invocation(cwd=repo_root, monkeypatch=monkeypatch) == 0

    # Control arm: a lefthook hook that shells out to pytest directly
    # (rather than through `just`) MUST be convicted. Without this arm
    # the passing assertion above could not distinguish "the rule holds"
    # from "the check inspected nothing".
    violation = tmp_path / "violation"
    violation.mkdir()
    (violation / "lefthook.yml").write_text(
        "pre-push:\n  commands:\n    tests:\n      run: pytest -q\n",
        encoding="utf-8",
    )
    assert _run_no_direct_tool_invocation(cwd=violation, monkeypatch=monkeypatch) == 1
