---
proposal: github-auth-module-contract.md
decision: accept
revised_at: 2026-07-03T02:53:16Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accepted per the maintainer-ordered spec wave (2026-07-03; the maintainer directive is the acceptance authority). Codifies the four contract deltas for the github_auth primitive shipped in v0.7.0 (PR #107, work-item livespec-u67wdb): (1) the env-only fail-closed config boundary (GITHUB_APP_ID + GITHUB_PRIVATE_KEY via the consuming tenant's credential_wrapper, optional GITHUB_APP_INSTALLATION_ID / GITHUB_API_URL, actionable diagnostics naming every missing var, NO fleet fallback); (2) the token lifecycle (mint on demand, process-memory cache only, transparent re-mint at the 55-minute horizon BEFORE the ~1-hour expiry, never persisted at rest); (3) the git credential helper contract (get answers https with username=x-access-token plus the minted token, store/erase no-ops, console script livespec-github-credential-helper as the public entry point); (4) the PEM custody bound (at most a mode-0600 tempfile deleted in a finally). Additions are H3 entries under the existing Module-level public surface H2 plus an openssl System-dependencies bullet and two Forbidden-patterns custody bullets; architecture is specified, mechanism is not. The constraints.md resulting content includes the prior decision's carve-out text (decisions apply in order; this file is the final state).

## Resulting Changes

- contracts.md
- constraints.md
