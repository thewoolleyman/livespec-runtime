"""Tests for `livespec_runtime.github_auth.mint`.

Verifies the installation-token mint railway over fake seams (JWT
assembly → RS256 sign → installation resolution →
`POST /app/installations/{id}/access_tokens`), the sole-installation
discovery vs the pinned-id path, the expected-failure railway
(`GithubAppAuthError` for empty credentials, ambiguous installations,
malformed responses), and the production urllib seams via a
monkeypatched `urllib.request.urlopen` — no live GitHub calls
anywhere.

Design reference: livespec core repo,
plan/github-app-auth/research/01-design.md (Pillar 1).
"""

import io
import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from livespec_runtime.github_auth.config import GithubAppConfig
from livespec_runtime.github_auth.errors import GithubAppAuthError
from livespec_runtime.github_auth.mint import (
    MintSeams,
    http_get_json,
    http_post_json,
    mint_installation_token,
    resolve_installation_id,
)
from livespec_runtime.github_auth.signing import b64url, jwt_signing_input

__all__: list[str] = []

_PEM = "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n"
_ISSUED_AT = 1_700_000_000


def _config(*, installation_id: str | None = None) -> GithubAppConfig:
    return GithubAppConfig(
        app_id="123456",
        private_key_pem=_PEM,
        installation_id=installation_id,
    )


def _seams(
    *,
    get_payload: Any = None,
    post_payload: Any = None,
    calls: list[tuple[str, str, str]] | None = None,
    signed_pems: list[str] | None = None,
) -> MintSeams:
    def sign(*, signing_input: str, pem: str) -> bytes:
        _ = signing_input
        if signed_pems is not None:
            signed_pems.append(pem)
        return b"fake-signature"

    def http_get(*, url: str, jwt: str) -> Any:
        if calls is not None:
            calls.append(("GET", url, jwt))
        return get_payload

    def http_post(*, url: str, jwt: str) -> Any:
        if calls is not None:
            calls.append(("POST", url, jwt))
        return post_payload

    return MintSeams(sign=sign, http_get=http_get, http_post=http_post)


def test_pinned_installation_mints_without_discovery() -> None:
    calls: list[tuple[str, str, str]] = []
    seams = _seams(post_payload={"token": "ghs_minted"}, calls=calls)
    token = mint_installation_token(
        config=_config(installation_id="42"),
        issued_at=_ISSUED_AT,
        seams=seams,
    )
    assert token == "ghs_minted"
    expected_jwt = (
        jwt_signing_input(app_id="123456", issued_at=_ISSUED_AT)
        + "."
        + b64url(raw=b"fake-signature")
    )
    assert calls == [
        ("POST", "https://api.github.com/app/installations/42/access_tokens", expected_jwt),
    ]


def test_sole_installation_discovery_resolves_and_mints() -> None:
    calls: list[tuple[str, str, str]] = []
    seams = _seams(get_payload=[{"id": 7}], post_payload={"token": "ghs_minted"}, calls=calls)
    token = mint_installation_token(config=_config(), issued_at=_ISSUED_AT, seams=seams)
    assert token == "ghs_minted"
    assert [(method, url) for method, url, _jwt in calls] == [
        ("GET", "https://api.github.com/app/installations"),
        ("POST", "https://api.github.com/app/installations/7/access_tokens"),
    ]


def test_pem_is_normalized_before_signing() -> None:
    signed_pems: list[str] = []
    seams = _seams(post_payload={"token": "ghs_minted"}, signed_pems=signed_pems)
    flattened = GithubAppConfig(
        app_id="123456",
        private_key_pem=_PEM.replace("\n", "\\n"),
        installation_id="42",
    )
    _ = mint_installation_token(config=flattened, issued_at=_ISSUED_AT, seams=seams)
    assert signed_pems == [_PEM]


def test_empty_app_id_fails_closed() -> None:
    config = GithubAppConfig(app_id="", private_key_pem=_PEM, installation_id="42")
    with pytest.raises(GithubAppAuthError) as excinfo:
        _ = mint_installation_token(config=config, issued_at=_ISSUED_AT, seams=_seams())
    assert "GITHUB_APP_ID" in excinfo.value.detail


def test_empty_private_key_fails_closed() -> None:
    config = GithubAppConfig(app_id="123456", private_key_pem="", installation_id="42")
    with pytest.raises(GithubAppAuthError) as excinfo:
        _ = mint_installation_token(config=config, issued_at=_ISSUED_AT, seams=_seams())
    assert "GITHUB_PRIVATE_KEY" in excinfo.value.detail


