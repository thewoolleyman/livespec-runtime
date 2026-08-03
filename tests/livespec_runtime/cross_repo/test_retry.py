"""Tests for `livespec_runtime.cross_repo.retry`.

Verifies the 3-attempt, 1s/2s/4s exponential backoff policy: function
runs to first-success, sleeps the documented delay between failed
attempts, and returns `RetryExhausted` on the failure track after all
attempts fail.

BOTH failure channels are covered on purpose. `fn` landing on the
`IOResult` failure track is the ordinary transport case; `fn` RAISING is
still caught, because the retry layer deliberately does not distinguish
transient transport errors from bugs, and dropping that catch would turn
an impl bug into a crash in every consumer's dispatcher.

`time.sleep` is monkeypatched to a list-append spy so test bodies
verify the backoff sequence without burning real wall-clock seconds.

Schema reference: livespec/SPECIFICATION/contracts.md v072.
"""

import time

import pytest
from returns.io import IOFailure, IOResult, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec_runtime.cross_repo.retry import RetryExhausted, retry_with_backoff

__all__: list[str] = []


def _exhausted(outcome: IOResult[object, RetryExhausted]) -> RetryExhausted:
    """The `RetryExhausted` an outcome carries, asserting it took the failure track."""
    assert isinstance(outcome, IOFailure)
    return unsafe_perform_io(outcome.failure())


def test_first_attempt_success_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)

    outcome = retry_with_backoff(fn=lambda: IOSuccess(42))

    assert isinstance(outcome, IOSuccess)
    assert unsafe_perform_io(outcome.unwrap()) == 42
    assert sleeps == []


def test_second_attempt_success_after_one_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)
    attempts: list[int] = []

    def fn() -> IOResult[int, str]:
        attempts.append(1)
        if len(attempts) == 1:
            return IOFailure("first attempt fails")
        return IOSuccess(99)

    outcome = retry_with_backoff(fn=fn)

    assert unsafe_perform_io(outcome.unwrap()) == 99
    assert sleeps == [1.0]


def test_third_attempt_success_after_two_backoffs(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)
    attempts: list[int] = []

    def fn() -> IOResult[str, str]:
        attempts.append(1)
        if len(attempts) < 3:
            return IOFailure("flake")
        return IOSuccess("ok")

    outcome = retry_with_backoff(fn=fn)

    assert unsafe_perform_io(outcome.unwrap()) == "ok"
    assert sleeps == [1.0, 2.0]


def test_all_attempts_failing_reports_the_last_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exhaustion carries WHY, which the pre-railway bare `None` could not."""
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)

    outcome = retry_with_backoff(fn=lambda: IOFailure("gh said no"))

    assert _exhausted(outcome) == RetryExhausted(attempts=3, detail="gh said no")
    assert sleeps == [1.0, 2.0]


def test_a_raising_fn_is_still_caught_and_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    """The broad catch is policy, not an accident — a bug degrades, it does not crash."""
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)

    def fn() -> IOResult[int, str]:
        raise RuntimeError("always fails")

    outcome = retry_with_backoff(fn=fn)

    assert _exhausted(outcome) == RetryExhausted(attempts=3, detail="RuntimeError: always fails")
    assert sleeps == [1.0, 2.0]


def test_backoff_sequence_documents_only_two_sleeps(monkeypatch: pytest.MonkeyPatch) -> None:
    """The documented sequence is 1s/2s/4s but the third backoff would
    follow the third (final) attempt — at which point we surface the
    exhaustion rather than sleeping. So in steady-state the spy only
    ever sees two delays."""
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)

    _ = retry_with_backoff(fn=lambda: IOFailure("always fails"))

    assert len(sleeps) == 2
    assert sleeps[0] == 1.0
    assert sleeps[1] == 2.0
