# constraints.md — livespec-runtime

Architecture-level constraints this library operates under. Each
constraint is a binary, mechanically-checkable rule; lint / type-check
/ test failures are the enforcement mechanism.

## Inherited from livespec

Every constraint in
`livespec/SPECIFICATION/non-functional-requirements.md` applies to
this library without restatement. The contributor-facing inherited
rules (toolchain pins, ruff/pyright/test discipline, lefthook
ordering, Conventional Commits, dataclass conventions) are catalogued
in this library's own
`SPECIFICATION/non-functional-requirements.md` §"Inherited from
livespec"; the rules below are architecture-level constraints
specific to this library's resolution substrate.

## Public-surface constraints

- The public symbols enumerated in `contracts.md` §"Module-level public
  surface" are the entire v1 stable API. That inventory covers both
  slot-concretizing sections and shared-runtime sections per `spec.md`
  §"Scope boundary"; neither category is exempt. Adding to this set is a
  minor-version bump; removing or renaming is a major-version bump.
- Every public dataclass MUST be frozen, slotted, and kw-only.
  Mutation through any public surface is FORBIDDEN.
- Every public function MUST take keyword-only arguments (the `*`
  separator before its parameters), with no positional-only or
  positional-or-keyword arguments.
- `Literal[...]`-typed discriminator fields on the `DependsOnEntry` union
  variants are
  load-bearing for pyright narrowing; consumers rely on the narrowing in
  `match` dispatch. The literal values MUST equal the snake_case variant
  name (`"local"`, `"sibling_work_item"`, `"pull_request"`, `"branch"`).
- Closed `Literal` VOCABULARIES that are not union discriminators —
  `AttentionKind`, `AttentionUrgency`, and `HandoffKind` — are governed
  separately. Their members MUST be lowercase and MAY contain internal
  hyphens; they are wire-visible strings rather than variant names, so
  the snake_case rule above MUST NOT be applied to them. Their exact
  membership is fixed by `contracts.md`, and widening any of them is a
  public-surface change per this section.
- Every `AttentionKind` member MUST correspond to exactly one stable-ID
  prefix accepted by `validate_attention_item_id`, and every accepted
  prefix MUST correspond to exactly one `AttentionKind` member. The
  correspondence MUST be a total, injective mapping DECLARED in
  `contracts.md` §"Module-level public surface", not inferred from
  spelling; a kind and its prefix MAY differ in literal text where the
  declared mapping says so. Adding a kind without its prefix, adding a
  prefix without its kind, or introducing either without a
  corresponding entry in the declared mapping is FORBIDDEN. A
  mechanical check MUST assert that the mapping is total and injective
  in both directions, so the two vocabularies cannot drift.
- The `internal` half of the v012 non-conformance is CLOSED:
  `validate_attention_item_id` now accepts the three-part `internal`
  prefix, so every ratified kind has an accepted prefix. The remaining
  non-conformance is that the declared mapping is not yet asserted by a
  mechanical check. Closing it MUST preserve every id already emitted;
  in particular the `human-valve` kind keeps the `valve` prefix, which
  is why the correspondence is declared rather than spelled. Renaming a
  kind to match its prefix, or migrating emitted ids to match a kind,
  are both FORBIDDEN remedies — the first breaks consumers matching the
  ratified kind literal, the second breaks natural keys already in
  circulation.
- `compose_needs_attention` MUST NOT silently omit a candidate. When a
  candidate's id fails `validate_attention_item_id`, the composer MUST
  surface the failure — by refusing the call, by returning a typed
  failure, or by emitting an explicit malformed marker in the returned
  sequence. Returning a shorter list with no other signal is FORBIDDEN,
  because an omission is indistinguishable from an absence of attention
  and therefore manufactures a false all-clear. Absence MUST always mean
  nothing needed attention, never that composition failed.
- Constructing an `AttentionItem` whose id fails
  `validate_attention_item_id` MUST NOT be a supported path. Validation
  MUST be enforced at construction or at every producer emission
  boundary; which of the two, and the exact surfaced-failure form above,
  MUST be fixed by the proposal that implements this constraint.
- As of the revision that ratifies the two constraints above, the
  implementation is NON-CONFORMANT: the shipped composer drops invalid
  candidates silently and direct construction is unvalidated. Both are
  spec-to-implementation gaps.

## Resolution-substrate constraints

- `resolve_ref` MUST be a pure function of its inputs plus the gh CLI's
  current view of the remote. No process-local cache, no module-level
  state, no memoization. Each call walks fresh.
