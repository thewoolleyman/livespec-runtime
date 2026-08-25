---
proposal: contracts-railway-idiom.md
decision: modify
revised_at: 2026-08-25T23:43:32Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Recorded as MODIFY. Both filed findings are accepted in substance and verified by EXECUTION against shipped code at v0.22.0, not by reading: retry exhaustion returns IOFailure(RetryExhausted(attempts=3,...)) so the ratified `out is None` test never fires and a conforming consumer treats exhaustion as SUCCESS; and RefStatus('open') raises TypeError, so the ratified deserialization idiom cannot be executed. MODIFY rather than accept because realizing the two corrections coherently required amending clauses the proposal did not name -- three of them in files it did name, plus a companion constraints.md edit. That scope widening was FORCED by joint satisfiability, not discretionary: correcting `retry_with_backoff` to take and return IOResult while the provider bullets still declared `-> str`/`-> bool`, when Resolution semantics mandates those be queried UNDER retry_with_backoff, would have left a type contradiction INSIDE one file. Before this revision contracts.md was uniformly pre-Railway -- wrong against shipped code but internally consistent -- so a partial de-drift would have been strictly worse than none. Independent read-only Fable review ran THREE passes and returned BLOCKERS on the first two, correctly both times; the second pass found that the fixes themselves had turned the gh-absence sentence into the last intra-file contradiction, which is the same closing-one-seam-opens-the-next shape recorded twice inside this single ratification. Final verdict NO BLOCKERS on contracts.md sha256 b6a6a092... and constraints.md sha256 5fb4d7e4.... Maintainer authorization to file this proposal and carry it through the revise flow end to end was given in-pane on 2026-08-26; the scope widening above is reported as part of that completion rather than re-gated, because every added edit is forced by the joint-satisfiability of the two authorized corrections.

## Modifications

Beyond the proposal's two named clauses, this ratification amends four more sites -- three in contracts.md and one in constraints.md, which the proposal did not name as a target.

1. contracts.md, github provider bullets. `query_pull_request_state`, `branch_exists_on_remote` and `branch_merged_into_default` were ratified as `-> str` / `-> bool`; shipped they return `IOResult[..., GithubQueryFailed | GithubBudgetUnmeasurable]`. Restated in that idiom, a `GithubFailure` TypeAlias bullet added (the corrected signatures name it), and 'Any other CalledProcessError propagates' replaced -- `completed_gh` folds it, so nothing propagates. Without this the file contradicts ITSELF once the retry signature is corrected.

2. constraints.md, Provider constraints (companion edit, outside the proposal's named targets). 'Every provider MUST raise on transport failure' contradicted the corrected retry contract across files. Restated: transport failures MUST be surfaced on the FAILURE TRACK as a typed GithubFailure, never raised and never discarded; swallowing stays FORBIDDEN; a raised exception is reserved for a CALLER DEFECT such as the non-canonical URL.

3. contracts.md, `parse_depends_on_entry`. Ratified as RAISING CrossRepoSchemaError; shipped returns `Result[...]` and yields `<Failure: depends_on entry missing required field 'kind'>`. This is the SAME instructs-a-false-green species this proposal exists to remove, sitting in the very section the RefStatus edit touches: a consumer writes a try/except that can never fire, then treats a Failure-carrying Result as a typed entry. Restated, and it now records that `parse_cross_repo_manifest` genuinely DOES still raise, so callers must not assume one idiom covers both boundaries.

4. contracts.md, System dependencies -- two edits. The clause claiming `typing_extensions` is the only non-stdlib runtime dependency is false (pyproject declares `returns>=0.25.0`) and had become self-defeating, since the corrected signatures write IOResult into the ratified contract; `returns` is now named. And the gh-absence sentence claimed absence 'surfaces as CalledProcessError raised by the provider functions' -- false twice over: a missing binary raises FileNotFoundError, and the provider raises neither, folding it via a dedicated `except OSError`. Restated in the failure-track idiom.

Also added: `RetryExhausted` to the public-surface inventory. It is exported in retry.py's __all__ but appeared nowhere in contracts.md, and the corrected retry signature names it. The wider inventory gap (~69 further exported-but-undocumented names) is deliberately NOT in scope and is tracked as livespec-runtime-mqsxsu.4, because some of those names likely warrant REMOVAL from __all__ rather than documentation -- a public-surface narrowing that must be version-classified first.

No `##` heading is added, renamed or removed in either file, so tests/heading-coverage.json needs no co-edit, and no scenario changes: the corrected behavior is already witnessed by tests/livespec_runtime/cross_repo/test_retry.py and by tests.consumer.test_cross_repo_resolution.test_pull_request_dependency_retry_exhaustion_is_unknown.

## Resulting Changes

- constraints.md
- contracts.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-25T23:41:00Z
verdict: NO BLOCKERS
proposal_stem: contracts-railway-idiom
content_digest: 01146a8dcc4df587873c26081b17360a726ec886a75fa35f550e16444d824b3a
