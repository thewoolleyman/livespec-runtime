---
proposal: scenarios-github-auth-and-work-items.md
decision: accept
revised_at: 2026-09-07T14:42:33Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted as filed after a rewrite and two independent review rounds. Closes the scenario half of gap-vjxowbbp, carried by livespec-runtime-bda: 42 of the two families' 43 documented public names appeared nowhere in scenarios.md, measured mechanically with the public-surface inventory test's own __all__ method (the '# @generated' _fractional_indexing port excluded as that test's register excludes it). The single prior hit was 'main', a prose over-credit of exactly the kind that test's HONEST LIMIT paragraph warns about. THE FIRST REVIEW BLOCKED THESE BYTES' PREDECESSOR with nine defects, all fixed here and all verified against the tree before ratification: the seven github_auth railway Thens, restated in Result/IOResult terms and unblocked by v023; the record-identity line, which had asserted that changing only the supersedes pointer does NOT change the identity when _work_item_to_dict is asdict(item) so the pointer IS in the canonical serialization and the cited test's own body asserts != (its NAME said the opposite, which is what produced the defect - read bodies, never names); and the App-JWT line, which had called exp-iat 'under' the 600s cap when _JWT_SKEW_SECONDS 60 + _JWT_TTL_SECONDS 540 makes it EXACTLY 600, so a literal '< 600' test would fail. FOUR TEST-AUTHORING HAZARDS were folded in, each of which would have produced a test that passes for the wrong reason or cannot pass at all: the sibling-dependency scenario gained the manifest Given that resolve.py:101 needs before the lookup is consulted; the credential-helper get scenario states the injected MintSeams that keep it off real openssl and the network; materialize's tie-break is named as the full (captured_at, identity); and the WorkItemStore scenario says static assignability, never isinstance, because the protocol is not @runtime_checkable and isinstance against it raises TypeError. A TENTH DEFECT surfaced during the rewrite and is why v024 exists: pi3's commit b678542 had replaced ready_sort_key with an aging-aware factory without updating contracts.md, so this proposal's ready_sort_key scenario and its cited node id were both stale. Corrected against the shipped tree and gated behind v024, which ratified first by --only-topic precisely because this proposal is OLDER by creation time. The reviewer verified clause by clause that the corrected scenario now restates the RATIFIED v024 bullet rather than merely matching lifecycle.py. THE SECOND REVIEW found all 32 scenarios sound, 0 defective, and blocked on three claims in the exemption record: a relocation justification that cited spec.md section 'Public surface' for something it never says (the citation runs the other way - tests/heading-coverage.json and tests/public-surface-debt.json cite THAT section as their authority); a false universal claiming every exempted name is exercised as a Given or a Then, when 17 of 23 appear in no scenario; and an inverted claim that DEFAULT_MINT_SEAMS is 'exercised by every mint scenario' when it is the production bundle every mint scenario deliberately DISPLACES by injecting fakes. All three fixed. A fourth, non-blocking, was fixed anyway because a proposal is snapshotted verbatim into history/vNNN/ and stands as ratified prose indefinitely: the opening gloss enumerated only 13 of the 17 unnamed names, and now enumerates all 17 (11 Literal value sets, 1 type alias, 2 Protocol seam shapes, 1 frozen data carrier, the production seam bundle, the process entry point), each category re-derived by the reviewer from the shipped definitions rather than from the sentence. THE EXEMPTION RECORD RELOCATES from scenarios.md to spec.md section 'Public surface', so spec.md joins scenarios.md as a target file. A normative prose register is not Gherkin, and scenarios.md holds only scenario blocks; this clears the template-compliance violation the first reviewer raised. Every one of the 43 names is now the subject of a scenario or named in the record, verified with zero uncovered. The tests/heading-coverage co-edit lands in the same changeset, 32 rows bijective with the 32 new headings, every cited unit-tier node id AST-checked to resolve on disk; the rows are acknowledged TODOs because consumer-tier tests for these families do not exist yet, which is declared as this proposal's impl follow-up rather than dodged.

## Resulting Changes

- scenarios.md
- spec.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-07T14:35:49Z
verdict: NO BLOCKERS
proposal_stem: scenarios-github-auth-and-work-items
content_digest: ed55bebbbbd5130fc2d955e113d849c96c2fa496b94d06b4049c2132d7519419
