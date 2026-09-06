---
topic: ratify-github-budget-family
author: claude-opus-5
created_at: 2026-09-06T16:23:08Z
spec_commitments:
  impl_followups:
    - id_hint: narrow-github-budget-split-out-modules
      description: |
        Land the narrowing this proposal's section declares: narrow `__all__` to `[]` in github_budget_client, github_budget_client_support, github_budget_measurement, and github_budget_types; add GithubBudgetResult and GithubBudgetTransport to livespec_runtime/github_budget.py's re-exports and `__all__`, so every type naming a ratified signature is expressible from the ratified import path; delete those four rows from tests/public-surface-debt.json (they go stale only when the `__all__` empties, because the inventory check reads the tree). The commit subject carries a `!` marker and a BREAKING CHANGE footer so release_bump_classification accepts the surface delta; the Major classification releases as a MINOR 0.X.0 bump under the pre-major provision. Already filed as livespec-runtime-cl5aqq, carried over from the withheld v020 Proposal 2.
---

## Proposal: Ratify the livespec_runtime.github_budget facade and declare its four split-out modules internal, now that GithubBudgetedClient is frozen

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md

### Summary

Re-lands the github_budget half of the v020 public-surface reconciliation, which was withheld at that revise. RATIFY the facade `livespec_runtime.github_budget` with one bullet per exported name, and DECLARE INTERNAL its four size-decomposition split-outs by narrowing each `__all__` to `[]` in the commitment changeset. The one change from the withheld text is the `GithubBudgetedClient` bullet, which now documents a FROZEN dataclass over a module-private state holder rather than a deliberately non-frozen one. With this accepted, spec.md's acknowledged-debt paragraph retires entirely and no shipped module that declares a public surface remains outside the inventory.

### Motivation

At the v020 revise (2026-09-06) the independent ratification review BLOCKED this family: the facade exported `GithubBudgetedClient` as `@dataclass(slots=True, kw_only=True)`, deliberately not frozen because it holds the conditional-read cache, the mutation-pacing clock and a mutation lock, while `constraints.md` §"Public-surface constraints" requires every public dataclass to be frozen without qualification. Ratifying it would have made the specification contradict itself, so the section was withheld and the family stayed recorded debt with the conflict named in spec.md and in the register.

