"""Global test fixtures.

Patches `time.sleep` to a no-op so retry-policy tests don't burn
real wall-clock time on the documented 1s / 2s / 4s backoffs.
Individual tests that want to verify backoff CALL COUNT can override
via monkeypatch within the test body (e.g., `monkeypatch.setattr` with
a list-append spy).
"""

import time

import pytest


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)
