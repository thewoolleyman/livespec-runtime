"""Tests for the hygiene scan's command railway.

`run_command` is the scan's ONLY process-spawn boundary, and until this
suite existed it carried `# pragma: no cover` — the one function in the
subsystem whose failure mode had never been exercised.
"""

import sys
from pathlib import Path

from returns.io import IOFailure, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec_runtime.hygiene_scan_context import run_command
from livespec_runtime.hygiene_scan_types import CommandResult, CommandUnavailable

__all__: list[str] = []


def test_run_command_carries_a_spawned_commands_result_on_the_success_track(
    tmp_path: Path,
) -> None:
    """A command that SPAWNS lands on the success track, exit code and all.

    A non-zero exit is DATA here, never the failure track: every reader in
    the scan already branches on `returncode`, so routing an ordinary
    "git said no" into the failure track would convert an answer into an
    error and change what the scan reports.
    """
    outcome = run_command(
        argv=[
            sys.executable,
            "-c",
            "import sys; sys.stdout.write('out'); sys.stderr.write('err'); sys.exit(3)",
        ],
        cwd=tmp_path,
    )

    assert isinstance(outcome, IOSuccess)
    assert unsafe_perform_io(outcome.unwrap()) == CommandResult(
        stdout="out", stderr="err", returncode=3
    )


def test_run_command_routes_an_unspawnable_command_to_the_failure_track(
    tmp_path: Path,
) -> None:
    """A command that cannot be SPAWNED is the one thing on the failure track.

    Before the railway this raised `FileNotFoundError` out of every caller
    in the subsystem, uncaught — a missing `git` or `gh` crashed the scan
    from wherever it happened to be invoked.
    """
    outcome = run_command(argv=["livespec-runtime-no-such-binary"], cwd=tmp_path)

    assert isinstance(outcome, IOFailure)
    failure = unsafe_perform_io(outcome.failure())
    assert failure == CommandUnavailable(
        argv="livespec-runtime-no-such-binary", detail=failure.detail
    )
    assert "livespec-runtime-no-such-binary" in failure.detail
