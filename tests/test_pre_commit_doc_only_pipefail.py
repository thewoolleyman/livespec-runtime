"""Regression coverage for the doc-only pre-commit subset's pipefail verdict."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).parent.parent
_SCRIPT = _ROOT / ".github/scripts/check-pre-commit-doc-only.sh"
_ARMED = "armed"
_UNARMED = "unarmed"

# A fake `git diff --cached --name-only` writer. The registry path comes first so an
# early-exiting reader can match and close its pipe while the writer still has output
# to write; `filler` lines then push the output past the 64 KiB pipe buffer.
_FAKE_GIT = """#!/usr/bin/env bash
printf '%s\\n' "$STAGED_FIRST"
for ((i = 0; i < FILLER; i++)); do
    printf 'docs/some/long/path/segment/file-%08d.md\\n' "$i"
done
"""

# A fake `just` recording whether the TODO-ownership tier was armed for the registry check.
_FAKE_JUST = """#!/usr/bin/env bash
if [ "$1" = check-no-todo-registry ]; then
    printf '%s\\n' "${LIVESPEC_FAIL_IF_HEADING_COVERAGE_TODOS_EXIST:-unset}" >> "$VERDICT_LOG"
fi
"""


def _verdict(*, tmp_path: Path, staged_first: str, filler: int) -> str:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in (("git", _FAKE_GIT), ("just", _FAKE_JUST)):
        stub = bin_dir / name
        stub.write_text(body, encoding="utf-8")
        stub.chmod(0o755)
    log = tmp_path / "verdict.log"
    env = {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "STAGED_FIRST": staged_first,
        "FILLER": str(filler),
        "VERDICT_LOG": str(log),
    }
    subprocess.run(
        ["bash", str(_SCRIPT)],
        env=env,
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    return _ARMED if log.read_text(encoding="utf-8").strip() == "true" else _UNARMED


@pytest.mark.parametrize("filler", [0, 20000])
def test_staged_registry_arms_the_tier_whatever_the_staged_list_size(
    *, tmp_path: Path, filler: int
) -> None:
    """A staged heading-coverage.json is judged present on a small and a >64 KiB list."""
    verdict = _verdict(tmp_path=tmp_path, staged_first="tests/heading-coverage.json", filler=filler)

    assert verdict == _ARMED


@pytest.mark.parametrize("filler", [0, 20000])
def test_unstaged_registry_leaves_the_tier_unarmed_whatever_the_staged_list_size(
    *, tmp_path: Path, filler: int
) -> None:
    """Without the registry staged the tier stays unarmed on either list size."""
    verdict = _verdict(tmp_path=tmp_path, staged_first="docs/readme.md", filler=filler)

    assert verdict == _UNARMED
