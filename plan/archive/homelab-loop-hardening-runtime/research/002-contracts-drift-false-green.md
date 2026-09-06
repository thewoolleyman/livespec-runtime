# 002 — Two ratified `contracts.md` clauses instruct consumers into false-greens

Status: findings VERIFIED empirically against shipped code at `ab4b1af`
(released `v0.22.0`). Proposal payload prepared but deliberately NOT
materialized — see §"Handoff".

## Why this note exists

The v015 ratification reviewer flagged two `contracts.md` clauses as
non-blocking side observations: the documented `retry_with_backoff`
signature and the `RefStatus` description both describe code this library
does not ship. They were correctly held back from blocking v015 — blocking
there would have left the unsatisfiable v014 `ValueError` clause ratified.

On verification both are worse than "documentation is stale". Each one
instructs a consumer to write code that either crashes or **silently
mistakes failure for success**. That is the same producer-side false-green
species this plan's charge point 4 (`livespec-runtime-emu`) just closed, on
the *consumer* side of the same library.

## Finding 1 — the retry contract manufactures a silent false-green

`SPECIFICATION/contracts.md` §"`livespec_runtime.cross_repo.retry`"
(line 102) ratifies:

> `retry_with_backoff(*, fn: Callable[[], T]) -> T | None` — invokes `fn`
> with the 3-attempt 1s/2s backoff policy. Returns `fn()`'s value on first
> success; returns `None` after all three attempts raise. […] callers
> translate the `None` return into `RefStatus.UNKNOWN` at their own
> resolution boundary.

`livespec_runtime/cross_repo/retry.py:56` ships:

```python
def retry_with_backoff(*, fn: Callable[[], IOResult[T, E]]) -> IOResult[T, RetryExhausted]:
```

Both the parameter type and the return type differ. The consumer-visible
consequence, reproduced against shipped code:

```
exhausted result                     -> IOFailure(RetryExhausted(attempts=3, …))
spec-following check `out is None`   -> False
```

A consumer that implements the ratified sentence — check `is None`,
translate to `RefStatus.UNKNOWN` — never sees `True`. Retry exhaustion is
therefore handled as a **successful result**, and the degradation path that
`constraints.md` §"Forbidden patterns" explicitly requires ("Every
degradation path MUST land at `RefStatus.UNKNOWN`") is never taken. The
ratified contract does not merely fail to describe the code; following it
produces exactly the forbidden pattern.

## Finding 2 — the ratified deserialization idiom raises `TypeError`

`SPECIFICATION/contracts.md` §"`livespec_runtime.cross_repo.types`"
(line 20) ratifies:

> `RefStatus` — `str`-valued Enum with members `OPEN`, `CLOSED`, `UNKNOWN`.
> […] Consumers SHOULD round-trip through JSON by serializing `.value` and
> deserializing via value-lookup (`RefStatus(s)`).

`livespec_runtime/cross_repo/types.py` ships a frozen, slotted, kw-only
dataclass with `value: Literal["open", "closed", "unknown"]` and three
`ClassVar` members assigned after the class body. Verified against shipped
code:

| Claim in the ratified clause | Shipped reality |
|---|---|
| is an `Enum` | `issubclass(RefStatus, Enum)` → `False` |
| is `str`-valued | `issubclass(RefStatus, str)` → `False` |
| `RefStatus(s)` deserializes | raises `TypeError: RefStatus.__init__() takes 1 positional argument but 2 were given` |
| serialize `.value` | works — `RefStatus.OPEN.value == "open"` |

Only the serialization half survives. The ratified deserialization idiom
crashes, and the working form is `RefStatus(value=s)`.

Note this clause is ALSO internally inconsistent with `constraints.md`
§"Public-surface constraints", which requires every public dataclass to be
frozen, slotted, and kw-only — the kw-only rule is precisely what makes the
ratified positional `RefStatus(s)` call impossible. The two clauses cannot
both be honored, which makes this the same jointly-unsatisfiable shape
catalogued five times already in this repo.

## Why no mechanical gate caught either

`doctor` compares the spec tree against its own history, never against
source signatures, so both clauses survive `just check` and a green CI. This
is the identical blind spot recorded for the `NonCanonicalGithubUrlError`
drift closed by v015 — a ratified contract sentence contradicting shipped
code, undetected because nothing compares the two. That makes three
confirmed instances in `contracts.md` alone.

## Prepared proposal payload

Not filed. Both findings target `SPECIFICATION/contracts.md`; the correct
resolution is to restate each clause in the shipped Railway-Oriented idiom
rather than to change the code, because the code is what every consumer
already links against at `v0.22.0` and both shipped shapes are the ones the
ratified `constraints.md` rules require.

- **Finding 1** — replace the `retry_with_backoff` bullet's signature with
  `retry_with_backoff(*, fn: Callable[[], IOResult[T, E]]) -> IOResult[T, RetryExhausted]`,
  and replace the "returns `None` […] callers translate the `None` return"
  sentences with the `IOResult` failure-track description, naming
  `RetryExhausted` and stating that callers translate an `IOFailure` into
  `RefStatus.UNKNOWN`.
- **Finding 2** — replace "`str`-valued Enum" with the shipped shape (a
  frozen/slotted/kw-only dataclass carrying `value: Literal[...]` plus
  `OPEN`/`CLOSED`/`UNKNOWN` `ClassVar` members) and correct the round-trip
  guidance to `RefStatus(value=s)`.

Reviewers of that proposal MUST apply the enforcement-suite lens and the
joint-satisfiability sweep this repo adopted after v015, and MUST confirm no
OTHER `contracts.md` clause still describes the pre-Railway idiom.

## Handoff

`AGENTS.md` §"Agent operating posture" forbids materializing
`SPECIFICATION/proposed_changes/` files on the maintainer's behalf unless the
task explicitly asks for that operation, so this note stops at the payload.
The maintainer runs:

```
/livespec:propose-change --spec-target SPECIFICATION/
```

filing the two findings above as one topic, then ratifies through
`/livespec:revise` with an independent review. Tracked as a work-item under
this plan's epic.
