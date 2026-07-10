"""Regression coverage for the Phase-1 mechanical fleet-check burndown."""

from collections.abc import Callable

from livespec_dev_tooling.checks import (
    all_declared,
    assert_never_exhaustiveness,
    keyword_only_args,
    no_inheritance,
)

__all__: list[str] = []


def _check_stderr(*, capsys, check: Callable[[], int]) -> str:
    assert check() == 0
    return capsys.readouterr().err


def test_non_file_lloc_newly_covered_mechanical_checks_are_burned_down(
    capsys,
) -> None:
    captured = "\n".join(
        (
            _check_stderr(capsys=capsys, check=keyword_only_args.main),
            _check_stderr(capsys=capsys, check=no_inheritance.main),
            _check_stderr(capsys=capsys, check=all_declared.main),
            _check_stderr(capsys=capsys, check=assert_never_exhaustiveness.main),
        ),
    )
    assert '"newly_covered": true' not in captured
