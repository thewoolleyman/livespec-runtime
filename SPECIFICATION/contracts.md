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
- `CrossRepoManifest` — a frozen, slotted, kw-only dataclass with a
  single REQUIRED field `targets: dict[str, CrossRepoTarget]`, keyed
  by the consumer-chosen repo slug used as the `repo` field on
  cross-repo `DependsOnEntry` variants. Consumers access entries via
  `manifest.targets[slug]`; renaming or removing the `targets`
  attribute is a major-version bump.
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
  returns True iff the named branch exists on the remote. The impl
  invokes `gh api repos/<owner>/<name>/branches/<branch>` and treats
  a 404 response as `False`. The 404 SHOULD be detected via `gh`'s
  exit code (or a structured response field), not via a substring
  match on stderr; consumers MAY rely on the False return for any
  branch the remote does not currently host. Any other
  CalledProcessError propagates.
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

### `livespec_runtime.work_items.types`

- `WorkItem` — frozen, slotted, kw-only dataclass: the unified
  work-item record shared by every impl-plugin store. **Twenty fields.**
  Required (no default), in order: `id: str`, `type: WorkItemType`,
  `status: WorkItemStatus`, `title: str`, `description: str`,
  `origin: Origin`, `gap_id: str | None`, `rank: str`,
  `assignee: str | None`, `depends_on: tuple[DependsOnRaw, ...]`,
  `captured_at: str`, `resolution: Resolution | None`,
  `reason: str | None`, `audit: AuditRecord | None`,
  `superseded_by: str | None`. Optional-on-read (defaulted `= None`,
  written explicitly on append): `spec_commitment_hint: str | None`,
  `supersedes: str | None`, `admission_policy: AdmissionPolicy | None`,
  `acceptance_policy: AcceptancePolicy | None`,
  `blocked_reason: StoredBlockedReason | None`. The optional-on-read
  fields read back as the default (`None`) for legacy records lacking
  them. The record schema is codified HERE, in this repo's own
  `### livespec_runtime.work_items.types`; livespec CORE's
  `SPECIFICATION/` delegates the work-item schema to the runtime +
  orchestrator spec trees and hosts no normative copy of it.
  - `rank` is the fractional/lexicographic ordering key — the **sole
    ordering authority**. Strictly required, non-null, no default: a
    field this library owns is set on every record it writes. Legacy
    pre-`rank` lines on disk read back through a **store-adapter
    bottom-sentinel** (see `### livespec_runtime.work_items.rank`), NOT
    through nullability in the domain type.
  - `priority: int` is **REMOVED** (two order sources = two conflicting
    truths). Legacy physical lines keep `priority` harmlessly in
    append-only history; new/backfilled records omit it (no data scrub).
  - `admission_policy` / `acceptance_policy` / `blocked_reason` follow
    the blessed `… | None` optional-on-read pattern (legacy records read
    back as the default; no in-place migration). `None` = inherit from
    the nearest ancestor epic, else the system safe default (`manual`
    admission, `ai-then-human` acceptance). `blocked_reason` stores ONLY
    `{needs-human, infra-external}`; the third reason `dependency` is
    DERIVED, never stored (it appears only as a rendered `Lane.reason` —
    see `### livespec_runtime.work_items.lifecycle`).
  - `assignee: str | None` is **REUSED in place** as the
    claimed-by/owner field (beads has no native `owner`; `assignee` maps
    1:1 to its native field). Set by the Dispatcher on `admit`;
    **REQUIRED once `status == "active"`** (the `active ⟹ assignee`
    invariant). No new `owner` field is added.
- `WorkItemStatus` — `Literal["backlog", "pending-approval", "ready",
  "active", "acceptance", "blocked", "done"]` (the seven stored lifecycle
  states). Was `open/in_progress/blocked/closed/deferred`.
- `AdmissionPolicy` — `Literal["auto", "manual"]`.
- `AcceptancePolicy` — `Literal["ai-only", "human-only",
  "ai-then-human"]`.
- `StoredBlockedReason` — `Literal["needs-human", "infra-external"]`
  (the STORED reasons only; `dependency` is derived).
- `AuditRecord` — frozen, slotted, kw-only dataclass:
  `verification_timestamp: str`, `commits: tuple[str, ...]`,
  `files_changed: tuple[str, ...]`, `merge_sha: str`,
  `pr_number: int | None = None`. The merge-evidence record attached at
  completed-resolution closure time.
