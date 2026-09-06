---
proposal: ratify-github-budget-family.md
decision: accept
revised_at: 2026-09-06T16:27:34Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted as filed. This re-lands the github_budget section withheld at v020, and the reason it was withheld is discharged rather than argued away: the independent review blocked ratifying a deliberately non-frozen GithubBudgetedClient against constraints.md's unqualified frozen-dataclass rule, the maintainer ruled on 2026-09-06 that the constraint stays absolute and the code changes (declining both a constraint amendment and parking the family as debt), and livespec-runtime-kd7hjn landed that refactor through the factory as PR #673 (merge aca26b3). The client is now @dataclass(frozen=True, slots=True, kw_only=True) over a module-private _ClientState holder absent from every __all__, with its construction and request signatures byte-identical, so the section's corrected bullet describes the tree as it stands. The rest of the section is the withheld text verbatim and its measured consumption evidence is unchanged: the facade is ratified because GithubBudgetUnmeasurable already sits in the ratified GithubFailure union and the ratified github_process signatures name GhInvocation and GithubBudgetFailure, while the four split-outs are declared internal because no repository outside this one imports them. The register co-edit deletes only the facade row; the four split-out rows stay until the narrowing changeset (livespec-runtime-cl5aqq) empties their __all__. With this accepted, spec.md's acknowledged-debt paragraph retires and no shipped module that declares a public surface remains outside the inventory.

## Resulting Changes

- contracts.md
- spec.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-06T16:27:10Z
verdict: NO BLOCKERS
proposal_stem: ratify-github-budget-family
content_digest: b768bab9121f679d954b4b2c41fa4c73eefbf04a864fdd982cc2a438a00b3291
