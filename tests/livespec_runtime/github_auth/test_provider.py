"""Tests for `livespec_runtime.github_auth.provider`.

Carries the HARD acceptance criterion of work-item livespec-u67wdb:
a call sequence crossing the ~1-hour installation-token validity
forces expiry mid-sequence and the provider re-mints transparently —
same `token()` call, no caller involvement. The clock and the mint
seams are injected fakes; no live GitHub calls, no real sleeping.

Design reference: livespec core repo,
plan/github-app-auth/research/01-design.md (Pillar 1 — first-class
remint; "survives a >1-hour run / re-mints transparently").
"""

from typing import Any

from livespec_runtime.github_auth.config import GithubAppConfig
from livespec_runtime.github_auth.mint import MintSeams
from livespec_runtime.github_auth.provider import (
    TOKEN_REFRESH_SECONDS,
    InstallationTokenProvider,
)

__all__: list[str] = []

_PEM = "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n"


class _FakeClock:
    """A settable clock so tests force token expiry without sleeping."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _mint_counting_seams(mints: list[int]) -> MintSeams:
    def sign(*, signing_input: str, pem: str) -> bytes:
        _ = signing_input, pem
        return b"fake-signature"

    def http_get(*, url: str, jwt: str) -> Any:
        _ = url, jwt
        return [{"id": 7}]

    def http_post(*, url: str, jwt: str) -> Any:
        _ = url, jwt
        mints.append(1)
        return {"token": f"ghs_mint_{len(mints)}"}

    return MintSeams(sign=sign, http_get=http_get, http_post=http_post)


def _provider(clock: _FakeClock, mints: list[int]) -> InstallationTokenProvider:
    config = GithubAppConfig(app_id="123456", private_key_pem=_PEM)
    return InstallationTokenProvider(
        config=config,
        seams=_mint_counting_seams(mints),
        clock=clock,
    )


def test_refresh_horizon_is_55_minutes_safely_before_the_hour_expiry() -> None:
    assert TOKEN_REFRESH_SECONDS == 55 * 60


def test_first_call_mints_and_returns_the_token() -> None:
    clock = _FakeClock()
    mints: list[int] = []
    provider = _provider(clock, mints)
    assert provider.token() == "ghs_mint_1"
    assert len(mints) == 1


def test_calls_within_the_refresh_horizon_reuse_the_cached_token() -> None:
    clock = _FakeClock()
    mints: list[int] = []
    provider = _provider(clock, mints)
    first = provider.token()
    clock.now = float(TOKEN_REFRESH_SECONDS - 1)
    assert provider.token() == first
    assert len(mints) == 1


def test_acceptance_forced_expiry_mid_sequence_remints_transparently() -> None:
    clock = _FakeClock()
    mints: list[int] = []
    provider = _provider(clock, mints)
    first = provider.token()
    clock.now = 30 * 60.0
    assert provider.token() == first
    clock.now = 61 * 60.0
    reminted = provider.token()
    assert reminted == "ghs_mint_2"
    assert reminted != first
    clock.now = 130 * 60.0
    assert provider.token() == "ghs_mint_3"
    assert len(mints) == 3


def test_refresh_fires_at_the_horizon_before_the_token_actually_expires() -> None:
    clock = _FakeClock()
    mints: list[int] = []
    provider = _provider(clock, mints)
    _ = provider.token()
    clock.now = float(TOKEN_REFRESH_SECONDS)
    assert provider.token() == "ghs_mint_2"
    assert len(mints) == 2
