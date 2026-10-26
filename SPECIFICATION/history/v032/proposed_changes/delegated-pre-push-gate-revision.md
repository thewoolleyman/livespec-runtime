---
proposal: delegated-pre-push-gate.md
decision: accept
revised_at: 2026-10-26T23:05:52Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted as written. Plan delegated-gate-fleet-rollout (livespec-dev-tooling-mvalxq) brings this repository into scope under the maintainer direction of 2026-10-24 to enable the delegated pre-push gate on every livespec repo. 'Lefthook pre-push MUST invoke just check' gains the delegation exception. A new bullet adopts, by citation, livespec's Delegated gate execution clause and livespec-dev-tooling's client contract, and adds an explicit rule that authority-reading checks run on the pushing host. Delegation changes where the aggregate runs, never what it verifies. The SKIP_TARGETS precondition holds (PR #781). No design record is contradicted. The independent opus review first found one blocker, outside the spec bytes: the debt register lacked the new TODO row. That row was added, its register test passes, and the re-review returned NO BLOCKERS. Three wording nits, all in the proposal's own text, are left for a follow-up revise.

## Resulting Changes

- non-functional-requirements.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-26T23:05:31Z
verdict: NO BLOCKERS
proposal_stem: delegated-pre-push-gate
content_digest: 54d88b21358e40da5862a92cd87039856a64d453c55358ea24ca4dfc094e8db4
