"""Tests for `livespec_runtime.cross_repo.retry`.

Verifies the 3-attempt, 1s/2s/4s exponential backoff policy over the
EXPECTED transport/environment failures a `gh`-backed query raises:
`fn` runs to first-success, sleeps the documented delay between failed
attempts, and returns `None` after all attempts raise such a failure.

The retry layer catches ONLY expected transport/environment failures
(`subprocess.SubprocessError`, `OSError`, `json.JSONDecodeError`); a
bug-class exception (e.g. `TypeError`) is NOT swallowed to `None` but
propagates to the supervisor, so an impl-side bug surfaces loudly
rather than degrading silently to `RefStatus.UNKNOWN`.

`time.sleep` is monkeypatched to a list-append spy so test bodies
verify the backoff sequence without burning real wall-clock seconds.

Schema reference: livespec/SPECIFICATION/contracts.md v072.
"""

import subprocess
import time

import pytest

from livespec_runtime.cross_repo.retry import retry_with_backoff

__all__: list[str] = []


def _transient() -> subprocess.CalledProcessError:
    """A transient transport failure the retry layer catches and retries."""
    return subprocess.CalledProcessError(returncode=1, cmd=["gh"])


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
            raise _transient()
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
            # OSError is a retried transport/environment failure (a
            # transient network error, or an absent `gh` binary).
            raise OSError("flake")
        return "ok"

    result = retry_with_backoff(fn=fn)
    assert result == "ok"
    assert sleeps == [1.0, 2.0]


def test_all_attempts_fail_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)

    def fn() -> int:
        raise _transient()

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
        raise _transient()

    _ = retry_with_backoff(fn=fn)
    assert len(sleeps) == 2
    assert sleeps[0] == 1.0
    assert sleeps[1] == 2.0


def test_bug_class_exception_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    """A bug-class exception is NOT swallowed to `None`: it propagates on
    the FIRST attempt (no retry), so an impl-side bug surfaces loudly to
    the supervisor rather than degrading silently to `RefStatus.UNKNOWN`."""
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)
    attempts: list[int] = []

    def fn() -> int:
        attempts.append(1)
        raise TypeError("impl-side bug")

    with pytest.raises(TypeError, match="impl-side bug"):
        _ = retry_with_backoff(fn=fn)
    # Propagated on the first attempt — never retried, never slept.
    assert attempts == [1]
    assert sleeps == []


def test_transient_subprocess_error_retried_then_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """A transient `subprocess.CalledProcessError` is STILL retried across
    all attempts and degrades to `None` after exhaustion (the transport
    graceful-degradation path the resolve-ref boundary maps to UNKNOWN)."""
    sleeps: list[float] = []
    monkeypatch.setattr(time, "sleep", sleeps.append)
    attempts: list[int] = []

    def fn() -> int:
        attempts.append(1)
        raise _transient()

    result = retry_with_backoff(fn=fn)
    assert result is None
    assert attempts == [1, 1, 1]
    assert sleeps == [1.0, 2.0]
