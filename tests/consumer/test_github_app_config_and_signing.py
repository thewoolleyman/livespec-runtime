"""Consumer-tier scenario tests: App config resolution + App-JWT signing.

Covers EIGHT of the thirty-two `## Scenario:` headings ratified as v025 in
`SPECIFICATION/scenarios.md` — the three `load_github_app_config` scenarios
and the five `livespec_runtime.github_auth.signing` ones — driven exactly as
a consuming tenant drives them: an environ MAPPING handed to the boundary
(never an ambient read), and the pure JWT/PEM helpers plus the openssl signer
called through the ratified module surface.

Every name imported below is ratified in `SPECIFICATION/contracts.md`
section "Module-level public surface". No network anywhere; the only process
spawned is `openssl`, offline, for the sign/verify round-trip the scenario
itself names.

Tier registration: each test below is named by a `tests/heading-coverage.json`
row under the `tests.consumer` node-id prefix declared in `pyproject.toml`
`[tool.livespec_dev_tooling].scenario_tiers`.
"""

import base64
import json
import string
import subprocess
from pathlib import Path
from typing import Any

import pytest
from returns.io import IOFailure, IOSuccess
from returns.pipeline import is_successful
from returns.unsafe import unsafe_perform_io

from livespec_runtime.github_auth.config import (
    DEFAULT_API_URL,
    load_github_app_config,
)
from livespec_runtime.github_auth.errors import GithubAppAuthError
from livespec_runtime.github_auth.signing import (
    b64url,
    jwt_signing_input,
    normalize_pem,
    sign_rs256_with_openssl,
)

__all__: list[str] = []

_PEM = "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n"
_ISSUED_AT = 1_700_000_000

# The App-JWT window the scenario pins: `iat` is backdated 60s for clock skew
# and `exp` is 540s past issuance.
_SKEW_SECONDS = 60
_TTL_SECONDS = 540
_GITHUB_APP_JWT_CAP_SECONDS = 600


def _decode_b64url_json(*, segment: str) -> dict[str, Any]:
    """Decode one unpadded URL-safe base64 JWT segment back to its object."""
    padded = segment + "=" * (-len(segment) % 4)
    decoded: dict[str, Any] = json.loads(base64.urlsafe_b64decode(padded))
    return decoded


def _generate_rsa_key(*, tmp_path: Path) -> tuple[str, Path]:
    """Generate an offline RSA keypair; return (private PEM text, public path)."""
    key_path = tmp_path / "app-key.pem"
    pub_path = tmp_path / "app-key.pub"
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


# ===========================================================================
# App config boundary scenarios
# ===========================================================================


def test_app_config_loads_from_the_credential_wrapper_environment() -> None:
    """Covers scenario "load the App config from the tenant's credential-wrapper environment".

    The consumer hands the boundary the environ its `credential_wrapper`
    injected; the two optional variables are absent, so the config falls back
    to the public API root with no installation pin.
    """
    result = load_github_app_config(environ={"GITHUB_APP_ID": "12345", "GITHUB_PRIVATE_KEY": _PEM})

    assert is_successful(result)
    config = result.unwrap()
    assert config.app_id == "12345"
    assert config.private_key_pem == _PEM
    assert config.api_url == DEFAULT_API_URL
    assert DEFAULT_API_URL == "https://api.github.com"
    assert config.installation_id is None


