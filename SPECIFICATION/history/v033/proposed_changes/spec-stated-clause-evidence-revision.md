---
proposal: spec-stated-clause-evidence.md
decision: accept
revised_at: 2026-11-09T03:34:56Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted as written under delegated decision mode. The ratified `### livespec_runtime.spec_stated` section listed SpecStatedVerdict's fields as a closed set of four and named no ClauseEvidence, while livespec-orchestrator-beads-fabro's vendored copy already ships and reads `verdict.evidence`. livespec-runtime-bxbyko's factory run 01M6Z4E59TG1 (dispatch ab429cdf) implemented the field and parser, and stopped on the public-surface inventory gate when the export was required. That run's commit is cherry-picked into the same pull request. Measured 2026-11-09: the revise alone on master fails the inventory reverse leg (phantom name livespec_runtime.spec_stated.ClauseEvidence), and the export alone fails the forward leg. So this revise lands in the same commit as the `__all__` export. The ratified_unshipped_modules waiver is module-level and spec_stated ships, so it does not apply. No design record is contradicted. The independent sonnet review returned NO BLOCKERS on these exact bytes, with two optional wording nits left for a later pass: entries' extra keys are tolerated, and the coverage row names only the Then-line test. The new scenario's heading-coverage row binds a real test, so the debt register does not grow. livespec-orchestrator-git-jsonl's vendored copy carries none of this surface and reads no `.evidence`; the defaulted field is additive for it.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-11-09T03:34:01Z
verdict: NO BLOCKERS
proposal_stem: spec-stated-clause-evidence
content_digest: e62735fbcb0b7f698e99e2efdcda6d8dc73191aa1c92ec861f58bcbbf24e6dad
