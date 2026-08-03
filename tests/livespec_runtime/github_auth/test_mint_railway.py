"""The GitHub App mint answers on a railway, not by raising.

Every EXPECTED failure on this path already had a single named type,
`GithubAppAuthError`, and every one of them was RAISED. The type does not
change and neither does what a consumer catches — `InstallationTokenProvider`
still raises it, which is what `beads-fabro`'s dispatcher imports and handles.
What changes is that between the openssl signer and the provider the failure
travels as a VALUE, so each step's own contract says whether it can fail.

These tests pin the two ends of that: the signer, which is the seam the mint
composes over, and the mint itself.
"""

import subprocess
from typing import Any

import pytest
from returns.io import IOFailure, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec_runtime.github_auth.errors import GithubAppAuthError
from livespec_runtime.github_auth.signing import sign_rs256_with_openssl

__all__: list[str] = []

_NOT_A_KEY = "-----BEGIN PRIVATE KEY-----\nnot-a-real-key\n-----END PRIVATE KEY-----\n"


def test_sign_rs256_carries_the_signature_on_the_success_track(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """openssl signed it — the bytes ride the success track."""

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(args=argv, returncode=0, stdout=b"signature", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)

    outcome = sign_rs256_with_openssl(signing_input="header.payload", pem=_NOT_A_KEY)

    assert isinstance(outcome, IOSuccess)
    assert unsafe_perform_io(outcome.unwrap()) == b"signature"


def test_sign_rs256_routes_an_unloadable_key_to_the_failure_track(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A key openssl cannot load is an EXPECTED misconfiguration.

    It kept its type — `GithubAppAuthError` with the same actionable detail —
    and only its channel changed, so a caller that catches the type still sees
    the same diagnostic once the provider re-raises it.
    """

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(args=argv, returncode=1, stdout=b"", stderr=b"bad key")

    monkeypatch.setattr(subprocess, "run", fake_run)

    outcome = sign_rs256_with_openssl(signing_input="header.payload", pem=_NOT_A_KEY)

    assert isinstance(outcome, IOFailure)
    failure = unsafe_perform_io(outcome.failure())
    assert isinstance(failure, GithubAppAuthError)
    assert "GITHUB_PRIVATE_KEY" in failure.detail
