---
proposal: github-auth-railway-signatures.md
decision: accept
revised_at: 2026-09-07T13:16:19Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted as filed. Impl->spec drift only: contracts.md declared three github_auth functions as raising when the shipped tree returns Result/IOResult, and this corrects the prose while leaving the code untouched — the code is the authority and `git diff 642d9d6 HEAD -- livespec_runtime/github_auth/` is empty, so the cited measurement still describes the tree. The independent reviewer verified all three corrected signatures and both seam protocol shapes line-by-line against config.py, signing.py and mint.py, and confirmed the change is NOT over-corrected: the provider and credential_helper bullets sit outside every diff hunk and are byte-identical, which is right, because token() deliberately ends in `raise unsafe_perform_io(minted.failure())` rather than unwrap() so consumers keep catching GithubAppAuthError, and credential_helper.main catches it and returns exit 1. The three deliberately-not-surface names in mint.py's __all__ comment were not promoted. Every preserved guarantee was checked present: no fleet-credential fallback, caller bugs propagate as built-ins, the token is ephemeral and not persisted, and the four env vars keep their REQUIRED/OPTIONAL split and empty-string-is-missing rule. The fail-closed obligation survives the rewording — 'MUST land on the failure track as GithubAppAuthError' keeps an uppercase MUST on the same actor, now enforced by the return type rather than by a raise. Scope is three hunks inside one section; the three x-release-please-version literals remain byte-identical at v0.27.0. No scenario is owed: scenarios.md contains zero github_auth material today, so no existing scenario is made false, and the scenarios arrive with livespec-runtime-bda, which is gated on this landing. Ratified with --only-topic deliberately: bda's proposal is older by creation time and a whole-directory pass would have processed its raise-asserting scenarios BEFORE this correction.

## Resulting Changes

- contracts.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-07T13:14:04Z
verdict: NO BLOCKERS
proposal_stem: github-auth-railway-signatures
content_digest: 0f1e45af88e6ba2331137eba2e16f7c4cc88dcfbc8ab84723a8d9c6c9c04ee3b
