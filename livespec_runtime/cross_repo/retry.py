"""Retry policy for cross-repo subprocess queries.

Per livespec/SPECIFICATION/contracts.md v072: 3 attempts with 1s / 2s /
4s exponential backoff over the EXPECTED transport/environment failures
a `gh`-backed query raises. On exhaustion this module returns `None` and
lets the caller translate that into `RefStatus.UNKNOWN`; a bug-class
exception is not retried and propagates to the supervisor (see
`retry_with_backoff`).

The policy is intentionally NOT user-configurable in v1. Projects
with bandwidth-constrained CI environments are expected to pre-fetch
sibling repos to local clones (configured via the `local_clone` field
in `cross_repo_targets`) to avoid the GitHub-query path entirely.

`time.sleep` is called directly so tests can monkeypatch it to a no-op
or a list-append spy and verify the backoff sequence without burning
real wall-clock seconds.
"""

import json
import subprocess
import time
from collections.abc import Callable
from typing import TypeVar

__all__: list[str] = ["retry_with_backoff"]

T = TypeVar("T")

_ATTEMPTS = 3
_BACKOFFS_SECONDS: tuple[float, ...] = (1.0, 2.0, 4.0)


def retry_with_backoff(*, fn: Callable[[], T]) -> T | None:
    """Run `fn` with the documented retry policy.

    Returns `fn()`'s value on first success; returns `None` after all
    `_ATTEMPTS` attempts raise an EXPECTED transport/environment failure.
    Callers translate the `None` return into `RefStatus.UNKNOWN` at the
    resolve-ref boundary; this module deliberately doesn't import the
    status enum to keep the seam minimal (retry layer is reusable across
    non-resolve callers).

    Only expected transport/environment failures are caught and retried:

    - `subprocess.SubprocessError` — a `gh` non-zero exit
      (`CalledProcessError`: transient auth / rate-limit / network) or a
      `TimeoutExpired`.
    - `OSError` — a transient network-level error (`ConnectionError`,
      `TimeoutError`, …), OR an absent `gh` binary (`FileNotFoundError`),
      which `providers.github` documents must collapse to
      `RefStatus.UNKNOWN` rather than crashing the resolve walk.
    - `json.JSONDecodeError` — a malformed / truncated `gh` payload,
      which `providers.github` documents as a transport failure.

    A BUG-class exception (`TypeError`, `KeyError`, `AttributeError`, …)
    is NOT caught: it propagates to the outermost supervisor instead of
    being masked as `None` → `RefStatus.UNKNOWN`, so an impl-side bug
    surfaces loudly rather than degrading silently. A domain/config error
    the provider raises (e.g. `NonCanonicalGithubUrlError` on a malformed
    `github_url`) likewise propagates — it is a user-configuration fault
    to surface, not a transient failure to retry.
    """
    for attempt_index in range(_ATTEMPTS):
        try:
            return fn()
        except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
            if attempt_index < _ATTEMPTS - 1:
                time.sleep(_BACKOFFS_SECONDS[attempt_index])
    return None
