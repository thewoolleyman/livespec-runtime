---
topic: contracts-railway-idiom
author: claude-opus-5
created_at: 2026-08-25T23:21:13Z
---

## Proposal: Restate the retry contract in the shipped Railway idiom

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The ratified `retry_with_backoff` bullet declares `(*, fn: Callable[[], T]) -> T | None` and instructs callers to translate a `None` return into `RefStatus.UNKNOWN`. The shipped function takes and returns `IOResult`. A consumer implementing the ratified sentence checks `is None`, never gets True, and so handles retry exhaustion as a SUCCESS -- producing the exact silent fallback that constraints.md §"Forbidden patterns" forbids.

### Motivation

Verified against shipped code at ab4b1af (released v0.22.0) by RUNNING it, not by reading: with `fn` always raising, `retry_with_backoff` returns `IOFailure(RetryExhausted(attempts=3, ...))`, and the ratified `out is None` test evaluates False. constraints.md §"Forbidden patterns" ratifies that every degradation path MUST land at `RefStatus.UNKNOWN` and that no silent fallback may hide a transport error. So the two ratified clauses cannot both be honored: following the retry contract produces the forbidden pattern. This is the same false-green species that livespec-runtime-emu closed on the PRODUCER side of this library (a shortened list indistinguishable from a quiet repo); here it is the CONSUMER side of the same library, and it is worse, because the consumer is following a ratified instruction rather than hitting an undocumented edge. No mechanical gate catches it: doctor compares the spec tree against its own history, never against source signatures, so the clause survives `just check` and green CI. Tracked as livespec-runtime-mqsxsu.3; full evidence and reproduction in plan/homelab-loop-hardening-runtime/research/002-contracts-drift-false-green.md.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"### `livespec_runtime.cross_repo.retry`", REPLACE the `retry_with_backoff` bullet's signature and its return-value sentences.

REPLACE the signature `retry_with_backoff(*, fn: Callable[[], T]) -> T | None` WITH `retry_with_backoff(*, fn: Callable[[], IOResult[T, E]]) -> IOResult[T, RetryExhausted]`.

REPLACE the sentences "Returns `fn()`'s value on first success; returns `None` after all three attempts raise." and the following "Exceptions raised by `fn` are caught broadly; callers translate the `None` return into `RefStatus.UNKNOWN` at their own resolution boundary." WITH text stating that the function returns `fn()`'s success value re-lifted onto the success track on the first attempt that lands there; that after all three attempts fail it returns an `IOFailure` carrying `RetryExhausted`, whose `attempts` and `detail` fields describe the final failure; that exceptions raised by `fn` are caught broadly and folded onto the same failure track; and that callers MUST translate an `IOFailure` into `RefStatus.UNKNOWN` at their own resolution boundary.

The replacement MUST NOT retain any `None`-sentinel wording, because the sentinel reading is precisely what makes a consumer treat exhaustion as success. The 3-attempt 1s/2s policy description and the reserved-but-unused 4.0s constant note are correct and MUST be left intact.

No `##` heading is added, renamed, or removed, so `tests/heading-coverage.json` needs no co-edit. The behavior is already covered by `tests.livespec_runtime.cross_repo.test_retry` and by `tests.consumer.test_cross_repo_resolution.test_pull_request_dependency_retry_exhaustion_is_unknown`, which is already mapped from `constraints.md` §"Forbidden patterns" -- the very clause this correction makes satisfiable.

## Proposal: Restate RefStatus as the shipped dataclass and fix the round-trip guidance

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The ratified `RefStatus` bullet describes a `str`-valued Enum and instructs consumers to deserialize via value-lookup `RefStatus(s)`. The shipped type is a frozen, slotted, kw-only dataclass: not an Enum, not a `str`, and `RefStatus("open")` raises `TypeError`. The ratified deserialization idiom cannot be executed.

### Motivation

Verified against shipped code at ab4b1af (released v0.22.0) by running it: `issubclass(RefStatus, Enum)` is False, `issubclass(RefStatus, str)` is False, and `RefStatus("open")` raises `TypeError: RefStatus.__init__() takes 1 positional argument but 2 were given`. Only the serialization half of the ratified guidance survives -- `.value` is real -- so a consumer following the round-trip instruction gets a working serialize and a crashing deserialize. The clause is ALSO jointly unsatisfiable with constraints.md §"Public-surface constraints", which requires every public dataclass to be frozen, slotted and kw-only: the kw-only rule is exactly what makes the ratified positional call impossible. That makes this the sixth jointly-unsatisfiable clause set ratified in this repository, and the third confirmed spec-vs-code drift in contracts.md alone (with the retry finding and the NonCanonicalGithubUrlError bullet v015 corrected). Tracked as livespec-runtime-mqsxsu.3.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"### `livespec_runtime.cross_repo.types`", REPLACE the `RefStatus` bullet's type description and round-trip guidance.

REPLACE "`RefStatus` — `str`-valued Enum with members `OPEN`, `CLOSED`, `UNKNOWN`. The `.value` strings are the lowercase member names (`"open"`, `"closed"`, `"unknown"`)." WITH a description of the shipped shape: a frozen, slotted, kw-only dataclass carrying `value: Literal["open", "closed", "unknown"]`, exposing `OPEN`, `CLOSED` and `UNKNOWN` as `ClassVar` members assigned after the class body, with the members comparing equal by value.

REPLACE the round-trip instruction so that consumers serialize `.value` (unchanged, and correct) and deserialize via the KEYWORD form `RefStatus(value=s)`. The positional `RefStatus(s)` form MUST NOT appear, because constraints.md §"Public-surface constraints" mandates kw-only construction and the positional call therefore raises `TypeError`.

Any surrounding sentence that depends on Enum semantics -- identity-based membership, iteration over members, or `str` comparison -- MUST be corrected or removed in the same edit; the reviser MUST re-read the whole bullet rather than patching only the quoted spans.

No `##` heading is added, renamed, or removed, so `tests/heading-coverage.json` needs no co-edit. Note for the reviser: the enclosing heading `## Module-level public surface` is the ONE heading-coverage entry still carrying a placeholder, deliberately held by livespec-runtime-mqsxsu.2 pending this correction; it can be adjudicated once this lands.
