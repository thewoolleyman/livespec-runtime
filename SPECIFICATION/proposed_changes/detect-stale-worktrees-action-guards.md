---
topic: detect-stale-worktrees-action-guards
author: claude-opus-5-5
created_at: 2026-11-11T12:07:25Z
---

## Proposal: detect_stale_worktrees: state the empty-status test, and that the current-worktree and lock guards belong to the consumer

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Tighten two phrases in v035's `detect_stale_worktrees` entry so they match the implementation. Its test for a landed worktree is an empty `git status --porcelain`; it is not whether a plain `git worktree remove` would accept the worktree. It excludes only the primary checkout, so the worktree the caller stands in and a locked worktree can appear. Skipping those is the consuming reaper's action-layer job.

### Motivation

These are the two non-blocking findings from the independent ratification review of v035 (livespec-runtime#882, 2026-11-11). legacy-coordinator-agent asked the dev-host-disk-retention seat to dispose of them. Neither needs a code change.

- v035 says the list holds a landed worktree 'only when a plain `git worktree remove` would accept it'. A plain remove also refuses a LOCKED worktree, and the detector does not test locks. Its test is an empty working-tree status. The reaper handles locks itself: `_lock_blocks_reap` skips a worktree locked by a live process and unlocks a dead-pid lock before removal.
- `detect_stale_worktrees` excludes only `primary_path`, while `stale_worktree_findings` also excludes `current_path`. That difference is deliberate. livespec's `reap_stale_worktrees.py` documents that the detector 'deliberately excludes only the primary checkout and defers this current-directory guard to the action layer', and `_is_current_worktree` implements that guard.
- As written, the contract could lead a future consumer to assume that locks and the caller's own worktree are already filtered out.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"Module-level public surface", in the `detect_stale_worktrees` bullet, replace:

> It holds a worktree whose work has
>   landed only when a plain `git worktree remove` would accept it, and
>   it holds worktree metadata git reports prunable.

with:

> It holds a worktree whose work has
>   landed only when that worktree's `git status --porcelain` is empty,
>   and it holds worktree metadata git reports prunable. It excludes
>   only the primary checkout: the worktree the caller is standing in,
>   and a locked worktree, can appear, and skipping them is the
>   consuming reaper's action-layer guard, not this function's.

No `## ` heading is added or removed.
