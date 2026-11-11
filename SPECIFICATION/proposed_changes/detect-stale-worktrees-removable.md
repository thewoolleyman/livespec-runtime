---
topic: detect-stale-worktrees-removable
author: claude-opus-5-5
created_at: 2026-11-11T10:41:09Z
---

## Proposal: detect_stale_worktrees returns the REMOVABLE candidate set, never a worktree with untracked entries

### Target specification files

- SPECIFICATION/contracts.md

### Summary

State in the contract entry for `detect_stale_worktrees` that its list is the REMOVABLE candidate set: a landed worktree a plain `git worktree remove` accepts, or prunable worktree metadata, never a worktree whose working tree holds any untracked or tracked entry. Reporting such a worktree stays the job of `stale_worktree_findings` and `scan_hygiene`.

### Motivation

Data-loss hazard measured 2026-11-11 by fleet-flaky-tests, and routed by legacy-coordinator-agent to the dev-host-disk-retention plan (livespec-dev-tooling-qgwxo4). The implementation fix is livespec-runtime-gyukpl, and the consumer's own guard is livespec-inmgc7.

- The contract calls the list only 'the stale-worktree CANDIDATE set', so it does not say whether a caller may remove what it returns. livespec-runtime-ciq (v0.22.3) widened the set to landed worktrees whose only dirt is untracked, so they would be reported. Its docstring assumed an unforced remove would refuse them.
- The consumer this entry names, livespec's `dev-tooling/reap_stale_worktrees.py`, removes every candidate with `git worktree remove --force`. On a runtime at v0.22.3 or later it therefore deletes authored untracked files. livespec#3168's check-per-file-coverage run 43002255507 proves it: `test_skips_dirty_worktree` fails because the reaper returned the dirty worktree as reaped.
- legacy-coordinator-agent ruled that the clarification lands as its own proposal, separate from gyukpl, because a factory worker cannot edit `SPECIFICATION/`.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"Module-level public surface", under `### \`livespec_runtime.hygiene_scan\``, replace the `detect_stale_worktrees` bullet:

> - `detect_stale_worktrees(*, repo_path: Path, runner: CommandRunner |
>   None = None) -> list[GitWorktree]` — the stale-worktree CANDIDATE set
>   for `repo_path`. The second signature held for the same cross-repo
>   reason: `livespec`'s worktree reaper consumes it directly.

with:

> - `detect_stale_worktrees(*, repo_path: Path, runner: CommandRunner |
>   None = None) -> list[GitWorktree]` — the REMOVABLE stale-worktree
>   candidate set for `repo_path`. It holds a worktree whose work has
>   landed only when a plain `git worktree remove` would accept it, and
>   it holds worktree metadata git reports prunable. It MUST NOT return a
>   worktree whose `git status --porcelain` shows any entry, tracked or
>   untracked, because its consumer removes what it returns. A landed
>   worktree whose only dirt is untracked is still REPORTED, by
>   `stale_worktree_findings` and `scan_hygiene`, with the forced
>   removal command for an operator. The second signature held for the
>   same cross-repo reason: `livespec`'s worktree reaper consumes it
>   directly.

No `## ` heading is added or removed, so `tests/heading-coverage.json` is unchanged.
