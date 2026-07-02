"""Tests for `livespec_runtime.github_auth.config`.

Verifies the env-only fail-closed input boundary: both fleet-shipped
secrets present → a typed `GithubAppConfig` (with the optional
installation-id pin + API-URL override carried through); any
absent-or-empty required var → `GithubAppAuthError` naming EVERY
missing var, pointing at the tenant's credential_wrapper, and stating
there is NO fleet fallback.

Design reference: livespec core repo,
plan/github-app-auth/research/01-design.md (Pillar 2 fail-closed
resolution feeding the Pillar 1 mint).
"""

import pytest

from livespec_runtime.github_auth.config import (
    DEFAULT_API_URL,
    GithubAppConfig,
    load_github_app_config,
)
from livespec_runtime.github_auth.errors import GithubAppAuthError

__all__: list[str] = []

_PEM = "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n"


def test_both_secrets_present_returns_config_with_defaults() -> None:
    config = load_github_app_config(
        environ={"GITHUB_APP_ID": "123456", "GITHUB_PRIVATE_KEY": _PEM},
    )
    assert config == GithubAppConfig(
        app_id="123456",
        private_key_pem=_PEM,
        api_url="https://api.github.com",
        installation_id=None,
    )


def test_default_api_url_constant_is_the_public_github_api() -> None:
    assert DEFAULT_API_URL == "https://api.github.com"


def test_optional_installation_id_pin_and_api_url_override_are_carried() -> None:
    config = load_github_app_config(
        environ={
            "GITHUB_APP_ID": "123456",
            "GITHUB_PRIVATE_KEY": _PEM,
            "GITHUB_APP_INSTALLATION_ID": "131208965",
            "GITHUB_API_URL": "https://github.example.com/api/v3",
        },
    )
    assert config.installation_id == "131208965"
    assert config.api_url == "https://github.example.com/api/v3"


def test_app_id_is_stripped_of_surrounding_whitespace() -> None:
    config = load_github_app_config(
        environ={"GITHUB_APP_ID": " 123456\n", "GITHUB_PRIVATE_KEY": _PEM},
    )
    assert config.app_id == "123456"


def test_missing_app_id_fails_closed_with_actionable_diagnostic() -> None:
    with pytest.raises(GithubAppAuthError) as excinfo:
        _ = load_github_app_config(environ={"GITHUB_PRIVATE_KEY": _PEM})
    detail = excinfo.value.detail
    assert "GITHUB_APP_ID" in detail
    assert "credential_wrapper" in detail
    assert "NO fleet fallback" in detail


def test_missing_private_key_fails_closed_naming_the_var() -> None:
    with pytest.raises(GithubAppAuthError) as excinfo:
        _ = load_github_app_config(environ={"GITHUB_APP_ID": "123456"})
    assert "GITHUB_PRIVATE_KEY" in excinfo.value.detail


def test_empty_values_are_treated_as_missing_and_all_named() -> None:
    with pytest.raises(GithubAppAuthError) as excinfo:
        _ = load_github_app_config(
            environ={"GITHUB_APP_ID": "", "GITHUB_PRIVATE_KEY": ""},
        )
    detail = excinfo.value.detail
    assert "GITHUB_APP_ID" in detail
    assert "GITHUB_PRIVATE_KEY" in detail


def test_empty_optional_vars_fall_back_to_defaults() -> None:
    config = load_github_app_config(
        environ={
            "GITHUB_APP_ID": "123456",
            "GITHUB_PRIVATE_KEY": _PEM,
            "GITHUB_APP_INSTALLATION_ID": "",
            "GITHUB_API_URL": "",
        },
    )
    assert config.installation_id is None
    assert config.api_url == DEFAULT_API_URL


def test_config_is_frozen() -> None:
    config = GithubAppConfig(app_id="123456", private_key_pem=_PEM)
    with pytest.raises(AttributeError):
        config.app_id = "other"  # type: ignore[misc]