- `WorkItemType`, `Origin`, `Resolution` — unchanged `Literal` string
  aliases enumerating the schema's closed value sets.
- `DependsOnRaw` — `TypeAlias` `str | dict[str, Any]` for a raw dependency
  entry as stored (parsed into the `cross_repo` `DependsOnEntry` variants
  by the consumer).

> **Invariants (doctor-checkable; restated for the consumer):**
> `active ⟹ assignee` set; stored `blocked ⟹ blocked_reason ∈
> {needs-human, infra-external}`; reaching `ready` requires transiting
> `pending-approval` (the structural grooming gate); every live (head,
> non-superseded) record has a real, non-sentinel `rank`. These
> invariants are *enforced* by the orchestrators' `doctor` (L1), not by
> the runtime dataclass; the runtime states them as the contract.

### `livespec_runtime.work_items.reduce`

- `work_item_record_identity(*, item: WorkItem) -> str` — the stable
  per-record identity `sha256:<hex>` over the record's canonical
  serialization; the value a superseding record carries in `supersedes`.
- `reduce_work_item_heads(*, records: Iterator[WorkItem]) -> dict[str,
  tuple[WorkItem, ...]]` — the order-independent supersession reduction:
  per entity `id`, the head record(s) no sibling supersedes, ordered by
  the deterministic `(captured_at, identity)` tie-break. More than one
  head for an `id` is concurrent divergence (surfaced, not resolved).
- `materialize_work_items(*, records: Iterator[WorkItem]) -> dict[str,
  WorkItem]` — the current-head-per-id dict (tie-break winner among each
  entity's heads). For a substrate inherently one-record-per-id (e.g.
  beads) this is the degenerate identity-collection case.
- `random_id_suffix() -> str` — a fresh six-character base32 id suffix
  (the `li-<suffix>` body).

### `livespec_runtime.work_items.store`

- `WorkItemStore` — `typing.Protocol` (structural; no inheritance) with
  `read_work_items(self) -> Iterator[WorkItem]` and
  `append_work_item(self, *, item: WorkItem) -> None`. The conformance
  contract every impl-plugin's work-item store satisfies via a thin
  per-impl facade over its backend I/O. Comments are deliberately NOT
  part of this contract (only the beads substrate carries them).

### `livespec_runtime.work_items.lifecycle`

- `lane_of(*, item: WorkItem, index: dict[str, WorkItem], manifest:
  CrossRepoManifest) -> Lane` — the single lane authority (net-new). The
  board lane **is** the state, with one derived overlay. Overlay logic:
  stored `ready` + any open dep → `Lane("blocked", "dependency")`;
  stored `blocked` → `Lane("blocked", <stored blocked_reason>)`; every
  other state → `Lane(<status>, None)`. "Open dep" reuses the
  `resolve_ref`/`RefStatus` notion: a dep blocks iff it resolves to
  `OPEN`, or is unparseable (fail-closed); `CLOSED`/`UNKNOWN` do not
  block — so lane and readiness agree by construction.
- `Lane` — frozen, slotted, kw-only dataclass: `name: LaneName`,
  `reason: BlockedReason | None` (non-None iff `name == "blocked"`).
- `LaneName` — `Literal["backlog", "pending-approval", "ready",
  "active", "acceptance", "blocked", "done"]` (the 7 rendered lanes).
- `BlockedReason` — `Literal["needs-human", "infra-external",
  "dependency"]` (the *rendered* reason; note the asymmetry vs. the
  2-valued stored `StoredBlockedReason`).
- `is_item_ready(*, item: WorkItem, index: dict[str, WorkItem],
  manifest: CrossRepoManifest) -> bool` — re-expressed as
  `lane_of(...).name == "ready"`. Relocated from the beads-fabro
  orchestrator's `commands/_cross_repo.py` as a **pure predicate** that
  takes **injected status-lookup callables** (`local_status_lookup`,
  optional `sibling_status_lookup`) so there is **no `runtime → beads`
  back-edge**. The beads store-reading stays in the orchestrator.
- `ready_sort_key(item: WorkItem) -> tuple[...]` — the single canonical
  ranking key both `next` and the Dispatcher compose. Lead key switches
  from `priority` to **`rank`**, then `id` as the deterministic
  tie-break. The old `priority → origin → captured_at` heuristic is
  retired.
