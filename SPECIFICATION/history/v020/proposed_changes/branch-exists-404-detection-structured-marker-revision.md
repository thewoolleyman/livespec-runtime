---
proposal: branch-exists-404-detection-structured-marker.md
decision: accept
revised_at: 2026-09-06T14:10:17Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-fable-5-1
---

## Decision and Rationale

Accepted as filed. The existing clause names a mechanism (gh's exit code) that cannot discriminate a 404 because gh exits 1 for every API failure; the replacement names the mechanisms that work (gh api's structured `(HTTP 404)` stderr marker line or an explicit status header), keeps the structured-field intent by requiring a typed field rather than caller-side stderr matching, and adds a MUST NOT on the exit code. Observable behaviour (404 -> False on the success track; other failures -> GithubFailure) is unchanged, so no scenario is owed. This is the accept-as-satisfied disposition the batch-1 triage ruling on plan runtime-backlog-drain (livespec-runtime-c7toen) recorded for livespec-runtime-5s4ax2 / gap-nyckdcxc; the maintainer directed the revise on 2026-09-06.

## Resulting Changes

- contracts.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-06T14:05:17Z
verdict: NO BLOCKERS
proposal_stem: branch-exists-404-detection-structured-marker
content_digest: dd732202aa645ba7b9576f572bd9267664c16abfa0e1bef23650a90dca5966a3
