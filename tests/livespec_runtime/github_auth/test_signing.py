"""Tests for `livespec_runtime.github_auth.signing` (+ the errors module).

Verifies the App JWT assembly (RS256 header; backdated `iat`; an `exp`
well under GitHub's 10-minute cap; `iss` = App id), the URL-safe
unpadded base64 encoding, the PEM re-normalization for
secrets-manager-flattened keys, and the openssl-subprocess RS256
production signer via an offline generate → sign → verify round-trip.
No network anywhere.

Design reference: livespec core repo,
plan/github-app-auth/research/01-design.md (Pillar 1).
"""

import base64
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from livespec_runtime.github_auth.errors import GithubAppAuthError
from livespec_runtime.github_auth.signing import (
    b64url,
    jwt_signing_input,
    normalize_pem,
    sign_rs256_with_openssl,
)

__all__: list[str] = []


def _decode_b64url_json(part: str) -> dict[str, Any]:
    padded = part + "=" * (-len(part) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def test_b64url_uses_urlsafe_alphabet_without_padding() -> None:
    assert b64url(raw=b"\xfb\xef\xbe") == "----"
    assert b64url(raw=b"a") == "YQ"


def test_jwt_signing_input_is_rs256_header_dot_backdated_claims() -> None:
    signing_input = jwt_signing_input(app_id="123456", issued_at=1_700_000_000)
    header_part, payload_part = signing_input.split(".")
    assert _decode_b64url_json(header_part) == {"alg": "RS256", "typ": "JWT"}
    payload = _decode_b64url_json(payload_part)
    assert payload["iss"] == "123456"
    assert payload["iat"] == 1_700_000_000 - 60
    assert payload["exp"] == 1_700_000_000 + 540


def test_normalize_pem_passthrough_with_real_newlines() -> None:
    pem = "-----BEGIN RSA PRIVATE KEY-----\nMIIBOgIBAAJBAKj3\n-----END RSA PRIVATE KEY-----"
    assert normalize_pem(raw=pem) == pem + "\n"


def test_normalize_pem_rewraps_flattened_single_line() -> None:
    body = "A" * 100
    flat = f"-----BEGIN PRIVATE KEY----- {body} -----END PRIVATE KEY-----"
    normalized = normalize_pem(raw=flat)
    lines = normalized.splitlines()
    assert lines[0] == "-----BEGIN PRIVATE KEY-----"
    assert lines[1] == "A" * 64
    assert lines[2] == "A" * 36
    assert lines[3] == "-----END PRIVATE KEY-----"
    assert normalized.endswith("-----END PRIVATE KEY-----\n")


def test_normalize_pem_converts_literal_backslash_n_to_newlines() -> None:
    pem = "-----BEGIN PRIVATE KEY-----\\nABC\\n-----END PRIVATE KEY-----"
    expected = "-----BEGIN PRIVATE KEY-----\nABC\n-----END PRIVATE KEY-----\n"
    assert normalize_pem(raw=pem) == expected


def test_normalize_pem_non_pem_single_line_passes_through() -> None:
    assert normalize_pem(raw="not a pem at all") == "not a pem at all"


def _generate_rsa_key(tmp_path: Path) -> tuple[str, Path]:
    key_path = tmp_path / "key.pem"
    pub_path = tmp_path / "key.pub"
    _ = subprocess.run(
        [
            "openssl",
            "genpkey",
            "-algorithm",
            "RSA",
            "-pkeyopt",
            "rsa_keygen_bits:2048",
            "-out",
            str(key_path),
        ],
        check=True,
        capture_output=True,
    )
    _ = subprocess.run(
        ["openssl", "pkey", "-in", str(key_path), "-pubout", "-out", str(pub_path)],
        check=True,
        capture_output=True,
    )
    return key_path.read_text(encoding="utf-8"), pub_path


def test_sign_rs256_with_openssl_round_trips_with_openssl_verify(tmp_path: Path) -> None:
    pem, pub_path = _generate_rsa_key(tmp_path)
    signature = sign_rs256_with_openssl(signing_input="header.payload", pem=pem)
    assert signature != b""
    sig_path = tmp_path / "sig.bin"
    _ = sig_path.write_bytes(signature)
    verify = subprocess.run(
        [
            "openssl",
            "dgst",
            "-sha256",
            "-verify",
            str(pub_path),
            "-signature",
            str(sig_path),
        ],
        input=b"header.payload",
        capture_output=True,
        check=False,
    )
    assert verify.returncode == 0, verify.stderr.decode("utf-8")


def test_sign_rs256_with_openssl_accepts_flattened_pem_after_normalize(tmp_path: Path) -> None:
    pem, _pub_path = _generate_rsa_key(tmp_path)
    flattened = pem.replace("\n", "\\n")
    signature = sign_rs256_with_openssl(
        signing_input="header.payload", pem=normalize_pem(raw=flattened)
    )
    assert signature != b""


def test_sign_rs256_with_openssl_unloadable_key_raises_actionable_error() -> None:
    with pytest.raises(GithubAppAuthError) as excinfo:
        _ = sign_rs256_with_openssl(signing_input="header.payload", pem="not a key")
    assert "openssl could not sign" in excinfo.value.detail


def test_github_app_auth_error_str_is_detail() -> None:
    error = GithubAppAuthError(detail="the actionable diagnostic")
    assert error.detail == "the actionable diagnostic"
    assert str(error) == "the actionable diagnostic"
