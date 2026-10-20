---
proposal: factory-routing.md
decision: modify
revised_at: 2026-10-20T15:39:16Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted in substance per coordinator rulings R318 and R320 (2026-10-20, answering for the maintainer under R202/R301 authority, plan petri-factory-on-gmktec, epic bd-ib-fyozyd): every fleet repository ratifies the same `## Factory routing` heading so the registry-switch work-item can reference it. The section is a configuration constraint on this repository's committed .livespec.jsonc, so it belongs in constraints.md and carries no scenario.

## Modifications

The upstream citation is written at file level, naming the section in prose ("the Fabro factory registry section of livespec-dev-tooling's `non-functional-requirements.md`"), instead of the proposal's section-sign form. This repository's CI runs doctor-no-cross-spec-reference against the pinned livespec core with no sibling clones, so an allowlisted section-sign citation to livespec-dev-tooling cannot be validated there and fails; the file-level form carries the same pointer. No normative wording changes.

## Resulting Changes

- constraints.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-20T15:39:13Z
verdict: NO BLOCKERS
proposal_stem: factory-routing
content_digest: 060ea701f810ae8457d0bb1b964975ceaef95faf5f34393fa65249edbc1e37b7
