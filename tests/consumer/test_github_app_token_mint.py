"""Consumer-tier scenario tests: the installation-token mint, provider, helper.

Covers NINE of the thirty-two `## Scenario:` headings ratified as v025 in
`SPECIFICATION/scenarios.md` — the three `mint_installation_token` scenarios,
the two `InstallationTokenProvider` ones, and the four `git credential`
helper ones.

⚠️ EVERY MINT BELOW RUNS OVER INJECTED `MintSeams`, AND THAT IS LOAD-BEARING
RATHER THAN STYLISTIC. Both `mint_installation_token` and
`credential_helper.main` default their `seams` parameter to
`DEFAULT_MINT_SEAMS`, which is the REAL openssl subprocess signer paired with
the REAL urllib calls to the GitHub REST API. A test written without the
injection would therefore attempt a genuine RS256 sign against a fake PEM and
a genuine network mint. Each recorder below asserts on what the fake seams
were asked for, so the assertions double as the proof that the production
seams were never reached.

Every name imported below is ratified in `SPECIFICATION/contracts.md`
section "Module-level public surface".
"""

import io
from pathlib import Path
from typing import Any

import pytest
from returns.io import IOFailure, IOResult, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec_runtime.github_auth.config import GithubAppConfig
from livespec_runtime.github_auth.credential_helper import main
from livespec_runtime.github_auth.errors import GithubAppAuthError
from livespec_runtime.github_auth.mint import MintSeams, mint_installation_token
from livespec_runtime.github_auth.provider import (
    TOKEN_REFRESH_SECONDS,
    InstallationTokenProvider,
)

__all__: list[str] = []

_PEM = "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n"
_ISSUED_AT = 1_700_000_000
_ENVIRON = {"GITHUB_APP_ID": "12345", "GITHUB_PRIVATE_KEY": _PEM}

# GitHub's installation tokens expire after roughly an hour; the refresh
# horizon must land safely before that.
_INSTALLATION_TOKEN_LIFETIME_SECONDS = 60 * 60


class _RecordingSeams:
    """A consumer-shaped `MintSeams` double that records what the mint asked for.

    Structural, not inherited: `as_seams()` binds the three methods into a
    real `MintSeams`, so the mint sees exactly the ratified seam shape while
    the test keeps a handle on the call log.
    """

    def __init__(self, *, installations: Any = None) -> None:
        self.installations = installations
        self.signed_pems: list[str] = []
        self.get_urls: list[str] = []
        self.post_urls: list[str] = []

    def sign(self, *, signing_input: str, pem: str) -> IOResult[bytes, GithubAppAuthError]:
        _ = signing_input
        self.signed_pems.append(pem)
        return IOSuccess(b"fake-signature")

    def http_get(self, *, url: str, jwt: str) -> IOResult[Any, GithubAppAuthError]:
        _ = jwt
        self.get_urls.append(url)
        return IOSuccess(self.installations)

    def http_post(self, *, url: str, jwt: str) -> IOResult[Any, GithubAppAuthError]:
        _ = jwt
        self.post_urls.append(url)
        return IOSuccess({"token": f"ghs_mint_{len(self.post_urls)}"})

    def as_seams(self) -> MintSeams:
        return MintSeams(sign=self.sign, http_get=self.http_get, http_post=self.http_post)


class _SettableClock:
    """An injectable clock so token expiry is forced without sleeping."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def _config(*, installation_id: str | None = None) -> GithubAppConfig:
    return GithubAppConfig(app_id="12345", private_key_pem=_PEM, installation_id=installation_id)


def _invoke_helper(
    *,
    argv: list[str],
    stdin_text: str,
    seams: MintSeams,
    environ: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    """Drive the helper exactly as git does: one operation, attributes on stdin."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = main(
        argv=argv,
        environ=_ENVIRON if environ is None else environ,
        stdin=io.StringIO(stdin_text),
        stdout=stdout,
        stderr=stderr,
        seams=seams,
    )
    return code, stdout.getvalue(), stderr.getvalue()


# ===========================================================================
# Mint scenarios
# ===========================================================================


def test_minting_with_a_pinned_installation_performs_no_discovery() -> None:
    """Covers scenario "minting with a pinned installation performs no discovery"."""
    recorder = _RecordingSeams()

    outcome = mint_installation_token(
        config=_config(installation_id="777"), issued_at=_ISSUED_AT, seams=recorder.as_seams()
    )

    assert isinstance(outcome, IOSuccess)
    assert unsafe_perform_io(outcome.unwrap()) == "ghs_mint_1"
    assert recorder.post_urls == ["https://api.github.com/app/installations/777/access_tokens"]
    assert recorder.get_urls == []


def test_minting_discovers_the_sole_installation_when_none_is_pinned() -> None:
    """Covers scenario "minting discovers the sole installation when none is pinned"."""
    recorder = _RecordingSeams(installations=[{"id": 777}])

    outcome = mint_installation_token(
        config=_config(), issued_at=_ISSUED_AT, seams=recorder.as_seams()
    )

    assert recorder.get_urls == ["https://api.github.com/app/installations"]
    assert recorder.post_urls == ["https://api.github.com/app/installations/777/access_tokens"]
    assert isinstance(outcome, IOSuccess)
    assert unsafe_perform_io(outcome.unwrap()) == "ghs_mint_1"


