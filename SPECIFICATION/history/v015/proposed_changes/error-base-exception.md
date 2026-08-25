---
topic: error-base-exception
author: claude-opus-5
created_at: 2026-08-25T15:28:38Z
---

## Proposal: Correct the ratified error base to Exception and ratify the public-error-base rule

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

v014 ratified that `InvalidAttentionItemIdError` "MUST subclass `ValueError`". That clause is unsatisfiable in this repository: the enforced `no_inheritance` check permits a direct base only from the allowlist `BaseException, Exception, Generic, LivespecError, NamedTuple, Protocol, TypedDict`, and `ValueError` is not on it. Every error type this library already exposes subclasses `Exception` directly. This corrects the clause to `Exception` and ratifies the general rule, so the convention is enforced by the specification rather than surviving as an unstated habit.

### Motivation

Found while implementing `livespec-runtime/livespec-runtime-emu` against v014: the product commit was refused by `check-no-inheritance`, which named `ValueError` as a base outside the direct-parent allowlist. The ratified clause therefore could not be implemented without violating an enforced architectural constraint, and the constraint is the correct one — `CrossRepoSchemaError`, `GithubAppAuthError`, `NonCanonicalGithubUrlError`, and `UnterminatedGovernanceBlockError` all subclass `Exception` directly. Worth recording plainly: the stated MOTIVATION for choosing `ValueError` was that consumers already guarding construction with a `ValueError` handler would keep working. That rationale was spurious. Construction never raised before this change, so no such handler could exist, and nothing is preserved by the choice. The clause asserted a compatibility benefit that was impossible by construction. This is the fourth jointly-unsatisfiable clause set ratified in this repository, and the first of a new species: a ratified clause against an ENFORCED CHECK rather than against another clause or the shipped code. The three earlier instances were all caught, or missed, by review lenses that compared spec text to spec text and spec text to source. No lens asked whether the enforcement suite permits what the spec mandates. Ratifying the general rule closes that gap for every future error type, rather than fixing this one symbol and leaving the next author to rediscover the allowlist through a refused commit.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"`livespec_runtime.attention_item`", the `InvalidAttentionItemIdError` bullet's sentence "It MUST subclass `ValueError`." MUST be REPLACED with:

> It MUST subclass `Exception` directly, per `constraints.md` §"Public-surface constraints".

The rest of that bullet, including "Its message MUST name the rejected id", MUST be left intact.

`SPECIFICATION/constraints.md` §"Public-surface constraints" MUST gain the general rule:

> Every public error type this library exposes MUST subclass `Exception` DIRECTLY. Subclassing a builtin exception subclass — `ValueError`, `TypeError`, `RuntimeError`, or any other — is FORBIDDEN, and a specification clause mandating one is a defect in the clause rather than a licence to violate this rule. Consumers MUST catch this library's error types by name, never by a builtin ancestor, so the exception hierarchy stays flat and every raise site is greppable by type.

The spec MUST NOT restate the enforcing check's allowlist, which is owned by the enforcement suite and MAY widen independently; the rule above binds this library's own public error types regardless of what the allowlist happens to permit.
