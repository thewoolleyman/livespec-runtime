---
topic: github-auth-http-client-carve-out
author: claude-fable-5
created_at: 2026-07-02T03:39:42Z
---

## Proposal: Scope the no-HTTP-client rule to cross_repo and carve out the github_auth mint

### Target specification files

- SPECIFICATION/constraints.md

### Summary

Narrow the '## Forbidden patterns' no-HTTP-client bullet in SPECIFICATION/constraints.md from a library-wide ban to the livespec_runtime.cross_repo resolution substrate it was written for, and add an explicit carve-out permitting livespec_runtime.github_auth to use stdlib urllib against the https GitHub REST API only. The rule's rationale ('keeps the auth boundary at gh auth') cannot apply to the GitHub App installation-token mint, because the mint is the credential bootstrap that produces the very credential gh consumes.

### Motivation

PR #107 (work-item livespec-u67wdb) landed livespec_runtime/github_auth/ per the fleet contract in livespec core's SPECIFICATION/non-functional-requirements.md (v153): GitHub App installation tokens are the fleet's automation credential, minted on demand via an RS256 App JWT and POST /app/installations/{id}/access_tokens. The mint runs exactly when no gh-visible credential exists yet, so it cannot funnel through the gh subprocess surface; its production HTTP seams use stdlib urllib (https-only, enforced and tested). The pre-existing constraints.md bullet ('No HTTP client (requests, httpx, urllib) inside the library; every external-state query funnels through the gh subprocess surface. This keeps the auth boundary at gh auth.') was authored for the cross_repo resolution substrate before that fleet contract existed, and as written it now contradicts an inherited upstream requirement. This proposal reconciles the repo-local constraint with the landed, spec-mandated implementation; the revise/accept decision is the maintainer's later gate.

### Proposed Changes

In SPECIFICATION/constraints.md under '## Forbidden patterns', replace the bullet:

> - No HTTP client (`requests`, `httpx`, `urllib`) inside the library;
>   every external-state query funnels through the `gh` subprocess
>   surface. This keeps the auth boundary at `gh auth`.

with:

> - No third-party HTTP client (`requests`, `httpx`) anywhere in the
>   library. Within `livespec_runtime.cross_repo`, stdlib `urllib` is
>   ALSO forbidden: every cross-repo external-state query MUST funnel
>   through the `gh` subprocess surface, keeping the resolution
>   substrate's auth boundary at `gh auth`.
> - ONE stdlib-urllib carve-out: `livespec_runtime.github_auth` MAY
>   use stdlib `urllib` against the https GitHub REST API only (the
>   module MUST refuse non-https URLs before any request leaves the
>   process). The App installation-token mint IS the credential
>   bootstrap — it produces the credential that `gh` consumes — so it
>   cannot ride the `gh auth` surface. The carve-out extends no
>   further: `github_auth` MUST NOT grow general-purpose HTTP usage
>   beyond the mint's App-API calls, and every other module remains
>   bound to the `gh` subprocess surface.
