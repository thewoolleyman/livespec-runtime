---
proposal: detect-stale-worktrees-removable.md
decision: accept
revised_at: 2026-11-11T11:59:18Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted as filed under delegated revise authority (legacy-coordinator-agent R301 standing grade; the coordinator routed this revise to the dev-host-disk-retention seat on 2026-11-11, --only-topic detect-stale-worktrees-removable). The contract now states what livespec-runtime#880 (livespec-runtime-gyukpl, released in v0.30.2) implements: detect_stale_worktrees returns only the REMOVABLE candidate set, never a worktree with tracked or untracked entries, because its consumer, livespec's worktree reaper, force-removes what it returns. stale_worktree_findings and scan_hygiene keep reporting a landed worktree whose only dirt is untracked, with the forced removal command. No heading changes.

## Resulting Changes

- contracts.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-11T11:57:41Z
verdict: NO BLOCKERS
proposal_stem: detect-stale-worktrees-removable
content_digest: 17084050e2370180ad685a6b15cca5881a8c559abf0fc36eeee4c0ff1af3f58f
