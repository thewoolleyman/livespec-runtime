"""Tests for the 3-attempt 1s/2s/4s retry policy."""

import time

import pytest

from livespec_runtime.cross_repo.retry import retry_with_backoff


def test_first_attempt_success_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)
    result = retry_with_backoff(fn=lambda: 42)
    assert result == 42
    assert sleeps == []  # no backoff on first-attempt success


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
    assert sleeps == [1.0, 2.0]  # backoff after attempts 1 and 2, none after attempt 3