def test_app_config_resolution_fails_closed_naming_every_missing_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Covers scenario "App config resolution fails closed naming every missing variable".

    The ambient process environment is deliberately populated with a
    COMPLETE, valid credential pair. The boundary reads ONLY the injected
    mapping, so a fleet-level fallback would turn this Failure into a
    Success — which is exactly the "no fleet credential is consulted as a
    fallback" clause, observed rather than asserted by inspection.
    """
    monkeypatch.setenv("GITHUB_APP_ID", "99999")
    monkeypatch.setenv("GITHUB_PRIVATE_KEY", _PEM)

    result = load_github_app_config(environ={"GITHUB_APP_ID": ""})

    assert not is_successful(result)
    failure = result.failure()
    assert isinstance(failure, GithubAppAuthError)
    assert "GITHUB_APP_ID" in failure.detail
    assert "GITHUB_PRIVATE_KEY" in failure.detail
    assert "credential_wrapper" in failure.detail
    assert "NO fleet fallback" in failure.detail


def test_the_optional_installation_pin_and_api_root_override_are_carried() -> None:
    """Covers scenario "the optional installation pin and API-root override are carried into the config"."""
    result = load_github_app_config(
        environ={
            "GITHUB_APP_ID": "12345",
            "GITHUB_PRIVATE_KEY": _PEM,
            "GITHUB_APP_INSTALLATION_ID": "777",
            "GITHUB_API_URL": "https://ghe.example/api/v3",
        }
    )

    config = result.unwrap()
    assert config.installation_id == "777"
    assert config.api_url == "https://ghe.example/api/v3"


# ===========================================================================
# JWT assembly + PEM normalization + RS256 signing scenarios
# ===========================================================================


def test_b64url_encodes_with_the_urlsafe_alphabet_and_no_padding() -> None:
    """Covers scenario "b64url encodes with the URL-safe alphabet and no padding".

    The Given is pinned rather than assumed: this input's STANDARD base64
    really does carry `+`, `/` and trailing `=`, so the URL-safe assertions
    below are witnessing a substitution rather than an input that never
    needed one.
    """
    raw = b"\xfb\xef\xbe\xff"
    standard = base64.b64encode(raw).decode("ascii")
    assert "+" in standard
    assert "/" in standard
    assert standard.endswith("=")

    encoded = b64url(raw=raw)

    assert encoded == "----_w"
    assert set(encoded) <= set(string.ascii_letters + string.digits + "-_")
    assert "=" not in encoded


def test_the_app_jwt_signing_input_is_rs256_header_payload_with_injected_time() -> None:
    """Covers scenario "the App JWT signing input is an RS256 header.payload with caller-injected time".

    ⚠️ THE `exp` - `iat` DISTANCE IS EXACTLY 600 SECONDS (60s of backdated
    skew + a 540s ttl), NOT under it. A literal `assert exp - iat < 600`
    FAILS. What sits under GitHub's 10-minute App-JWT cap is the distance
    from the INJECTED issuance instant to `exp`, which is the 540s ttl —
    the backdating is what buys tolerance for a skewed clock, and it is
    deliberately spent right up to the cap.
    """
    signing_input = jwt_signing_input(app_id="12345", issued_at=_ISSUED_AT)

    header_segment, payload_segment = signing_input.split(".")
    assert _decode_b64url_json(segment=header_segment)["alg"] == "RS256"
    claims = _decode_b64url_json(segment=payload_segment)
    assert claims["iss"] == "12345"
    assert claims["iat"] == _ISSUED_AT - _SKEW_SECONDS
    assert claims["exp"] == _ISSUED_AT + _TTL_SECONDS
    assert claims["exp"] - claims["iat"] == _GITHUB_APP_JWT_CAP_SECONDS
    assert claims["exp"] - _ISSUED_AT < _GITHUB_APP_JWT_CAP_SECONDS


def test_normalize_pem_rewraps_a_flattened_key_and_passes_a_well_formed_one_through() -> None:
    """Covers scenario "normalize_pem re-wraps a flattened key and passes a well-formed PEM through unchanged".

    Three legs, exactly as the scenario states them: a key a secrets manager
    flattened to one line with its newlines collapsed to whitespace is
    re-wrapped at 64 columns; a key whose newlines were written as literal
    backslash-n has them RESTORED with its existing line structure preserved
    rather than re-wrapped; and an already well-formed PEM ending in exactly
    one newline round-trips byte-identically.
    """
    flattened = f"-----BEGIN PRIVATE KEY----- {'A' * 100} -----END PRIVATE KEY-----"
    rewrapped = normalize_pem(raw=flattened).splitlines()
    assert rewrapped[0] == "-----BEGIN PRIVATE KEY-----"
    assert rewrapped[1] == "A" * 64
    assert rewrapped[2] == "A" * 36
    assert rewrapped[3] == "-----END PRIVATE KEY-----"

    escaped = "-----BEGIN PRIVATE KEY-----\\nABC\\nDEF\\n-----END PRIVATE KEY-----"
    restored = "-----BEGIN PRIVATE KEY-----\nABC\nDEF\n-----END PRIVATE KEY-----\n"
    assert normalize_pem(raw=escaped) == restored

    assert normalize_pem(raw=restored) == restored


def test_rs256_signing_round_trips_against_openssl_verify(tmp_path: Path) -> None:
    """Covers scenario "RS256 signing with openssl round-trips against openssl verify".

    The consumer's own acceptance test for the production signer: sign with
    the private half through the ratified entry point, then verify with the
    public half through openssl itself. Offline — the keypair is generated
    into `tmp_path` and no network is touched.
    """
    pem, pub_path = _generate_rsa_key(tmp_path=tmp_path)

    outcome = sign_rs256_with_openssl(signing_input="header.payload", pem=pem)

    assert isinstance(outcome, IOSuccess)
    signature = unsafe_perform_io(outcome.unwrap())
    signature_path = tmp_path / "signature.bin"
    _ = signature_path.write_bytes(signature)
    verified = subprocess.run(
        ["openssl", "dgst", "-sha256", "-verify", str(pub_path), "-signature", str(signature_path)],
        input=b"header.payload",
        capture_output=True,
        check=False,
    )
    assert verified.returncode == 0, verified.stderr.decode("utf-8")


def test_an_unloadable_private_key_is_surfaced_as_a_github_app_auth_error() -> None:
    """Covers scenario "an unloadable private key is an expected misconfiguration surfaced as GithubAppAuthError".

    A key openssl cannot load is an EXPECTED misconfiguration, so it rides
    the failure track with an actionable diagnostic and no exception escapes
    — the call returning at all is itself the "no exception escapes" clause.
    """
    outcome = sign_rs256_with_openssl(signing_input="header.payload", pem="not a key at all")

    assert isinstance(outcome, IOFailure)
    failure = unsafe_perform_io(outcome.failure())
    assert isinstance(failure, GithubAppAuthError)
    assert "GITHUB_PRIVATE_KEY" in failure.detail
    assert "credential_wrapper" in failure.detail
