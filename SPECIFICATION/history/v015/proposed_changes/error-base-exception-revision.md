---
proposal: error-base-exception.md
decision: modify
revised_at: 2026-08-25T15:50:20Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-5
---

## Decision and Rationale

The proposal is correct on its own terms and its remedy is verified satisfiable: the enforced check-no-inheritance allowlist (_ALLOWED_PARENTS in livespec_dev_tooling.checks.no_inheritance) contains Exception and not ValueError, and all five error types this library already ships subclass Exception directly, with github.py's NonCanonicalGithubUrlError docstring stating that convention verbatim. Recorded as MODIFY rather than ACCEPT because accepting it as filed would have shipped this repository's FIFTH jointly-unsatisfiable clause set, and the first to repeat the same species twice: the proposal's new general rule forbids a ValueError base while two ratified clauses in the very two files it edits still mandate one. Those two are co-edited here. One of them, contracts.md's NonCanonicalGithubUrlError bullet, was ALSO live drift against shipped code, which has subclassed Exception since it was written. The other, constraints.md's provider-domain-exception bullet, justified its ValueError requirement as needed 'so the retry layer's broad catch still works'; that rationale is spurious in exactly the way v014's ValueError rationale was, because retry.py's catch is `except Exception` and never depended on a ValueError ancestry. The intent-preservation gate forced explicit maintainer confirmation rather than the configured delegated mode, because the resolution touches ratified statements and no design record is cited or reachable anywhere in this spec tree; the maintainer confirmed the modify disposition in-pane. Independent read-only Fable review returned NO BLOCKERS on these exact bytes.

## Modifications

Beyond the proposal's two named edits (contracts.md's InvalidAttentionItemIdError bullet and the new general rule in constraints.md §"Public-surface constraints"), this ratification co-edits two further clauses in those same two files, both of which the proposal left standing and both of which its own new rule would have contradicted:

1. contracts.md §`livespec_runtime.cross_repo.providers.github`: the NonCanonicalGithubUrlError bullet said '`ValueError` subclass raised when a `github_url` is not the canonical https form'. Rewritten to require subclassing Exception directly, per constraints.md §"Public-surface constraints". This also closes a live drift: livespec_runtime/cross_repo/providers/github.py declares `class NonCanonicalGithubUrlError(Exception)` and its docstring already says 'Inherits `Exception` directly: consumers catch this domain type (or `Exception`), never `ValueError`.'

2. constraints.md §"Provider constraints": future provider-local domain exceptions 'MUST raise `ValueError` subclasses (or a documented sibling class) so the retry layer's broad catch still works'. Rewritten to require subclassing Exception directly, and the stale justification replaced with the verified fact — livespec_runtime/cross_repo/retry.py catches `except Exception`, so it already catches every such exception and no part of the retry path depends on a ValueError ancestry.

Additionally, the proposal's closing paragraph (that the spec must not restate the enforcing check's allowlist) was authored as instruction-to-the-reviser prose rather than as ratifiable text; it is folded into the general rule's own wording so the ratified clause carries it.

No `##` heading is added, renamed, or removed, so tests/heading-coverage.json needs no co-edit, and no new scenario is required: this is a structural public-surface constraint of the same kind as the frozen/slotted/kw-only rule it sits beside, not a new observable behavior.

## Resulting Changes

- constraints.md
- contracts.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-25T15:49:09Z
verdict: NO BLOCKERS
proposal_stem: error-base-exception
content_digest: 95ef146991651c2480a45187a5cb059128315c66d1283e98e0cdc89c3eba7bae
