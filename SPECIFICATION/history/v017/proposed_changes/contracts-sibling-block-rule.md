---
topic: contracts-sibling-block-rule
author: claude-opus-4-8
created_at: 2026-07-21T22:49:46Z
---

## Proposal: Correct the lifecycle dependency-blocking rule for sibling_work_item UNKNOWN

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The §`### livespec_runtime.work_items.lifecycle` sentence describing when a dependency blocks readiness states a blanket rule — `CLOSED`/`UNKNOWN` do not block — that the shipped `_entry_blocks` behaviour contradicts as of livespec-runtime v0.12.0 (`8eff84b`). Replace the blanket rule with the per-kind rule the code implements: OPEN blocks any kind, unparseable fails closed, and a `sibling_work_item` that does not resolve to `CLOSED` also fails closed (so UNKNOWN blocks for that kind only), while a `local` UNKNOWN still does not block.

### Motivation

v0.12.0 released the fail-closed fix (bd-ib-qiqz6b clause 1) that makes an unresolved cross-repo sibling dependency block readiness. The code change was correct; the contract sentence describing the old fail-open rule was not amended in the same landing, because the spec tree is lifecycle-governed and a hand-edit would trip doctor-out-of-band-edits. No mechanical gate catches this drift: doctor compares the spec tree against its own history, never against source docstrings or code, so the false sentence survives `just check` and CI green. The drift is now LIVE fleet-wide (the release fanned out and every consumer pin moved off v0.11.0), so a maintainer reading the contract would be actively misled about shipped behaviour. Tracked as livespec-runtime-0h8.

### Proposed Changes

In `SPECIFICATION/contracts.md`, §`### livespec_runtime.work_items.lifecycle`, in the `lane_of` bullet, REPLACE the verbatim sentence:

    "Open dep" reuses the `resolve_ref`/`RefStatus` notion: a dep blocks iff it resolves to `OPEN`, or is unparseable (fail-closed); `CLOSED`/`UNKNOWN` do not block — so lane and readiness agree by construction.

WITH:

    "Open dep" reuses the `resolve_ref`/`RefStatus` notion: a dep blocks iff it resolves to `OPEN` (any kind), is unparseable (fail-closed), or is a `sibling_work_item` that does not resolve to `CLOSED` (also fail-closed — an unresolved cross-repo blocker must not let a candidate slip through as ready). `CLOSED` never blocks; `UNKNOWN` blocks for the `sibling_work_item` kind ONLY — a `local` UNKNOWN (a missing id) does NOT block, since `no-orphan-dependency` owns that case, and `pull_request`/`branch` UNKNOWN keeps its tolerate-partial-visibility semantics — so lane and readiness agree by construction.

This matches `_entry_blocks` on livespec-runtime origin/master exactly: it returns True for `status == RefStatus.OPEN`, for an unparseable entry, and for `entry.kind == "sibling_work_item" and status == RefStatus.UNKNOWN`.

REVIEWER NOTE (replacement-target fidelity): the quoted replace-target is the single logical sentence in the `lane_of` bullet; in the current `contracts.md` it appears line-wrapped across four physical lines (from `"Open dep" reuses the` through `agree by construction.`). It is present verbatim modulo that wrapping — a whitespace-normalized match succeeds — so it is not absent; do not flag the wrap as a missing target.

Only prose inside an existing H3 bullet changes; no `## ` heading is added, changed, or removed, so `tests/heading-coverage.json` needs no co-edit.

SEQUENCING NOTE FOR THE REVISE PASS (not part of the replacement text): the corrected sentence is deliberately worded as the STABLE fail-closed rule ("a sibling_work_item that does not resolve to CLOSED blocks"), which remains accurate after the separate `sibling_status_lookup` follow-up (the second half of bd-ib-qiqz6b) lands — that follow-up only makes more siblings resolve to a concrete CLOSED/OPEN rather than UNKNOWN; it does not change the blocking rule. When that follow-up lands it will amend the DIFFERENT sentences in this same section that document the `lane_of` / `is_item_ready` signatures (adding the injected `sibling_status_lookup` callable), so co-reviewing the two is advisable but neither blocks the other.
