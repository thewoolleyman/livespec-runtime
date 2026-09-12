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

import json
from pathlib import Path

from livespec_dev_tooling.checks import heading_coverage, no_direct_tool_invocation

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


def test_test_discipline_heading_coverage_registry_is_complete(monkeypatch, tmp_path) -> None:
    """Witness non-functional-requirements.md "Test discipline".

    Among that section's clauses is the scenario-tier / registry-coverage
    discipline this very `tests/heading-coverage.json` implements: every
    spec H2 MUST carry a registry entry. check-heading-coverage enforces
    it. The control arm drives the check to conviction on a fabricated
    spec tree carrying an unregistered heading, so the passing assertion
    against this repo is evidence the discipline holds rather than
    evidence the check inspected nothing.
    """
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(repo_root)
    assert heading_coverage.main() == 0

    # Control arm: a spec tree with an H2 absent from the registry MUST be
    # convicted (the uncovered-heading direction).
    fixture = tmp_path / "fixture"
    (fixture / "SPECIFICATION").mkdir(parents=True)
    (fixture / "SPECIFICATION" / "spec.md").write_text(
        "# Title\n\n## Uncovered Heading\n\nbody\n", encoding="utf-8"
    )
    (fixture / "tests").mkdir()
    (fixture / "tests" / "heading-coverage.json").write_text(json.dumps([]), encoding="utf-8")
    monkeypatch.chdir(fixture)
    assert heading_coverage.main() == 1
