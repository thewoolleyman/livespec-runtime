---
proposal: ready-sort-key-aging-signature.md
decision: accept
revised_at: 2026-09-07T14:29:23Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted as filed. Impl->spec drift only, the same class as v023: contracts.md declared the retired ready_sort_key(item: WorkItem) -> tuple[...] shape while the shipped tree has, since commit b678542 (livespec-runtime-pi3, 'aging-aware ready_sort_key equal-rank tiebreak'), a keyword-only FACTORY returning a callable over (rank, aging tier, ready-instant order, id). That commit touched lifecycle.py, its tests and a CLAUDE.md and ZERO SPECIFICATION/ paths, which is how the prose was left behind. The code is the authority and no product .py changes: git shows livespec_runtime/work_items/lifecycle.py untouched by this changeset. The drift was caught mechanically rather than by reading — a check that every unit-tier node id cited by the sibling scenarios proposal still resolves on disk found test_ready_sort_key_orders_by_rank_then_id gone. The independent reviewer verified every sentence of the replacement bullet line by line against lifecycle.py: the signature, keyword-only-ness, the 24.0 default threshold, the tuple[str,int,float,str] key type, and in particular the tier boundary, where the un-aged branch is taken on '<=' (lifecycle.py:250) so the prose 'LONGER than' matches the operator exactly rather than hiding a silent '>=' slip. It confirmed the change is NOT over-corrected: ready_sort_key appears exactly once in the live spec, and the neighbouring bullets were checked and correctly left alone — the Dispatcher drain-order bullet is about eligibility rather than ordering, and rank-as-'sole ordering authority' survives because that clause is about RECORD FIELDS (its rationale is the removed priority field) while ready_since is not a WorkItem field at all but an injected lookup. The reviewer independently reproduced the canonical digest and verified on the final bytes that the diff is a single hunk, that the three x-release-please-version sentinel literals are byte-identical at v0.27.0 and merely shifted by the hunk's +19 lines, and that everything before and after the hunk is byte-identical. One blocker was raised and fixed before ratification: created_at had been stamped 2026-09-07T15:52:00Z, the local +0200 wall clock labelled Z, which is ~2h in the future and post-dates its own commit. That field is load-bearing twice over — revise orders pending proposals by it, and the ratification-evidence check rejects any reviewed_at preceding it, so the wrong value would have refused every honest review of this proposal. Corrected to 13:33:00Z in PR #691. Ratified with --only-topic deliberately: the sibling scenarios-github-auth-and-work-items proposal is OLDER by creation time (12:01:43Z), and a whole-directory pass would ratify its corrected ready_sort_key scenario BEFORE this correction makes that scenario true.

## Resulting Changes

- contracts.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-07T13:50:24Z
verdict: NO BLOCKERS
proposal_stem: ready-sort-key-aging-signature
content_digest: cd015eb3a3f01afdae5fd8ae0fbfcff25e4a353b17b8a9ee3eeb1c23c55cbf48
