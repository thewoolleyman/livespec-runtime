---
topic: github-auth-module-contract
author: claude-fable-5
created_at: 2026-07-03T02:49:25Z
---

## Proposal: Declare the livespec_runtime.github_auth public surface and contracts

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Codify the github_auth module contract (landed in PR #107, work-item livespec-u67wdb) into the Module-level public surface: the env-only fail-closed config boundary (GITHUB_APP_ID + GITHUB_PRIVATE_KEY via the consuming tenant's credential_wrapper, optional GITHUB_APP_INSTALLATION_ID pin and GITHUB_API_URL override), the mint-on-demand installation-token railway, the caching provider's token lifecycle (process-memory cache only, transparent re-mint at the 55-minute horizon BEFORE the ~1-hour expiry), and the git credential helper protocol with its livespec-github-credential-helper console-script entry point. Also names openssl as a github_auth system dependency alongside gh.

### Motivation

Maintainer-ordered spec wave (2026-07-03): the fleet GitHub-auth primitive shipped in v0.7.0 (PR #107) per the fleet contract in livespec core's SPECIFICATION/non-functional-requirements.md (v153), but this library's own SPECIFICATION does not yet declare any of it. Per the self-application rule, every stable public-API surface must be declared in contracts.md via the propose-change -> revise lifecycle; this proposal specifies architecture (surfaces, env contract, lifecycle invariants), not mechanism.

### Proposed Changes

Under the existing `## Module-level public surface` H2 in SPECIFICATION/contracts.md, append the following H3 entries AFTER `### livespec_runtime.work_items.rank` and BEFORE the `## Resolution semantics` H2 (no new H2 is introduced):

### `livespec_runtime.github_auth.errors`

- `GithubAppAuthError` — `Exception` subclass with a `detail: str` attribute; the single expected-failure domain error on the App-token mint path (missing/rejected credentials, App API rejections, malformed responses). `detail` MUST be an actionable diagnostic naming the specific cause; consumers MAY surface it verbatim.

### `livespec_runtime.github_auth.config`

- `GithubAppConfig` — frozen, slotted, kw-only dataclass: `app_id: str`, `private_key_pem: str`, `api_url: str = DEFAULT_API_URL`, `installation_id: str | None = None`.
- `DEFAULT_API_URL` — `"https://api.github.com"`.
- `load_github_app_config(*, environ: Mapping[str, str]) -> GithubAppConfig` — the env-only input boundary. Inputs come ONLY from environment variables injected by the consuming tenant's `credential_wrapper`: `GITHUB_APP_ID` and `GITHUB_PRIVATE_KEY` (REQUIRED; an empty string counts as missing), `GITHUB_APP_INSTALLATION_ID` (OPTIONAL installation pin) and `GITHUB_API_URL` (OPTIONAL API-root override, e.g. GitHub Enterprise). Resolution MUST fail closed: any absent-or-empty required variable raises `GithubAppAuthError` naming EVERY missing variable and pointing the operator at the tenant's `credential_wrapper`; there MUST NOT be a fallback to any fleet credential.

### `livespec_runtime.github_auth.signing`

- `b64url(*, raw: bytes) -> str` — URL-safe unpadded base64 (the JWS/JWT encoding).
- `jwt_signing_input(*, app_id: str, issued_at: int) -> str` — the unsigned RS256 App-JWT `header.payload`; the caller injects time. The JWT lifetime MUST stay under GitHub's 10-minute App-JWT cap.
- `normalize_pem(*, raw: str) -> str` — re-normalizes secrets-manager-flattened keys to real PEM line structure; a well-formed PEM passes through unchanged.
- `sign_rs256_with_openssl(*, signing_input: str, pem: str) -> bytes` — the production RS256 signer (openssl subprocess). An unloadable key is an EXPECTED misconfiguration and MUST raise `GithubAppAuthError`.

### `livespec_runtime.github_auth.mint`

- `mint_installation_token(*, config: GithubAppConfig, issued_at: int, seams: MintSeams = DEFAULT_MINT_SEAMS) -> str` — mint on demand: sign the App JWT, resolve the installation (the pinned `installation_id`, else sole-installation discovery — any other installation count is an EXPECTED ambiguity that MUST raise `GithubAppAuthError` directing the operator to pin `GITHUB_APP_INSTALLATION_ID`), then `POST /app/installations/{id}/access_tokens`. Every EXPECTED failure raises `GithubAppAuthError`; caller bugs propagate as built-ins. The returned token is ephemeral and MUST NOT be persisted at rest.
- `MintSeams` — frozen, slotted, kw-only seam bundle (`sign`, `http_get`, `http_post`); `SignRs256` / `HttpJson` — the kw-only `typing.Protocol` seam shapes; `DEFAULT_MINT_SEAMS` — the production bundle (openssl signer + stdlib-urllib HTTP). Production HTTP MUST refuse non-https URLs before any request leaves the process.

### `livespec_runtime.github_auth.provider`

- `InstallationTokenProvider` — the token-lifecycle authority: `__init__(*, config, seams=DEFAULT_MINT_SEAMS, clock=time.time)`, `token() -> str`. Tokens are minted on demand at first use and cached in process memory ONLY; `token()` MUST re-mint transparently once the refresh horizon passes — BEFORE the ~1-hour installation-token expiry — so operations that outlive a token never see an expired credential and callers MUST NOT need to handle expiry themselves. Tokens MUST NOT be persisted at rest. The provider is synchronous (no threads, per this library's process boundaries); refresh happens lazily on access.
- `TOKEN_REFRESH_SECONDS` — `3300` (the 55-minute refresh horizon, safely before the ~60-minute expiry).

### `livespec_runtime.github_auth.credential_helper`

- `main(*, argv, environ, stdin, stdout, stderr, seams=DEFAULT_MINT_SEAMS) -> int` — the `git credential` get/store/erase protocol body over injected streams. `get` MUST answer https contexts with `username=x-access-token` plus a freshly minted installation token as the password, and MUST NOT emit a credential for non-https contexts (exit 0 with no output — git treats missing output as "no credential from this helper"). `store` and `erase` MUST be no-ops (the token is ephemeral; there is nothing to persist or erase). A fail-closed credential error MUST print the actionable diagnostic to stderr and exit non-zero; a usage error exits 2.
- `run() -> int` — the process entry wiring the real streams and environment.
- The console script `livespec-github-credential-helper` (declared in pyproject `[project.scripts]`, targeting `run`) is the public entry point; consumers wire it as `git config credential.helper '!livespec-github-credential-helper'`. Renaming or removing the console script is a major-version bump.

Additionally, under the existing `## System dependencies` H2, append one bullet after the `gh auth status` bullet:

- `openssl` CLI — REQUIRED in any environment where consumers mint GitHub App installation tokens via `livespec_runtime.github_auth` (the production RS256 signer shells out to it). Like `gh`, it is NOT pinned by this library; the consumer environment owns the install.

## Proposal: GitHub App credential custody constraints (PEM transit bound; nothing at rest)

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Add credential-custody bullets to '## Forbidden patterns' in SPECIFICATION/constraints.md binding the github_auth secret handling: the App private key PEM may transit AT MOST a mode-0600 temporary file that is deleted in a finally block (the openssl signing seam), and installation tokens are never persisted at rest (process-memory caching only).

### Motivation

Maintainer-ordered spec wave (2026-07-03), delta (4): the PEM is the fleet's durable secret and the installation token its ephemeral derivative (fleet contract, livespec core SPECIFICATION/non-functional-requirements.md v153). The implementation landed in PR #107 already honors these bounds; this proposal makes them binding architecture constraints in the consuming library's own spec tree so a future change relaxing them is a spec violation, not a style regression.

### Proposed Changes

Append the following bullets to the existing `## Forbidden patterns` H2 in SPECIFICATION/constraints.md (no new H2 is introduced):

- The GitHub App private key PEM MUST NOT persist at rest under this library's control. During RS256 signing it MAY transit AT MOST a mode-0600 temporary file, and that file MUST be deleted in a `finally` block regardless of signing outcome. The PEM MUST NOT appear in argv, URLs, logs, or diagnostics.
- GitHub App installation tokens MUST NOT be persisted at rest by this library: caching is process-memory only (the provider), and the `git credential` helper's `store`/`erase` operations MUST remain no-ops. Diagnostics MUST NOT include token values.
