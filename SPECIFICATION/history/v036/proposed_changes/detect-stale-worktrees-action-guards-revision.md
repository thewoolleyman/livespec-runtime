---
proposal: detect-stale-worktrees-action-guards.md
decision: accept
revised_at: 2026-11-11T12:15:31Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted as filed under delegated revise authority (legacy-coordinator-agent R301; the coordinator asked the dev-host-disk-retention seat on 2026-11-11 to dispose of v035's two review nits, --only-topic detect-stale-worktrees-action-guards). It is a wording-only correction matching the implementation: the landed test is an empty git status, and only the primary checkout is excluded; the caller's current worktree and lock guards belong to the consuming reaper. The independent review's further nits are recorded and left as they are: 'excludes only the primary checkout' does not mention the default-branch and unreadable-status cases, which only narrow the list; one line wraps unevenly; and the prunable case predates this change.

## Resulting Changes

- contracts.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-11T12:14:59Z
verdict: NO BLOCKERS
proposal_stem: detect-stale-worktrees-action-guards
content_digest: 641ae06d3c5640050275df5fbc107f545944a9a21c1c3f6dbddd83664119a2c8
