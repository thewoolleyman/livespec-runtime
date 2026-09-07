---
topic: github-auth-railway-signatures
author: claude-opus-5
created_at: 2026-09-07T13:12:18Z
spec_commitments:
  impl_followups:
    - id_hint: github-auth-railway-signatures-carrier-close
      description: |
        livespec-runtime-zvj is this proposal's carrier and closes on ratification; no product .py changes are owed, because the code is already correct and is the authority this proposal defers to. Verify by re-reading the three signatures against the ratified bullets after the revise pass.
    - id_hint: bda-scenarios-rewrite-unblocked
      description: |
        livespec-runtime-bda's scenario rewrite is gated on this ratification. Once it lands, restate its seven railway-affected Thens in Result/IOResult terms (the model is the existing 'the GithubAppConfig carries ...' phrasing, which never claimed the return value WAS the config), alongside bda's two non-gated fixes and the census/exemption corrections recorded on that item.
---

## Proposal: github-auth-railway-signatures

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Correct three `github_auth` bullets in §"Module-level public surface" that declare a raising API for functions which return `Result`/`IOResult` in the shipped tree, and state the two seam protocols' return types. Impl→spec drift only: the code is correct and unchanged; the prose catches up. Scoped deliberately to the three false bullets, leaving `InstallationTokenProvider.token()` and `credential_helper.main` alone because their raising behaviour is real and intentional.

### Motivation

Measured against master 642d9d6: `load_github_app_config` returns `Result[GithubAppConfig, GithubAppAuthError]`, `sign_rs256_with_openssl` returns `IOResult[bytes, GithubAppAuthError]`, and `mint_installation_token` returns `IOResult[str, GithubAppAuthError]`, while contracts.md declares `-> GithubAppConfig`, `-> bytes`, `-> str` and "MUST raise" for all three. `sign_rs256_with_openssl`'s own docstring says the failure is carried on the failure track rather than raised, and the unit tests assert the railway shape, so the tree is unambiguous. Every consumer reading the ratified contract to decide whether to wrap a credential-mint call in `try` is reading a false statement about three functions on the App-token path. The drift surfaced because the scenarios authored for livespec-runtime-bda transcribed the contract faithfully and therefore asserted a raise seven times; the independent ratification reviewer for that proposal blocked it on exactly this, and bda's rewrite is gated on this correction landing first. Filed as livespec-runtime-zvj. The scope was audited rather than guessed: an earlier draft of that work item speculated the rest of the family might carry the same drift, and the audit found it does not.

### Proposed Changes

`SPECIFICATION/contracts.md` §"Module-level public surface" MUST be corrected so the three `github_auth` bullets below declare the signatures the tree actually ships. The code is the AUTHORITY here and MUST NOT be changed to match the prose; only the prose moves.

**1. `livespec_runtime.github_auth.config`.** The `load_github_app_config` bullet's opening MUST change from `load_github_app_config(*, environ: Mapping[str, str]) -> GithubAppConfig` to `load_github_app_config(*, environ: Mapping[str, str]) -> Result[GithubAppConfig, GithubAppAuthError]`, and its fail-closed sentence MUST change from "any absent-or-empty required variable raises `GithubAppAuthError` naming EVERY missing variable" to "any absent-or-empty required variable MUST put a `GithubAppAuthError` on the failure track naming EVERY missing variable". Everything else in the bullet — the env-only boundary, the four variable names and their REQUIRED/OPTIONAL split, the empty-string-counts-as-missing rule, pointing the operator at the tenant's `credential_wrapper`, and "there MUST NOT be a fallback to any fleet credential" — MUST survive verbatim.

**2. `livespec_runtime.github_auth.signing`.** The `sign_rs256_with_openssl` bullet MUST change from `sign_rs256_with_openssl(*, signing_input: str, pem: str) -> bytes` to `sign_rs256_with_openssl(*, signing_input: str, pem: str) -> IOResult[bytes, GithubAppAuthError]`, and "An unloadable key is an EXPECTED misconfiguration and MUST raise `GithubAppAuthError`" MUST become "An unloadable key is an EXPECTED misconfiguration and MUST land on the failure track as `GithubAppAuthError`".

**3. `livespec_runtime.github_auth.mint`.** The `mint_installation_token` bullet MUST change from `... -> str` to `... -> IOResult[str, GithubAppAuthError]`. Its two raise-phrasings MUST become failure-track phrasings: "any other installation count is an EXPECTED ambiguity that MUST raise `GithubAppAuthError` directing the operator to pin `GITHUB_APP_INSTALLATION_ID`" becomes "... that MUST land on the failure track as `GithubAppAuthError` directing the operator to pin `GITHUB_APP_INSTALLATION_ID`", and "Every EXPECTED failure raises `GithubAppAuthError`" becomes "Every EXPECTED failure lands on the failure track as `GithubAppAuthError`". The rest of that sentence — "caller bugs propagate as built-ins" — is TRUE and MUST survive verbatim, as MUST "The returned token is ephemeral and MUST NOT be persisted at rest".

**4. Completeness, same section.** The `MintSeams` bullet names `SignRs256` / `HttpJson` as "the kw-only `typing.Protocol` seam shapes" without their return types. It SHOULD state them, since both are on the railway and a consumer implementing a seam needs the shape: `SignRs256.__call__(*, signing_input: str, pem: str) -> IOResult[bytes, GithubAppAuthError]` and `HttpJson.__call__(*, url: str, jwt: str) -> IOResult[Any, GithubAppAuthError]`.

**WHAT MUST NOT CHANGE, and why this proposal is deliberately narrow.** Two bullets in the same family look like the same drift and are NOT. `InstallationTokenProvider.token() -> str` genuinely raises: `provider.py`'s docstring records that it re-raises the exact error rather than `unwrap()`ing it, precisely so the boundary consumers catch does not change, and `livespec-orchestrator-beads-fabro` catches `GithubAppAuthError` at two call sites. `credential_helper.main(*, argv, environ, stdin, stdout, stderr, seams) -> int` catches `GithubAppAuthError` and returns exit 1; that is its contract. The raising boundary around a railway interior is deliberate design, and both bullets describe the tree correctly today. A blanket "everything is railway now" correction MUST NOT be applied to either. Likewise this proposal MUST NOT promote `resolve_installation_id`, `http_get_json` or `http_post_json`: `mint.py`'s own `__all__` comment records that they stay module-level and importable but are deliberately NOT declared surface, and adding them would widen the ratified API by accident.
