"""Retry policy for cross-repo subprocess queries.

Per livespec/SPECIFICATION/contracts.md §"Cross-repo dependency awareness":
3 attempts with 1s / 2s / 4s exponential backoff. On every-attempt
failure the caller surfaces `RefStatus.unknown` rather than raising.

The retry policy is NOT user-configurable in v1. Projects with
bandwidth-constrained CI environments are expected to pre-fetch sibling
repos to local clones to avoid the GitHub-query path entirely.
"""

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

_ATTEMPTS = 3
_BACKOFFS_SECONDS: tuple[float, ...] = (1.0, 2.0, 4.0)


def retry_with_backoff(*, fn: Callable[[], T]) -> T | None:
    """Run `fn` with the documented retry policy.

    Returns the function's value on first success; returns `None` after
    all attempts raise. The caller's job to translate `None` into
    `RefStatus.unknown` (this module deliberately doesn't import the
    status enum to keep the seam minimal).

    `time.sleep` is called directly so tests can `patch("time.sleep")`
    or `monkeypatch.setattr("time.sleep", ...)` to skip real backoff.
    """
    for attempt_index in range(_ATTEMPTS):
        try:
            return fn()
        except Exception:
            if attempt_index < _ATTEMPTS - 1:
                time.sleep(_BACKOFFS_SECONDS[attempt_index])
    return None


__all__ = ["retry_with_backoff"]