The maintainer ruled on 2026-09-06 that the CONSTRAINT STAYS ABSOLUTE and the code changes: amending constraints.md with a stateful-client exception was offered and DECLINED, as was parking the family as debt. `livespec-runtime-kd7hjn` landed that refactor through the factory (PR #673, merge aca26b3): `GithubBudgetedClient` is now `@dataclass(frozen=True, slots=True, kw_only=True)`, its three mutable pieces live on a module-private `_ClientState` holder the client owns and mutates through, and the construction and `request` signatures are byte-identical to their pre-change form. The blocker is therefore discharged in the direction the constraint demanded, and the withheld section can land with its client bullet corrected.

The remaining substance is unchanged from the withheld proposal and its measured evidence stands: the facade is RATIFIED because `GithubBudgetUnmeasurable` is already a member of the ratified `GithubFailure` union documented under `### livespec_runtime.cross_repo.providers.github`, and the ratified `cross_repo.providers.github_process` section names `GhInvocation` and `GithubBudgetFailure` in its own signatures, so these types are consumer-visible by construction. The four split-outs are DECLARED INTERNAL because, measured across the nine fleet member checkouts on 2026-09-06, no repository outside this one imports any `github_budget*` module; they exist because `file_lloc` hard-gates this repo at 250 LLOC, and ratifying helpers such as `header_value` and `mapping_option` would pin plumbing as v1 stable API and contradict this repo's own `total_absence_returns` declaration about them.

### Proposed Changes

### 1. `SPECIFICATION/contracts.md` — ratify the family

In §"Module-level public surface", INSERT the following `###` section immediately after `### `livespec_runtime.hygiene_scan`` and immediately before `### `livespec_runtime.spec_governance``, which is the placement the withheld v020 Proposal 2 specified.

### `livespec_runtime.github_budget`

SHARED-RUNTIME contract per `spec.md` §"Scope boundary": `livespec` core
names NO slot for GitHub request budgeting. This module is the family's
SINGLE ratified import path; its four companion modules
(`github_budget_client`, `github_budget_client_support`,
`github_budget_measurement`, `github_budget_types`) are size-decomposition
split-outs declared internal below and MUST NOT be imported directly.
The consuming producer inside this library is
`livespec_runtime.cross_repo.providers.github_process`, and the family is
consumer-visible because the ratified provider failure union
`GithubFailure` names `GithubBudgetUnmeasurable`: a consumer that lands on
a provider's failure track holds one of these records.

- `GhInvocation` — frozen, slotted, kw-only dataclass. Fields:
  `argv: str` (REQUIRED, shell-quoted so an operator can rerun it),
  `stdout: str = ""`, `stderr: str = ""`, `returncode: int = 0`,
  `unspawnable: str | None = None`. `unspawnable` is the ONE structural
  failure — the binary is missing or the process could not start — and is
  distinct from a run that happened and exited non-zero.
- `GhExecutor` — the `TypeAlias` `Callable[..., GhInvocation]`: what
  spawns one `gh` argv.
- `GithubRateLimitSnapshot` — frozen, slotted, kw-only dataclass parsing
  GitHub's `x-ratelimit-*` response headers. Fields: `limit: int`,
  `remaining: int`, `used: int`, `reset: int`, `resource: str` (all
  REQUIRED).
- `GithubRateLimitClassification` — frozen, slotted, kw-only dataclass
  carrying `value: Literal["primary_exhaustion", "secondary_limit",
  "auth_failure", "other"]`, exposing `PRIMARY_EXHAUSTION`,
  `SECONDARY_LIMIT`, `AUTH_FAILURE`, and `OTHER` as `ClassVar` members.
  It is NOT an Enum, for the same reason `cross_repo.types.RefStatus` is
  not: `constraints.md` §"Public-surface constraints" mandates kw-only
  construction. The four classes are mutually exclusive.
- `GithubBudgetRequest` — frozen, slotted, kw-only dataclass. Fields:
  `method: str`, `resource: str`, `headers: Mapping[str, str]` (all
  REQUIRED), `value: object | None = None`. A transport request after
  budget policy has been applied.
- `GithubBudgetResponse` — frozen, slotted, kw-only dataclass. Fields:
  `status_code: int`, `headers: Mapping[str, str]`, `value: object |
  None`, `primary_budget_spent: int` (all REQUIRED), `snapshot:
  GithubRateLimitSnapshot | None = None`. A `snapshot` of `None` means
  the read was UNMEASURED; it MUST NOT be read as a measured zero.
- `GithubBudgetSuccess` — frozen, slotted, kw-only dataclass carrying
  `response: GithubBudgetResponse` (REQUIRED) and an `unwrap()` method
  returning it.
- `GithubBudgetDeferred` — frozen, slotted, kw-only dataclass carrying
  `resource: str`, `remaining: int`, `floor: int`, and
  `snapshot: GithubRateLimitSnapshot` (all REQUIRED). Deferrable work
  refused to preserve the caller's reserved budget floor.
- `GithubBudgetUnmeasurable` — frozen, slotted, kw-only dataclass
  carrying `argv: str`, `detail: str`, `classification:
  Literal["primary_exhaustion", "secondary_limit"]`, and
  `snapshot: GithubRateLimitSnapshot` (all REQUIRED), plus
  `outcome: Literal["UNMEASURABLE"] = "UNMEASURABLE"`. A rate-limited
  query whose answer cannot be measured now. This is the variant the
  ratified `cross_repo.providers.github` failure union names, so it is
  reachable by any consumer of that provider.
- `GithubBudgetSignalFailed` — frozen, slotted, kw-only dataclass
  carrying `path: Path` and `detail: str` (both REQUIRED): the local
  budget signal could not be appended.
- `GithubBudgetFailure` — the `TypeAlias` for the union
  `GithubBudgetDeferred | GithubBudgetUnmeasurable`.
- `GithubBudgetResult` — the `TypeAlias` for
  `GithubBudgetSuccess | IOFailure[GithubBudgetFailure]`, the return type
  of `GithubBudgetedClient.request`.
- `GithubBudgetTransport` — the `TypeAlias`
  `Callable[..., GithubBudgetResponse]`: the injected transport protocol
  the client is built over.
- `GithubBudgetedClient` — a frozen, slotted, kw-only dataclass, per
  `constraints.md` §"Public-surface constraints". It is the family's ONE
  stateful object, and its state is held OFF the public surface: the
  conditional-read cache, the mutation-pacing clock and the mutation
  lock live on a module-private state holder the client owns and mutates
  THROUGH, so no public field is rebindable and the frozen rule binds
  here with no exception. Fields:
  `transport: GithubBudgetTransport` (REQUIRED), `now: Callable[[],
  float]`, `sleep: Callable[[float], None]`, `max_attempts: int = 3`.
  Its single public method is `request(self, *, method: str, resource:
  str, headers: Mapping[str, str] | None = None, value: object | None =
  None, **options: object) -> GithubBudgetResult`, which applies cache,
  pacing, backoff, and floor policy. A caller that owns its own retry
  policy MUST construct the client with `max_attempts=1` rather than
  nesting two backoff loops.
- `gh_transport(*, execute: GhExecutor) -> GithubBudgetTransport` —
  adapt a `gh` executor to the client's transport protocol. EVERY piece
  of `gh` knowledge (the argv, the conditional-read header, which streams
  carry the response headers, which reads are free) is applied here.
- `gh_invocation(*, value: object) -> GhInvocation` — read a
  `GithubBudgetResponse.value` back as this transport's record. The field
  is typed `object` because the transport protocol is transport-agnostic;
  a value of any other shape is a wiring defect.
- `parse_rate_limit_snapshot(*, headers: Mapping[str, str]) ->
  GithubRateLimitSnapshot` — parse rate-limit headers into a typed
  snapshot.
- `extract_rate_limit_headers(*, text: str | None) -> dict[str, str]` —
  extract the `x-ratelimit-*` header lines from `gh` debug/include text.
- `extract_conditional_headers(*, text: str | None) -> dict[str, str]` —
  extract the cache and pacing header lines from the same text. A CLOSED
  set, not a prefix: `etag`, `retry-after`, and `x-poll-interval`.
- `classify_github_failure(*, status_code: int, snapshot:
  GithubRateLimitSnapshot) -> GithubRateLimitClassification` — classify a
  failed response into exactly one of the four classes.
- `append_rate_limit_snapshot(*, snapshot: GithubRateLimitSnapshot, argv:
  str, status_code: int | None, classification:
  GithubRateLimitClassification | None, path: Path | None = None) ->
  IOResult[None, GithubBudgetSignalFailed]` — append one snapshot to the
  durable local JSONL budget signal. The failure track is named rather
  than raised.

IMPL CO-REQUISITE — the facade's two additive re-exports. The section above documents `GithubBudgetResult` (the return type of `GithubBudgetedClient.request`) and `GithubBudgetTransport` (the type of its `transport` field). Both are currently exported only by `github_budget_types`, which this proposal declares internal, so `livespec_runtime/github_budget.py` MUST re-export them and add them to its `__all__`, taking it from 19 names to 21. Without that, the ratified `GithubBudgetedClient` bullet would name types no consumer could import from the ratified path. Adding a public symbol is **Minor** per `non-functional-requirements.md` §"Versioning".

IMPL CO-REQUISITE — the four narrowings. Each of the following modules is DECLARED INTERNAL; its `__all__` narrows to the empty list. The names themselves stay module-level and public in Python terms — they are imported by name inside this package, and `__all__` governs the DECLARED surface and `import *`, not direct imports — so nothing is renamed and no cross-module private import is created:

- `livespec_runtime.github_budget_client` — `__all__` narrows from 1 name to `[]`, dropping `GithubBudgetedClient`.
- `livespec_runtime.github_budget_client_support` — `__all__` narrows from 10 names to `[]`, dropping `GithubCachedRead`, `MisshapedGithubBudgetOptionError`, `backoff_seconds`, `cached_response`, `header_value`, `int_option`, `mapping_option`, `poll_interval`, `unmeasurable_classification`, `with_snapshot`.
- `livespec_runtime.github_budget_measurement` — `__all__` narrows from 13 names to `[]`, dropping `RATE_LIMIT_RESOURCE`, `append_rate_limit_snapshot`, `classify_github_failure`, `extract_conditional_headers`, `extract_rate_limit_headers`, `gh_argv`, `gh_headers`, `gh_invocation`, `gh_status_code`, `gh_transport`, `parse_rate_limit_snapshot`, `record_budget_signal`, `snapshot_from_headers`.
- `livespec_runtime.github_budget_types` — `__all__` narrows from 13 names to `[]`, dropping `GhExecutor`, `GhInvocation`, `GithubBudgetDeferred`, `GithubBudgetFailure`, `GithubBudgetRequest`, `GithubBudgetResponse`, `GithubBudgetResult`, `GithubBudgetSignalFailed`, `GithubBudgetSuccess`, `GithubBudgetTransport`, `GithubBudgetUnmeasurable`, `GithubRateLimitClassification`, `GithubRateLimitSnapshot`.


### 2. `SPECIFICATION/spec.md`, §"Public surface" — retire the last debt paragraph

REPLACE the two paragraphs that currently begin `Every shipped module that declares a public surface is inside the ratified inventory, is explicitly declared internal there, or is the one family still recorded as ACKNOWLEDGED DEBT below.` and `The `livespec_runtime.github_budget` family (the facade and its four split-out modules) remains ACKNOWLEDGED DEBT` WITH this single paragraph:

Every shipped module that declares a public surface is inside the
ratified inventory or is explicitly declared internal there. The
families that `contracts.md` §"Module-level public surface" ratifies as
this library's SINGLE import path are `livespec_runtime.credentials`,
`livespec_runtime.github_budget`, `livespec_runtime.hygiene_scan`, and
`livespec_runtime.spec_governance`. Where a family's entry point is
ratified, its size-decomposition split-out modules are declared INTERNAL
and named as such in that family's section: consumers MUST import from
the ratified entry point, and this repository MAY change a split-out's
surface without a major classification. A module that ships a public
surface and appears in neither place is a defect rather than tolerated
debt, and `tests/livespec_runtime/test_public_surface_inventory.py`
fails on it; the `# @generated` third-party port that test's register
excludes is outside this rule by construction.

The second paragraph is DELETED outright rather than reworded: it exists only to record the blocked ratification, and the block is gone. With this proposal accepted, no shipped module that declares a public surface remains recorded as acknowledged debt.

### 3. `tests/public-surface-debt.json` — delete the facade row

DELETE the `livespec_runtime.github_budget` row. It is stale the moment the section above lands, because `tests/livespec_runtime/test_public_surface_inventory.py::test_the_debt_register_carries_no_stale_rows` fails with `now ratified in contracts.md (delete the row)` until it is deleted, so it MUST be deleted in the revise changeset itself.

The four split-out rows (`github_budget_client`, `github_budget_client_support`, `github_budget_measurement`, `github_budget_types`) MUST STAY. The register check reads the tree rather than the prose, so those rows do not go stale until each module's `__all__` empties, which is the narrowing changeset declared as this proposal's spec→impl commitment and already filed as `livespec-runtime-cl5aqq`.

### 4. Scenarios and heading coverage

NO scenario is added, on the reasoning v020's Proposal 6b recorded for this family and which this proposal carries forward unchanged: `github_budget`'s consumer-visible behaviour reaches a consumer only through the ratified `cross_repo.providers.github` surface, which already carries mapped `## Scenario:` headings, and duplicating them one layer down would create two entries that must move together silently. EXEMPT, reason recorded.

NO `## ` heading is added, changed, or removed — the new section is a `### ` module section inside the existing `## Module-level public surface` heading, and the `spec.md` edit lands under the existing `## Public surface` heading — so `tests/heading-coverage.json` needs no new entry and every existing entry stays valid.

### 5. Versioning

This proposal changes NO `__all__`, so `non-functional-requirements.md` §"Versioning" is not engaged by the ratification itself and no release-bump classification is owed for it. The `__all__` changes the family still owes (the facade's two additive re-exports, Minor; the four split-outs' narrowings, Major released as a MINOR `0.X.0` bump under the pre-major provision) belong to the commitment changeset, whose commit MUST carry a `!` marker and a `BREAKING CHANGE:` footer so `release_bump_classification` accepts the surface delta.