- The open/closed-dependency determination (`parse_entry` /
  `_entry_blocks` / local-status-lookup construction) is lifted here too,
  reusing `resolve_ref`/`RefStatus` from `livespec_runtime.cross_repo` —
  so "open deps" is computed in exactly ONE place and the Dispatcher's
  drain order can never diverge from what `next` advertises.

> The exact callable signatures the orchestrator injects mirror the
> existing `resolve_ref(local_status_lookup=…, sibling_status_lookup=…)`
> contract (`### livespec_runtime.cross_repo.resolve`), so the consumer
> wires its beads store-reads through the same seam it already uses. The
> precise public-vs-helper split (which `_`-prefixed helpers are part of
> the surface) is a `groom`/implement detail.

### `livespec_runtime.work_items.rank`

- `key_between(*, a: str | None, b: str | None) -> str` — thin
  livespec-facing wrapper over the ported `generate_key_between`. `a` /
  `b` are the neighbor keys (`None` = open end); returns a fresh key
  ordering strictly between them.
- `n_keys_between(*, a: str | None, b: str | None, n: int) -> list[str]`
  — wrapper over `generate_n_keys_between`; returns `n` evenly-spaced
  keys between the neighbors (the `rebalance-ranks` / backfill
  generator).
- `BOTTOM_SENTINEL: str` — the shared bottom-sentinel a store ADAPTER
  substitutes for a legacy line lacking `rank`. A constant using a char
  **outside** the lib's base-62 alphabet (`0-9A-Za-z`), e.g. `"~"`
  (`0x7E` > `z` `0x7A`), so it sorts strictly **after** every real key.
  The two backend facades (git-jsonl, beads) import this one constant;
  the strict `rank: str` domain type never carries it.
- `_fractional_indexing` — the PORTED CC0-1.0 module
  (`httpie/fractional-indexing-python`, the official Python port of
  `rocicorp/fractional-indexing`; stdlib-only; public
  `generate_key_between` / `generate_n_keys_between` /
  `validate_order_key`). Vendored verbatim with an attribution header; a
  `NOTICES` entry is added at the repo root. PORT (not vendor) because
  `rank` math must live in `livespec_runtime`, which has no vendoring
  machinery and is itself copied source-only into every consumer's
  `_vendor/` tree — one file rides along automatically, no new
  machinery, no drift.

### `livespec_runtime.github_auth.errors`

- `GithubAppAuthError` — `Exception` subclass with a `detail: str`
  attribute; the single expected-failure domain error on the App-token
  mint path (missing/rejected credentials, App API rejections,
  malformed responses). `detail` MUST be an actionable diagnostic
  naming the specific cause; consumers MAY surface it verbatim.

### `livespec_runtime.github_auth.config`

- `GithubAppConfig` — frozen, slotted, kw-only dataclass:
  `app_id: str`, `private_key_pem: str`,
  `api_url: str = DEFAULT_API_URL`,
  `installation_id: str | None = None`.
- `DEFAULT_API_URL` — `"https://api.github.com"`.
- `load_github_app_config(*, environ: Mapping[str, str]) ->
  GithubAppConfig` — the env-only input boundary. Inputs come ONLY
  from environment variables injected by the consuming tenant's
  `credential_wrapper`: `GITHUB_APP_ID` and `GITHUB_PRIVATE_KEY`
  (REQUIRED; an empty string counts as missing),
  `GITHUB_APP_INSTALLATION_ID` (OPTIONAL installation pin) and
  `GITHUB_API_URL` (OPTIONAL API-root override, e.g. GitHub
  Enterprise). Resolution MUST fail closed: any absent-or-empty
  required variable raises `GithubAppAuthError` naming EVERY missing
  variable and pointing the operator at the tenant's
  `credential_wrapper`; there MUST NOT be a fallback to any fleet
  credential.

### `livespec_runtime.github_auth.signing`

- `b64url(*, raw: bytes) -> str` — URL-safe unpadded base64 (the
  JWS/JWT encoding).
- `jwt_signing_input(*, app_id: str, issued_at: int) -> str` — the
  unsigned RS256 App-JWT `header.payload`; the caller injects time.
  The JWT lifetime MUST stay under GitHub's 10-minute App-JWT cap.
- `normalize_pem(*, raw: str) -> str` — re-normalizes
  secrets-manager-flattened keys to real PEM line structure; a
  well-formed PEM passes through unchanged.
- `sign_rs256_with_openssl(*, signing_input: str, pem: str) -> bytes`
  — the production RS256 signer (openssl subprocess). An unloadable
  key is an EXPECTED misconfiguration and MUST raise
  `GithubAppAuthError`.

