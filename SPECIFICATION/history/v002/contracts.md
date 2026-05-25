# contracts.md — livespec-runtime

Wire-level surfaces this library exposes (importable Python module
shapes, gh CLI subprocess contracts, and the consumer-facing
`.livespec.jsonc` `compat` block shape). Every contract here
concretizes a slot in `livespec/SPECIFICATION/contracts.md`; nothing
here overrides upstream.

## Module-level public surface

The importable names below are the library's v1 stable API. Removing or
renaming any of them is a major-version bump per `spec.md` §"Public
surface".

### `livespec_runtime.cross_repo.types`

- `RefStatus` — `str`-valued Enum with members `OPEN`, `CLOSED`,
  `UNKNOWN`. The `.value` strings are the lowercase member names
  (`"open"`, `"closed"`, `"unknown"`). Consumers SHOULD round-trip
  through JSON by serializing `.value` and deserializing via
  value-lookup (`RefStatus(s)`); consumers MUST NOT deserialize
  via name-lookup (`RefStatus[s]`), which would require uppercase
  inputs.
- `LocalDependency`, `SiblingWorkItemDependency`,
  `PullRequestDependency`, `BranchDependency` — frozen, slotted,
  kw-only dataclasses discriminated on a `Literal[...]`-typed `kind`
  field. The `kind` field's value MUST equal the variant name's
  snake_case form (`"local"`, `"sibling_work_item"`, `"pull_request"`,
  `"branch"`); the `Literal` annotation pins this so pyright narrows
  union members on `match entry.kind: ...` dispatch.
- `DependsOnEntry` — the `TypeAlias` for the four-variant union.

Per-variant required and optional fields (the `kind` field is the
discriminator on every variant, REQUIRED, and pinned to the literal
named above):

- `LocalDependency`: `work_item_id: str` (REQUIRED).
- `SiblingWorkItemDependency`: `repo: str` (REQUIRED),
  `work_item_id: str` (REQUIRED).
- `PullRequestDependency`: `repo: str` (REQUIRED), `number: int`
  (REQUIRED).
- `BranchDependency`: `repo: str` (REQUIRED), `name: str`
  (REQUIRED) — the branch name MUST be supplied without the
  `refs/heads/` prefix.

`parse_depends_on_entry` raises `CrossRepoSchemaError` when any
required field above is absent; the error's `detail` names the
specific missing field.

- `CrossRepoTarget` — a frozen, slotted, kw-only dataclass carrying
  `github_url: str` (REQUIRED), `local_clone: Path | None`
  (OPTIONAL, default `None`), and `default_branch: str` (OPTIONAL,
  default `"master"`).
- `CrossRepoManifest` — a frozen, slotted, kw-only dataclass wrapping
  a `dict[str, CrossRepoTarget]` keyed by the consumer-chosen repo
  slug used as the `repo` field on cross-repo `DependsOnEntry` variants.
- `parse_depends_on_entry(*, parsed: dict[str, Any]) -> DependsOnEntry`
  — the dict-to-typed boundary. Raises `CrossRepoSchemaError` with a
  descriptive `detail` when `kind` is missing, unknown, or a per-kind
  required field is absent.
- `parse_cross_repo_manifest(*, parsed: dict[str, Any]) ->
  CrossRepoManifest` — the dict-to-typed boundary for the
  `cross_repo_targets` block.

### `livespec_runtime.cross_repo.errors`

- `CrossRepoSchemaError` — `Exception` subclass with a `detail: str`
  attribute. The single domain error this library raises. Consumers MAY
  catch it at the parse-boundary and surface `detail` to the user
  verbatim.

### `livespec_runtime.cross_repo.providers.github`

- `query_pull_request_state(*, github_url: str, number: int) -> str` —
  returns the PR's `state` (`"OPEN"`, `"CLOSED"`, or `"MERGED"`) via
  `gh pr view <number> --repo <github_url> --json state`.
- `branch_exists_on_remote(*, github_url: str, name: str) -> bool` —
  returns True iff the named branch exists on the remote. 404 responses
  translate to `False`; any other CalledProcessError propagates.
- `branch_merged_into_default(*, github_url: str, name: str,
  default_branch: str) -> bool` — returns True iff `name` is fully
  reachable from `default_branch` (`gh api compare` `status` is
  `identical` or `behind`).
- `NonCanonicalGithubUrlError` — `ValueError` subclass raised when a
  `github_url` is not the canonical https form. Carries the offending
  `github_url: str` attribute.

### `livespec_runtime.cross_repo.retry`

- `retry_with_backoff(*, fn: Callable[[], T]) -> T | None` — invokes
  `fn` with the 3-attempt 1s/2s backoff policy (see §"Retry policy"
  below for the full description, including the reserved-but-unused
  4.0s constant). Returns `fn()`'s value on first success; returns
  `None` after all three attempts raise.
  Exceptions raised by `fn` are caught broadly; callers translate the
  `None` return into `RefStatus.UNKNOWN` at their own resolution
  boundary. Backoff delays use `time.sleep` directly so tests can
  monkeypatch.

### `livespec_runtime.cross_repo.resolve`

