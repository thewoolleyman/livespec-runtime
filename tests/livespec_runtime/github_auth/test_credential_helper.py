"""Tests for `livespec_runtime.github_auth.credential_helper`.

Verifies the `git credential` helper protocol end-to-end over injected
streams and fake mint seams: `get` answers https contexts with
`username=x-access-token` plus a freshly minted installation token as
the password; `store`/`erase` are deliberate no-ops (the token is
ephemeral — nothing is ever persisted); a missing wrapper-injected env
fails closed with the actionable diagnostic on stderr and a non-zero
exit; and the `run()` process entry wires the real streams. No live
GitHub calls anywhere.

Design reference: livespec core repo,
plan/github-app-auth/research/01-design.md (Pillar 1 — the credential
helper shape; Pillar 3 — one primitive for factory AND standalone).
"""

import io
import os
import sys
from typing import Any

import pytest
from returns.io import IOFailure, IOResult, IOSuccess

from livespec_runtime.github_auth.credential_helper import main, run
from livespec_runtime.github_auth.errors import GithubAppAuthError
from livespec_runtime.github_auth.mint import MintSeams

__all__: list[str] = []

_PEM = "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n"
_ENVIRON = {"GITHUB_APP_ID": "123456", "GITHUB_PRIVATE_KEY": _PEM}


def _seams() -> MintSeams:
    def sign(*, signing_input: str, pem: str) -> IOResult[bytes, GithubAppAuthError]:
        _ = signing_input, pem
        return IOSuccess(b"fake-signature")

    def http_get(*, url: str, jwt: str) -> IOResult[Any, GithubAppAuthError]:
        _ = url, jwt
        return IOSuccess([{"id": 7}])

    def http_post(*, url: str, jwt: str) -> IOResult[Any, GithubAppAuthError]:
        _ = url, jwt
        return IOSuccess({"token": "ghs_helper"})

    return MintSeams(sign=sign, http_get=http_get, http_post=http_post)


def _failing_sign_seams() -> MintSeams:
    """Seams whose RS256 signing fails, so the mint puts an error on the track."""

    working = _seams()

    def sign(*, signing_input: str, pem: str) -> IOResult[bytes, GithubAppAuthError]:
        _ = signing_input, pem
        return IOFailure(GithubAppAuthError(detail="openssl could not load the private key"))

    return MintSeams(sign=sign, http_get=working.http_get, http_post=working.http_post)


def _invoke(
    *,
    argv: list[str],
    stdin_text: str,
    environ: dict[str, str] | None = None,
    seams: MintSeams | None = None,
) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = main(
        argv=argv,
        environ=_ENVIRON if environ is None else environ,
        stdin=io.StringIO(stdin_text),
        stdout=stdout,
        stderr=stderr,
        seams=_seams() if seams is None else seams,
    )
    return code, stdout.getvalue(), stderr.getvalue()


def test_get_answers_x_access_token_username_and_minted_password() -> None:
    code, out, err = _invoke(
        argv=["get"],
        stdin_text="protocol=https\nhost=github.com\npath=owner/repo.git\n\n",
    )
    assert code == 0
    assert out == "username=x-access-token\npassword=ghs_helper\n"
    assert err == ""


def test_get_parses_attributes_up_to_eof_and_ignores_malformed_lines() -> None:
    code, out, _err = _invoke(
        argv=["get"],
        stdin_text="not-an-attribute\nprotocol=https\nhost=github.com",
    )
    assert code == 0
    assert "password=ghs_helper" in out


def test_get_missing_env_fails_closed_with_actionable_diagnostic() -> None:
    code, out, err = _invoke(
        argv=["get"],
        stdin_text="protocol=https\nhost=github.com\n\n",
        environ={},
    )
    assert code == 1
    assert out == ""
    assert "GITHUB_APP_ID" in err
    assert "credential_wrapper" in err
    assert "NO fleet fallback" in err


def test_get_mint_failure_fails_closed_with_the_mint_diagnostic() -> None:
    """A config that resolves but a mint that fails still exits 1, naming the cause.

    The config boundary is on the `Result` railway while the mint
    boundary re-raises `GithubAppAuthError`, so these are two distinct
    failure paths through `main`. This covers the mint one: before the
    railway conversion both were discharged by a single `except`, and a
    missing-env test covered the mint branch only incidentally.
    """
    code, out, err = _invoke(
        argv=["get"],
        stdin_text="protocol=https\nhost=github.com\n\n",
        seams=_failing_sign_seams(),
    )
    assert code == 1
    assert out == ""
    assert "openssl could not load the private key" in err


def test_get_non_https_context_emits_no_credential() -> None:
    code, out, err = _invoke(
        argv=["get"],
        stdin_text="protocol=http\nhost=github.com\n\n",
    )
    assert code == 0
    assert out == ""
    assert err == ""


def test_store_and_erase_are_noops_for_the_ephemeral_token() -> None:
    for operation in ("store", "erase"):
        code, out, err = _invoke(
            argv=[operation],
            stdin_text="protocol=https\nhost=github.com\n\n",
        )
        assert code == 0
        assert out == ""
        assert err == ""


def test_unknown_operations_are_ignored_like_git_expects() -> None:
    code, out, _err = _invoke(argv=["capability"], stdin_text="")
    assert code == 0
    assert out == ""


def test_missing_operation_argument_is_a_usage_error() -> None:
    code, out, err = _invoke(argv=[], stdin_text="")
    assert code == 2
    assert out == ""
    assert "usage" in err


def test_run_wires_process_streams_and_environ(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["livespec-github-credential-helper", "get"])
    monkeypatch.setattr(sys, "stdin", io.StringIO("protocol=https\nhost=github.com\n\n"))
    monkeypatch.setattr(sys, "stdout", io.StringIO())
    stderr = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stderr)
    monkeypatch.setattr(os, "environ", {})
    assert run() == 1
    assert "GITHUB_APP_ID" in stderr.getvalue()
