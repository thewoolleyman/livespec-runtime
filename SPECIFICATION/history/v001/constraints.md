# constraints.md — livespec-runtime

Architecture-level constraints this library operates under. Each
constraint is a binary, mechanically-checkable rule; lint / type-check
/ test failures are the enforcement mechanism.

## Inherited from livespec

Every constraint in `livespec/SPECIFICATION/non-functional-requirements.md`
applies to this library without restatement. The list below captures
only the constraints that are LIBRARY-LOCAL refinements or that bear
directly on the cross-repo resolution substrate.

Inherited (verbatim, NOT re-stated here):

- Toolchain pins (mise + uv); `just` as the single dev-tooling entry
  point.
- Ruff rule set; Pyright strict mode plus the strict-plus diagnostics.
- 100% line + branch coverage; pytest discipline.
- Conventional Commits subjects; rebase-merge-only master.
- Lefthook pre-commit / commit-msg / pre-push step ordering.
- Comment discipline (Ruff ERA; no historical references inline).
- Keyword-only arguments and dataclasses.
- Domain errors vs bugs split — Result-track for expected errors;
  raised exceptions for unexpected.
- No relative imports; no banned-API surface (`abc.ABC`, `pickle`, etc.);
  typing.Protocol over abc.

## Public-surface constraints

- The public symbols enumerated in `contracts.md` §"Module-level public
  surface" are the entire v1 stable API. Adding to this set is a
  minor-version bump; removing or renaming is a major-version bump.
- Every public dataclass MUST be frozen, slotted, and kw-only.
  Mutation through any public surface is FORBIDDEN.
- Every public function MUST take keyword-only arguments (the `*`
  separator before its parameters), with no positional-only or
  positional-or-keyword arguments.
- `Literal[...]`-typed discriminator fields on the union variants are
  load-bearing for pyright narrowing; consumers rely on the narrowing in
  `match` dispatch. The literal values MUST equal the snake_case variant
  name (`"local"`, `"sibling_work_item"`, `"pull_request"`, `"branch"`).

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
  library's perspective (the v0.2.0 surface does not read local clones
  at all; consumers wire local-clone reading via `sibling_status_lookup`).

## Dependency constraints

- Python runtime dependencies are pinned in `pyproject.toml` and locked
  in `uv.lock`. At v0.2.0 the only runtime dep is `typing_extensions`.
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
  exhaustive-walk policy.
- No HTTP client (`requests`, `httpx`, `urllib`) inside the library;
  every external-state query funnels through the `gh` subprocess
  surface. This keeps the auth boundary at `gh auth`.
- No mutating writes to any file outside `tests/` fixtures during test
  runs. The library is read-only against the consumer environment.