def test_minting_with_several_installations_and_no_pin_fails_closed() -> None:
    """Covers scenario "minting with several installations and no pin fails closed directing the operator to pin one"."""
    recorder = _RecordingSeams(installations=[{"id": 1}, {"id": 2}])

    outcome = mint_installation_token(
        config=_config(), issued_at=_ISSUED_AT, seams=recorder.as_seams()
    )

    assert isinstance(outcome, IOFailure)
    failure = unsafe_perform_io(outcome.failure())
    assert isinstance(failure, GithubAppAuthError)
    assert "GITHUB_APP_INSTALLATION_ID" in failure.detail
    assert recorder.post_urls == []


# ===========================================================================
# Caching-provider scenarios
# ===========================================================================


def test_the_provider_mints_on_first_use_and_caches_in_process_memory_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Covers scenario "the provider mints on first use and caches in process memory only".

    The cwd is moved to an empty `tmp_path` for the whole exchange, so the
    "never written to disk or any store" clause is OBSERVED: a provider that
    persisted its token would have to leave something behind, and the
    directory is asserted still empty afterwards.
    """
    monkeypatch.chdir(tmp_path)
    recorder = _RecordingSeams(installations=[{"id": 777}])
    provider = InstallationTokenProvider(
        config=_config(), seams=recorder.as_seams(), clock=_SettableClock()
    )

    first = provider.token()

    assert first == "ghs_mint_1"
    assert len(recorder.post_urls) == 1
    assert provider.token() == first
    assert len(recorder.post_urls) == 1
    assert list(tmp_path.iterdir()) == []


def test_the_provider_remints_transparently_past_the_refresh_horizon() -> None:
    """Covers scenario "the provider re-mints transparently once the 55-minute refresh horizon passes".

    The caller makes the same `token()` call throughout — handling expiry is
    the provider's job, not the caller's — and the horizon is asserted to sit
    before GitHub's roughly 60-minute installation-token expiry.
    """
    assert TOKEN_REFRESH_SECONDS == 3300
    assert TOKEN_REFRESH_SECONDS < _INSTALLATION_TOKEN_LIFETIME_SECONDS
    clock = _SettableClock()
    recorder = _RecordingSeams(installations=[{"id": 777}])
    provider = InstallationTokenProvider(config=_config(), seams=recorder.as_seams(), clock=clock)
    first = provider.token()

    clock.now = float(TOKEN_REFRESH_SECONDS)
    reminted = provider.token()

    assert reminted == "ghs_mint_2"
    assert reminted != first
    assert len(recorder.post_urls) == 2


# ===========================================================================
# `git credential` helper scenarios
# ===========================================================================


def test_the_credential_helper_answers_an_https_get_with_a_freshly_minted_token() -> None:
    """Covers scenario "the credential helper answers an https get with x-access-token and a freshly minted token".

    The injected seams are what keeps this offline, and the recorder proves
    it: the fake signer was handed the normalized PEM, so the production
    openssl sign and the production network mint were both bypassed.
    """
    recorder = _RecordingSeams(installations=[{"id": 777}])

    code, out, err = _invoke_helper(
        argv=["get"],
        stdin_text="protocol=https\nhost=github.com\npath=owner/repo.git\n\n",
        seams=recorder.as_seams(),
    )

    assert code == 0
    assert out == "username=x-access-token\npassword=ghs_mint_1\n"
    assert err == ""
    assert recorder.signed_pems == [_PEM]


def test_the_credential_helper_emits_no_credential_for_a_non_https_context() -> None:
    """Covers scenario "the credential helper emits no credential for a non-https context".

    Exit 0 with empty stdout is how git reads "no credential from this
    helper"; the untouched recorder shows the helper short-circuited before
    any mint was attempted.
    """
    recorder = _RecordingSeams(installations=[{"id": 777}])

    code, out, err = _invoke_helper(
        argv=["get"], stdin_text="protocol=ssh\nhost=github.com\n\n", seams=recorder.as_seams()
    )

    assert code == 0
    assert out == ""
    assert err == ""
    assert recorder.post_urls == []


def test_the_credential_helper_store_and_erase_are_noops(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Covers scenario "the credential helper's store and erase are no-ops for the ephemeral token".

    The token is ephemeral, so there is nothing to store and nothing to
    erase. A pre-existing sentinel file witnesses the "nothing is written or
    removed anywhere" clause from both directions.
    """
    monkeypatch.chdir(tmp_path)
    sentinel = tmp_path / "sentinel.txt"
    _ = sentinel.write_text("untouched", encoding="utf-8")
    recorder = _RecordingSeams(installations=[{"id": 777}])

    for operation in ("store", "erase"):
        code, out, err = _invoke_helper(
            argv=[operation],
            stdin_text="protocol=https\nhost=github.com\n\n",
            seams=recorder.as_seams(),
        )
        assert code == 0
        assert out == ""
        assert err == ""

    assert list(tmp_path.iterdir()) == [sentinel]
    assert sentinel.read_text(encoding="utf-8") == "untouched"
    assert recorder.post_urls == []


def test_the_credential_helper_fails_closed_with_the_diagnostic_on_stderr() -> None:
    """Covers scenario "the credential helper fails closed with the actionable diagnostic on stderr"."""
    recorder = _RecordingSeams(installations=[{"id": 777}])

    code, out, err = _invoke_helper(
        argv=["get"],
        stdin_text="protocol=https\nhost=github.com\n\n",
        seams=recorder.as_seams(),
        environ={"GITHUB_APP_ID": "12345"},
    )

    assert code != 0
    assert out == ""
    assert "GITHUB_PRIVATE_KEY" in err
    assert "credential_wrapper" in err
    assert recorder.post_urls == []
