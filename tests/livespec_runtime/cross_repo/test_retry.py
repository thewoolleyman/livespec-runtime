"""Tests for `livespec_runtime.cross_repo.retry`.

Verifies the 3-attempt, 1s/2s/4s exponential backoff policy: function
runs to first-success, sleeps the documented delay between failed
attempts, and returns `None` after all attempts raise.

`time.sleep` is monkeypatched to a list-append spy so test bodies
verify the backoff sequence without burning real wall-clock seconds.

Schema reference: livespec/SPECIFICATION/contracts.md v072.
"""

import time

import pytest

from livespec_runtime.cross_repo.retry import retry_with_backoff

__all__: list[str] = []


def test_first_attempt_success_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)
    result = retry_with_backoff(fn=lambda: 42)
    assert result == 42
    assert sleeps == []


def test_second_attempt_success_after_one_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)
    attempts: list[int] = []

    def fn() -> int:
        attempts.append(1)
        if len(attempts) == 1:
            raise RuntimeError("first attempt fails")
        return 99

    result = retry_with_backoff(fn=fn)
    assert result == 99
    assert sleeps == [1.0]


def test_third_attempt_success_after_two_backoffs(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)
    attempts: list[int] = []

    def fn() -> str:
        attempts.append(1)
        if len(attempts) < 3:
            raise OSError("flake")
        return "ok"

    result = retry_with_backoff(fn=fn)
    assert result == "ok"
    assert sleeps == [1.0, 2.0]


def test_all_attempts_fail_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)

    def fn() -> int:
        raise RuntimeError("always fails")

    result = retry_with_backoff(fn=fn)
    assert result is None
    assert sleeps == [1.0, 2.0]


def test_backoff_sequence_documents_only_two_sleeps(monkeypatch: pytest.MonkeyPatch) -> None:
    """The documented sequence is 1s/2s/4s but the third backoff would
    follow the third (final) attempt — at which point we surface None
    rather than sleeping. So in steady-state the spy only ever sees
    two delays."""
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)

    def fn() -> int:
        raise RuntimeError("always fails")

    _ = retry_with_backoff(fn=fn)
    assert len(sleeps) == 2
    assert sleeps[0] == 1.0
    assert sleeps[1] == 2.0