- The walk MUST tolerate partial visibility. Missing `local_clone`,
  missing `sibling_status_lookup`, missing `repo` slug in the manifest,
  and gh-CLI exhaustion ALL degrade to `RefStatus.UNKNOWN` rather than
  raising. The ONLY raised path from `resolve_ref` is a bug in caller-
  supplied callbacks (uncaught exceptions propagate to the consumer
  supervisor).
- Subprocess invocations MUST funnel through
  `livespec_runtime.cross_repo.providers.<provider>`. Direct
  `subprocess.run` calls in `resolve.py` or `retry.py` are FORBIDDEN.
- The retry layer MUST NOT import from `resolve.py` or from any
  RefStatus-aware module; retry stays a generic backoff helper so a
  future non-resolve caller can reuse it.

## Provider constraints

- The `github` provider is the v1 provider; future providers
  (`gitlab`, `gitea`, etc.) land as sibling modules under
  `livespec_runtime.cross_repo.providers.<name>` with the same
  function-level surface (`query_pull_request_state`,
  `branch_exists_on_remote`, `branch_merged_into_default`).
- Every provider MUST raise on transport failure (CalledProcessError,
  JSONDecodeError). The retry layer catches; the resolve layer
  translates exhaustion to `UNKNOWN`. Providers MUST NOT swallow
  exceptions internally.
- `NonCanonicalGithubUrlError` is the github provider's only domain
  exception. Future providers MAY add their own provider-local domain
  exceptions but MUST keep them in the provider module and MUST raise
  `ValueError` subclasses (or a documented sibling class) so the
  retry layer's broad catch still works.

## Process boundaries

- Each `resolve_ref` invocation runs synchronously in the calling
  process. No threads, no asyncio, no subprocess pool. The retry layer's
  `time.sleep` blocks the calling thread.
- The library is safe to invoke from any sub-command's wrapper process
  (no fork-safety contract is needed because there are no daemons).
- The library MUST NOT mutate the consumer's filesystem. Local clones
  declared in `cross_repo_targets.local_clone` are READ-ONLY from this
  library's perspective (the v1 surface does not read local clones
  at all; consumers wire local-clone reading via `sibling_status_lookup`).

## Dependency constraints

- Python runtime dependencies are pinned in `pyproject.toml` and locked
  in `uv.lock` (see those files for the authoritative current list).
- Adding a new Python runtime dependency requires a propose-change /
  revise cycle that justifies the addition AND a minor-version bump on
  this library AND a bump-pin pass through every consumer.
- System dependencies (`gh`) are NOT pinned by this library; the
  consumer environment owns the `gh` install. The library does declare
  the canonical github_url shape it accepts.

## Forbidden patterns

- No silent fallback that hides a transport error. Every degradation
  path MUST land at `RefStatus.UNKNOWN`; consumers consult `UNKNOWN`
  to decide warn-vs-fail.
- No process-local cache on `resolve_ref`. Each call is fresh per the
  per-variant-walk policy.
- No third-party HTTP client (`requests`, `httpx`) anywhere in the
  library. Within `livespec_runtime.cross_repo`, stdlib `urllib` is
  ALSO forbidden: every cross-repo external-state query MUST funnel
  through the `gh` subprocess surface, keeping the resolution
  substrate's auth boundary at `gh auth`.
- ONE stdlib-urllib carve-out: `livespec_runtime.github_auth` MAY
  use stdlib `urllib` against the https GitHub REST API only (the
  module MUST refuse non-https URLs before any request leaves the
  process). The App installation-token mint IS the credential
  bootstrap — it produces the credential that `gh` consumes — so it
  cannot ride the `gh auth` surface. The carve-out extends no
  further: `github_auth` MUST NOT grow general-purpose HTTP usage
  beyond the mint's App-API calls, and every other module remains
  bound to the `gh` subprocess surface.
- No mutating writes to any file outside `tests/` fixtures during test
  runs. The library is read-only against the consumer environment.
- The GitHub App private key PEM MUST NOT persist at rest under this
  library's control. During RS256 signing it MAY transit AT MOST a
  mode-0600 temporary file, and that file MUST be deleted in a
  `finally` block regardless of signing outcome. The PEM MUST NOT
  appear in argv, URLs, logs, or diagnostics.
- GitHub App installation tokens MUST NOT be persisted at rest by
  this library: caching is process-memory only (the provider), and
  the `git credential` helper's `store`/`erase` operations MUST
  remain no-ops. Diagnostics MUST NOT include token values.
