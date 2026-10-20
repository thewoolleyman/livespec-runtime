---
proposal: spec-stated-judgement.md
decision: modify
revised_at: 2026-10-20T11:18:50Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-fable-5-1:spec-implementation-lockstep
---

## Decision and Rationale

Accepted with modifications under the delegated revise_decision_mode of this repository's .livespec.jsonc spec_governance, by session spec-implementation-lockstep for plan epic bd-ib-ax3rds in livespec-orchestrator-beads-fabro (Definition of Done assertion 6: both orchestrators run the same is-this-stated-by-the-spec judgement from livespec-runtime). The family meets the Scope boundary admission test: two producers, livespec-orchestrator-beads-fabro and livespec-orchestrator-git-jsonl, construct and store its SpecChangeTier values, and its inputs are consumer-neutral. The section precedes its module under the v026 ratified_unshipped_modules register: the same commit adds the row naming livespec_runtime.spec_stated and its owning work-item livespec-runtime-krpzzb to tests/public-surface-debt.json, and repairs the consumer-tier waiver test so its injected row is appended to the shipped register instead of replacing it. The configured ratification reviewer, opus, in a separate read-only session, returned NO BLOCKERS on the exact resulting bytes. Its non-blocking findings are recorded on the implementing work-item livespec-runtime-krpzzb.

## Modifications

Two repairs on top of the proposal text, both reviewed on the exact resulting bytes: M1, the new livespec_runtime.spec_stated section's first sentence states that livespec core names NO slot for it, because the contracts.md introduction requires every shared-runtime section to say so in its own text; M2, the SpecStatedParseError bullet names it as the Failure payload of judge, classify and parse_verdict, not of parse_verdict alone, because judge and classify return it on their Failure track.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-20T11:18:04Z
verdict: NO BLOCKERS
proposal_stem: spec-stated-judgement
content_digest: 120807d51ece0ce54ef47d181b64ae97ab73c96ac0391c3a623101c7ce5597f0
