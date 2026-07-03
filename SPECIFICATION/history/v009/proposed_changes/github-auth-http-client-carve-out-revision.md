---
proposal: github-auth-http-client-carve-out.md
decision: accept
revised_at: 2026-07-03T02:53:16Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-fable-5
---

## Decision and Rationale

Accepted per the maintainer-ordered spec wave (2026-07-03; the maintainer directive is the acceptance authority). The pre-existing library-wide no-HTTP-client bullet was authored for the cross_repo resolution substrate before the v153 fleet contract made App-token minting a requirement; the mint is the credential bootstrap that produces the credential gh consumes, so it cannot ride the gh-auth surface. The replacement keeps third-party HTTP clients banned library-wide, keeps stdlib urllib banned within cross_repo, and bounds the github_auth carve-out to the https GitHub REST API only. Matches the implementation landed in PR #107.

## Resulting Changes

- constraints.md