def test_non_list_installations_payload_is_actionable() -> None:
    seams = _seams(get_payload={"message": "nope"})
    with pytest.raises(GithubAppAuthError) as excinfo:
        _ = mint_installation_token(config=_config(), issued_at=_ISSUED_AT, seams=seams)
    assert "GITHUB_APP_INSTALLATION_ID" in excinfo.value.detail


def test_multiple_installations_require_a_pin() -> None:
    seams = _seams(get_payload=[{"id": 1}, {"id": 2}])
    with pytest.raises(GithubAppAuthError) as excinfo:
        _ = mint_installation_token(config=_config(), issued_at=_ISSUED_AT, seams=seams)
    assert "2 installations" in excinfo.value.detail
    assert "GITHUB_APP_INSTALLATION_ID" in excinfo.value.detail


def test_missing_token_in_mint_response_is_actionable() -> None:
    seams = _seams(post_payload={"expires_at": "2026-07-02T04:00:00Z"})
    with pytest.raises(GithubAppAuthError) as excinfo:
        _ = mint_installation_token(
            config=_config(installation_id="42"), issued_at=_ISSUED_AT, seams=seams
        )
    assert "no access token" in excinfo.value.detail


def test_non_dict_mint_response_is_actionable() -> None:
    seams = _seams(post_payload=["not", "a", "dict"])
    with pytest.raises(GithubAppAuthError) as excinfo:
        _ = mint_installation_token(
            config=_config(installation_id="42"), issued_at=_ISSUED_AT, seams=seams
        )
    assert "no access token" in excinfo.value.detail


def test_resolve_installation_id_prefers_the_pin() -> None:
    resolved = resolve_installation_id(
        api_url="https://api.github.com",
        jwt="unused",
        installation_id="131208965",
        http_get=lambda **_: pytest.fail("discovery must not run when a pin is present"),
    )
    assert resolved == "131208965"


def _urlopen_capture(
    monkeypatch: pytest.MonkeyPatch,
    *,
    body: bytes,
) -> list[tuple[urllib.request.Request, float]]:
    captured: list[tuple[urllib.request.Request, float]] = []

    def fake_urlopen(request: urllib.request.Request, timeout: float) -> io.BytesIO:
        captured.append((request, timeout))
        return io.BytesIO(body)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return captured


def test_http_get_json_sends_bearer_jwt_and_parses_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _urlopen_capture(monkeypatch, body=json.dumps([{"id": 7}]).encode("utf-8"))
    payload = http_get_json(url="https://api.github.com/app/installations", jwt="the-jwt")
    assert payload == [{"id": 7}]
    request, timeout = captured[0]
    assert request.get_method() == "GET"
    assert request.data is None
    assert request.get_header("Authorization") == "Bearer the-jwt"
    assert request.get_header("Accept") == "application/vnd.github+json"
    assert request.get_header("X-github-api-version") == "2022-11-28"
    assert timeout == 30.0


def test_http_post_json_sends_empty_json_object_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _urlopen_capture(monkeypatch, body=b'{"token": "ghs_minted"}')
    payload = http_post_json(url="https://api.github.com/x", jwt="the-jwt")
    assert payload == {"token": "ghs_minted"}
    request, _timeout = captured[0]
    assert request.get_method() == "POST"
    assert request.data == b"{}"


def test_http_transport_error_is_wrapped_actionably(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: urllib.request.Request, timeout: float) -> io.BytesIO:
        _ = request, timeout
        raise urllib.error.URLError("boom")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(GithubAppAuthError) as excinfo:
        _ = http_get_json(url="https://api.github.com/app/installations", jwt="the-jwt")
    assert "failed" in excinfo.value.detail


def test_http_invalid_json_is_wrapped_actionably(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = _urlopen_capture(monkeypatch, body=b"not json")
    with pytest.raises(GithubAppAuthError) as excinfo:
        _ = http_get_json(url="https://api.github.com/app/installations", jwt="the-jwt")
    assert "failed" in excinfo.value.detail


def test_non_https_url_is_refused_before_any_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: pytest.fail("urlopen must not be reached for a non-https URL"),
    )
    with pytest.raises(GithubAppAuthError) as excinfo:
        _ = http_get_json(url="http://api.github.com/app/installations", jwt="the-jwt")
    assert "https" in excinfo.value.detail