### `livespec_runtime.github_auth.mint`

- `mint_installation_token(*, config: GithubAppConfig, issued_at:
  int, seams: MintSeams = DEFAULT_MINT_SEAMS) -> str` — mint on
  demand: sign the App JWT, resolve the installation (the pinned
  `installation_id`, else sole-installation discovery — any other
  installation count is an EXPECTED ambiguity that MUST raise
  `GithubAppAuthError` directing the operator to pin
  `GITHUB_APP_INSTALLATION_ID`), then
  `POST /app/installations/{id}/access_tokens`. Every EXPECTED
  failure raises `GithubAppAuthError`; caller bugs propagate as
  built-ins. The returned token is ephemeral and MUST NOT be
  persisted at rest.
- `MintSeams` — frozen, slotted, kw-only seam bundle (`sign`,
  `http_get`, `http_post`); `SignRs256` / `HttpJson` — the kw-only
  `typing.Protocol` seam shapes; `DEFAULT_MINT_SEAMS` — the
  production bundle (openssl signer + stdlib-urllib HTTP). Production
  HTTP MUST refuse non-https URLs before any request leaves the
  process.

### `livespec_runtime.github_auth.provider`

- `InstallationTokenProvider` — the token-lifecycle authority:
  `__init__(*, config, seams=DEFAULT_MINT_SEAMS, clock=time.time)`,
  `token() -> str`. Tokens are minted on demand at first use and
  cached in process memory ONLY; `token()` MUST re-mint transparently
  once the refresh horizon passes — BEFORE the ~1-hour
  installation-token expiry — so operations that outlive a token
  never see an expired credential and callers MUST NOT need to handle
  expiry themselves. Tokens MUST NOT be persisted at rest. The
  provider is synchronous (no threads, per this library's process
  boundaries); refresh happens lazily on access.
- `TOKEN_REFRESH_SECONDS` — `3300` (the 55-minute refresh horizon,
  safely before the ~60-minute expiry).

### `livespec_runtime.github_auth.credential_helper`

- `main(*, argv, environ, stdin, stdout, stderr,
  seams=DEFAULT_MINT_SEAMS) -> int` — the `git credential`
  get/store/erase protocol body over injected streams. `get` MUST
  answer https contexts with `username=x-access-token` plus a freshly
  minted installation token as the password, and MUST NOT emit a
  credential for non-https contexts (exit 0 with no output — git
  treats missing output as "no credential from this helper"). `store`
  and `erase` MUST be no-ops (the token is ephemeral; there is
  nothing to persist or erase). A fail-closed credential error MUST
  print the actionable diagnostic to stderr and exit non-zero; a
  usage error exits 2.
- `run() -> int` — the process entry wiring the real streams and
  environment.
- The console script `livespec-github-credential-helper` (declared in
  pyproject `[project.scripts]`, targeting `run`) is the public entry
  point; consumers wire it as
  `git config credential.helper '!livespec-github-credential-helper'`.
  Renaming or removing the console script is a major-version bump.

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
`livespec/SPECIFICATION/contracts.md`. The block shape for the
`livespec-runtime` consumer slot
is:

```jsonc
{
  "livespec-runtime": {
    "compat": {
      "livespec": ">=0.1.0,<1.0.0",
      "pinned": "v0.12.0" // x-release-please-version
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
livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.12.0" } # x-release-please-version
```

Or as a runtime dependency:

```toml
[project]
dependencies = [
    "livespec-runtime>=0.2.0",
]

[tool.uv.sources]
livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.12.0" } # x-release-please-version
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
- `openssl` CLI — REQUIRED in any environment where consumers mint
  GitHub App installation tokens via `livespec_runtime.github_auth`
  (the production RS256 signer shells out to it). Like `gh`, it is
  NOT pinned by this library; the consumer environment owns the
  install.
- The only Python runtime dependency outside the standard library is
  `typing_extensions` (for `assert_never` on Python <3.11 — the
  project's `requires-python` is `>=3.10.16`). The authoritative
  current list lives in `pyproject.toml` and `uv.lock`.

## Versioning

Semver bump rules and the consumer pin-and-bump mechanism live in
`non-functional-requirements.md` §"Versioning". Surface-change
classifications (additions / removals / refactors) are referenced
by `spec.md` §"Public surface" and by the per-symbol bullets above.
