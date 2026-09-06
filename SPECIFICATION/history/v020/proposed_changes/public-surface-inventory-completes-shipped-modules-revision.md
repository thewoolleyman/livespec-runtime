---
proposal: public-surface-inventory-completes-shipped-modules.md
decision: modify
revised_at: 2026-09-06T14:10:17Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-fable-5-1
---

## Decision and Rationale

Accepted with modifications. Proposals 1, 3, 4 and 5 ratify credentials, the hygiene_scan entry point, spec_governance, and cross_repo.providers.github_process with one bullet per exported name, and declare the seven hygiene_scan size-decomposition split-outs internal by name; Proposal 6 retires the acknowledged-debt paragraph's coverage of those families and records the conscious scenario exemptions and the F-04/F-05 dispositions. Consumption evidence in the motivations is measured and the per-module disposition is what it supports. Proposal 2 (the github_budget facade and its four split-outs) is NOT landed in this revision: the independent ratification review found that ratifying `GithubBudgetedClient`, a deliberately stateful non-frozen dataclass, contradicts constraints.md section "Public-surface constraints" (`Every public dataclass MUST be frozen, slotted, and kw-only`), a conflict the proposal never addresses and whose resolution (a named exception in constraints.md, or a different disposition of the client) is a constraint change outside this proposal's target files and the maintainer's to rule on. The github_budget family therefore stays recorded debt, with the blocking conflict named in spec.md and in the register row. The register co-edit deletes exactly the four rows that go stale on ratification. The maintainer directed the revise on 2026-09-06.

## Modifications

Three modifications. (1) Proposal 2 is withheld: the `### livespec_runtime.github_budget` section is not added to contracts.md, the github_budget row stays in tests/public-surface-debt.json with its reason updated to name the blocking constraint conflict, and the proposal's `narrow-github-budget-split-out-modules` spec->impl commitment is consequently NOT owed by this revision (only `narrow-hygiene-scan-split-out-modules` and `declare-attention-cross-repo-public-api-residue` are filed). Reason: the independent review's blocker that ratifying the non-frozen `GithubBudgetedClient` contradicts constraints.md section "Public-surface constraints"; amending that constraint is a separate proposal for the maintainer. (2) Proposal 6a's spec.md replacement paragraph is redrafted to match: it names credentials, hygiene_scan and spec_governance as the ratified single-import-path families, keeps a second paragraph recording the github_budget family as ACKNOWLEDGED DEBT blocked on the named constraint conflict, and scopes the `# @generated` third-party port out of the every-module claim (the review's non-blocker that the original sentence over-claimed by one module). (3) In the new `### livespec_runtime.spec_governance` section, the sentence citing livespec core's constraints.md with the section-sign form was rephrased to `livespec core's own SPECIFICATION/constraints.md, in its "Locked vendored libs" constraint, names ...`, because this repository's doctor `no-cross-spec-reference` check refuses a section-sign citation of a heading outside this SPECIFICATION/ tree; meaning unchanged. Editorially, each landed family's contracts.md section carries the proposal's `###` heading, intro, per-name bullets, and (for hygiene_scan) the two IMPL CO-REQUISITE paragraphs naming the additive re-exports and the per-module __all__ narrowings, so the intro's `declared internal below` resolves inside the contract; the proposal's Versioning-classification, register-effect, spec.md-pointer, and heading-coverage notes are proposal commentary and are not copied into contracts.md. The new github_process section still names `GhInvocation`, `GithubBudgetFailure` and the process-wide `GithubBudgetedClient` from the unratified family, exactly as the already-ratified providers.github section names `GithubBudgetUnmeasurable`.

## Resulting Changes

- contracts.md
- spec.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-06T14:09:49Z
verdict: NO BLOCKERS
proposal_stem: public-surface-inventory-completes-shipped-modules
content_digest: 84bb8e2a38cac13f028dca5b7da252c3d5c14ace5dbcaf8b26b61f09eb8e38dd
