---
proposal: lifecycle-injected-lookup-signatures.md
decision: accept
revised_at: 2026-08-26T12:08:41Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted as filed. All three corrections were verified against shipped code: `lane_of` and `is_item_ready` each declare four keyword-only parameters whose fourth is `sibling_status_lookup: Callable[[str, str], RefStatus] | None = None`, matching the newly documented signatures character-for-character; `sibling_status_lookup` is genuinely injected, threading unchanged to `resolve_ref`; and local status is genuinely derived in-module, since `_entry_blocks` builds `_LocalStatusLookup(index=index)`, which returns UNKNOWN for a missing id, CLOSED for a `done` record, and OPEN otherwise. The replaced prose did not merely simplify: it named a `local_status_lookup` parameter that does not exist on the public surface. The retained no-back-edge assertion survives and is better supported than before, because the old wording justified it by 'both lookups are injected', which was false for the local one, while the new wording justifies it by what the code does; the module imports nothing beads-shaped. The correction also closes the misreading it was filed for: with the parameter documented, a reader can see how a sibling dependency ever escapes UNKNOWN under the per-kind blocking rule ratified in v017, which this pass leaves byte-unchanged. INDEPENDENCE DISCLOSURE, recorded deliberately rather than left implicit: this proposal was AUTHORED BY THE SAME SESSION THAT IS DECIDING IT, earlier the same day, so this ratification did not have the fresh-eyes separation that a proposal inherited from another session provides; and the independent reviewer's model family matches the deciding session's because the repository's `ratification_reviewer_model` was pinned fleet-wide to `opus` today for availability reasons, not chosen for this proposal. Both reductions were surfaced to the reviewer in its own brief so it would read harder as the only independent check, and are recorded here so a maintainer can weigh or reverse them on sight rather than having to reconstruct them. The independent-review floor itself was met in full: a separate, read-only, independently spawned reviewer returned the literal verdict NO BLOCKERS for these exact bytes, having re-computed the content digest itself and confirmed by a word-level diff of the whole file that the only changes are the three intended ones.

## Resulting Changes

- contracts.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-26T12:02:42Z
verdict: NO BLOCKERS
proposal_stem: lifecycle-injected-lookup-signatures
content_digest: ee5d03164284a5d48dd421fceb5ec7e91ab7d553fee40d9bbc328f3ebe81a4b2
