---
proposal: contracts-sibling-block-rule.md
decision: accept
revised_at: 2026-08-26T10:36:53Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted as filed after re-verifying every claim against current code, because the proposal was authored 2026-07-21 against v0.12.0 and this repo is now past v0.22.0. The replace-target sentence is still present exactly once (whitespace-normalized) in the `lane_of` bullet, so the proposal has not been overtaken. The replacement matches shipped `_entry_blocks` exactly: it blocks on `OPEN` for any kind, on an unparseable entry (fail-closed), and on a `sibling_work_item` that does not resolve to `CLOSED`, while a `local` UNKNOWN still does not block because `no-orphan-dependency` owns that case. The sentence being replaced is a live, fleet-wide-misleading false statement (it describes the fail-open rule that PR #296 removed), tracked as livespec-runtime-0h8, and no mechanical gate catches it because doctor compares the spec tree against its own history rather than against code. The proposal's own wording is deliberately the stable fail-closed rule, so it stays accurate now that the `sibling_status_lookup` follow-up has landed in code. Only prose inside an existing H3 bullet changes, so `tests/heading-coverage.json` needs no co-edit. The adjacent staleness in the same bullet — the documented `lane_of` signature omits the `sibling_status_lookup` parameter the code now takes — is deliberately NOT fixed here: no proposal describes it, and smuggling an unproposed edit into a ratification is exactly the out-of-band change this process forbids; it is surfaced as a follow-up propose-change instead. Independent read-only ratification review by the repository's designated reviewer model returned NO BLOCKERS for these exact bytes.

## Resulting Changes

- contracts.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-26T10:30:53Z
verdict: NO BLOCKERS
proposal_stem: contracts-sibling-block-rule
content_digest: fd2898fdce3a365ace0371d44a2a49bea0a4fc78f229400ca3a8887c74d2d742