- `resolve_ref(*, entry: DependsOnEntry, manifest: CrossRepoManifest,
  local_status_lookup: Callable[[str], RefStatus],
  sibling_status_lookup: Callable[[str, str], RefStatus] | None = None)
  -> RefStatus` — the public entry point. Match-dispatches on the
  entry's variant and returns the resolved status. `local_status_lookup`
  is REQUIRED; `sibling_status_lookup` is OPTIONAL (absent =
  `SiblingWorkItemDependency` resolutions return `UNKNOWN`).

## Resolution semantics

For each `DependsOnEntry` variant `resolve_ref` returns:

- `LocalDependency` — delegates entirely to `local_status_lookup`;
  whatever it returns is the answer.
- `SiblingWorkItemDependency` — returns `UNKNOWN` when the `repo`
  slug is not in the manifest OR when `sibling_status_lookup` is absent;
  otherwise returns whatever `sibling_status_lookup(repo,
  work_item_id)` returns.
- `PullRequestDependency` — returns `UNKNOWN` when `repo` is not in
  the manifest; otherwise queries `query_pull_request_state` under
  `retry_with_backoff`. `state` `MERGED` or `CLOSED` → `CLOSED`;
  `OPEN` → `OPEN`; retry exhaustion → `UNKNOWN`.
- `BranchDependency` — returns `UNKNOWN` when `repo` is not in the
  manifest; otherwise queries `branch_exists_on_remote` under
  `retry_with_backoff`. Absent branch → `CLOSED` (assumes
  deleted-after-merge; the consumer's branch hygiene MUST delete feature
  branches on merge for this to be correct). Present branch → query
  `branch_merged_into_default`; merged → `CLOSED`; not merged →
  `OPEN`; retry exhaustion at either step → `UNKNOWN`.

The `UNKNOWN` return MUST NOT be treated as a hard failure by
consumers; livespec-core's doctor surfaces `UNKNOWN` resolutions as a
`warn` finding by default and never `fail`.

## Retry policy

- 3 attempts total.
- Backoff between attempts: 1s before attempt 2, 2s before attempt 3.
  (4s appears in the constants tuple to keep room for a documented
  future widening; the v1 contract is 3 attempts using the first two
  delays only.)
- All exceptions caught broadly; no per-exception classification.
- Backoff uses `time.sleep` so tests MAY monkeypatch it; consumers MUST
  NOT depend on a specific clock source.
- The policy is NOT user-configurable in v1. Projects with
  bandwidth-constrained CI environments are expected to pre-fetch
  sibling repos to local clones (via the `local_clone` field on
  `CrossRepoTarget`) to avoid the GitHub-query path entirely.

## `.livespec.jsonc` `compat` block (consumer-facing)

Every consumer MUST declare a top-level section on its `.livespec.jsonc`
keyed by the consumer's own plugin / library name and MUST include a
`compat` block under that section per
`livespec/SPECIFICATION/contracts.md` §"Cross-repo coordination —
pin-and-bump". The block shape for the `livespec-runtime` consumer slot
is:

```jsonc
{
  "livespec-runtime": {
    "compat": {
      "livespec": ">=0.1.0,<1.0.0",
      "pinned": "v0.3.0" // x-release-please-version
    }
  }
}
```

This is the same shape impl-plugins and `livespec-dev-tooling` use; the
key `livespec-runtime` is the load-bearing identifier the doctor
`contract-version-compatibility` invariant consults.

## Consumption shape

Consumers add this library via `uv` git source. Either as a dev
dependency:

```toml
[dependency-groups]
dev = [
    "livespec-runtime",
]

[tool.uv.sources]
livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.3.0" } # x-release-please-version
```

Or as a runtime dependency:

```toml
[project]
dependencies = [
    "livespec-runtime>=0.2.0",
]

[tool.uv.sources]
livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.3.0" } # x-release-please-version
```

The tag value in `[tool.uv.sources]` MUST match the `compat.pinned`
value in `.livespec.jsonc` for the consumer; drift between the two is
the consumer's responsibility to enforce (doctor does not yet cross-
check them).

## System dependencies

- `gh` CLI — REQUIRED in any environment where consumers invoke
  `resolve_ref` against `PullRequestDependency` or `BranchDependency`
  entries. The runtime does NOT shell-detect `gh`'s presence; absence
  surfaces as `CalledProcessError` raised by the provider functions
  and (via the retry layer) collapses to `RefStatus.UNKNOWN`.
- `gh auth status` — MUST be successful for the `gh` invocations to
  succeed. Authentication is the consumer environment's responsibility.
- The only Python runtime dependency outside the standard library is
  `typing_extensions` (for `assert_never` on Python <3.11 — the
  project's `requires-python` is `>=3.10.16`). The authoritative
  current list lives in `pyproject.toml` and `uv.lock`.

## Versioning

- Major (`X.0.0`) — removing or renaming a public symbol; changing a
  resolution semantic; tightening a parse contract such that previously
  valid inputs now raise.
- Minor (`0.X.0`) — adding a public symbol; adding a new
  `DependsOnEntry` variant; loosening a parse contract; adding a new
  provider module.
- Patch (`0.0.X`) — internal refactors with no public-surface change;
  bugfixes that align behavior with this contract.

The pin-and-bump mechanism means consumers MAY pin to a major-version
range (`>=0.2.0,<1.0.0`) but MUST also carry an explicit `pinned` tag
in their `.livespec.jsonc` `compat` block. The pinned tag is the
actually-used version; the semver range communicates compatibility.
