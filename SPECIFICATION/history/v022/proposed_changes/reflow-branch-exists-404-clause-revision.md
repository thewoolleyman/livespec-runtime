---
proposal: reflow-branch-exists-404-clause.md
decision: accept
revised_at: 2026-09-07T12:29:13Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted as filed. A whitespace-only re-wrap of the branch_exists_on_remote bullet, proven so rather than asserted: whole-file whitespace-normalized equality is true, and the independent reviewer corroborated with a strict CommonMark render that is identical modulo whitespace, one HTML hunk confined to the same list item, backticks 16 to 16 and SHOULD / MUST NOT / MAY each 1 to 1. The region's two over-80 lines (85 and 123 columns) are gone at max width 78, and the file-wide count drops 20 to 18 — exactly the region's count, so nothing elsewhere grew. This content was REGENERATED after release 0.27.0 landed mid-pass: the first computation would have reverted three x-release-please-version literals from v0.27.0 to v0.26.0, and the reviewer confirmed on the rebased bytes that all three sentinel lines are byte-identical and sit outside the edit region. The 123-column line is the one carrying the clause's MUST NOT, so legibility here has real value; the fix is targeted, since the 18 remaining over-80 lines are unwrapped IMPL CO-REQUISITE paragraphs and fenced TOML, neither of which is wrapped prose.

## Resulting Changes

- contracts.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-07T12:27:27Z
verdict: NO BLOCKERS
proposal_stem: reflow-branch-exists-404-clause
content_digest: 76cc794ad984ee999529657a40bac52b154dca8b5bf4757d803334e0c422e568
