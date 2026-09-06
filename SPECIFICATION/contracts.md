# contracts.md — livespec-runtime

Wire-level surfaces this library exposes (importable Python module
shapes, gh CLI subprocess contracts, and the consumer-facing
`.livespec.jsonc` `compat` block shape). Every contract here either
concretizes a slot in `livespec/SPECIFICATION/contracts.md` or is a
shared-runtime contract per `spec.md` §"Scope boundary". Nothing here
overrides upstream. Each shared-runtime section MUST state, in its own
text, that core names no slot for it and MUST name the producers that
consume it.

## Module-level public surface

The importable names below are the library's v1 stable API. Removing or
renaming any of them is a major-version bump per `spec.md` §"Public
surface".

### `livespec_runtime.cross_repo.types`

- `RefStatus` — a frozen, slotted, kw-only dataclass carrying
  `value: Literal["open", "closed", "unknown"]`, exposing `OPEN`,
  `CLOSED`, and `UNKNOWN` as `ClassVar` members assigned after the
  class body. It is NOT an Enum and NOT a `str` subclass. Members
  compare equal by value, so `status == RefStatus.OPEN` is the
  membership test. Consumers SHOULD round-trip through JSON by
  serializing `.value` and deserializing via the KEYWORD form
  (`RefStatus(value=s)`). The positional form (`RefStatus(s)`) and
  subscript lookup (`RefStatus[s]`) both raise `TypeError` — the
  first because `constraints.md` §"Public-surface constraints"
  mandates kw-only construction, the second because a dataclass is
  not subscriptable.
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

`parse_depends_on_entry` returns a `Failure` carrying
`CrossRepoSchemaError` when any required field above is absent; the
error's `detail` names the specific missing field. It does NOT raise —
a caller guarding it with `try`/`except` would never see the handler
fire and would then treat a `Failure`-carrying `Result` as a typed
entry.

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
- `parse_depends_on_entry(*, parsed: dict[str, Any]) ->
  Result[DependsOnEntry, CrossRepoSchemaError]` — the dict-to-typed
  boundary. Returns a `Failure` carrying `CrossRepoSchemaError` with a
  descriptive `detail` when `kind` is missing, unknown, or a per-kind
  required field is absent. `parse_cross_repo_manifest`, by contrast,
  still RAISES; the two boundaries differ deliberately and callers
  MUST NOT assume one idiom covers both.
- `parse_cross_repo_manifest(*, parsed: dict[str, Any]) ->
  CrossRepoManifest` — the dict-to-typed boundary for the
  `cross_repo_targets` block.

### `livespec_runtime.cross_repo.errors`

- `CrossRepoSchemaError` — `Exception` subclass with a `detail: str`
  attribute. The single domain error this library raises. Consumers MAY
  catch it at the parse-boundary and surface `detail` to the user
  verbatim.

### `livespec_runtime.cross_repo.providers.github`

- `GithubFailure` — the `TypeAlias` for a provider transport failure,
  the union `GithubQueryFailed | GithubBudgetUnmeasurable`.
- `query_pull_request_state(*, github_url: str, number: int) ->
  IOResult[str, GithubFailure]` — yields the PR's `state` (`"OPEN"`,
  `"CLOSED"`, or `"MERGED"`) via
  `gh pr view <number> --repo <github_url> --json state`.
- `branch_exists_on_remote(*, github_url: str, name: str) ->
  IOResult[bool, GithubFailure]` — yields True iff the named branch
  exists on the remote. The impl invokes
  `gh api repos/<owner>/<name>/branches/<branch>` and treats a 404
  response as `False`. The 404 SHOULD be detected from `gh`'s structured `(HTTP 404)`
  stderr marker line or an explicit HTTP status header (for example via
  `gh api --include`), surfaced to callers as a typed field rather than by
  callers matching stderr text themselves; `gh`'s exit code is 1 for every
  API failure and MUST NOT be relied on to discriminate a 404; consumers MAY rely on the False success value for any branch
  the remote does not currently host. Any other transport failure
  lands on the failure track as `GithubFailure`; it is NOT raised.
- `branch_merged_into_default(*, github_url: str, name: str,
  default_branch: str) -> IOResult[bool, GithubFailure]` — yields True
  iff `name` is fully reachable from `default_branch` (`gh api compare`
  `status` is `identical` or `behind`).
- `NonCanonicalGithubUrlError` — raised when a `github_url` is not the
  canonical https form. It MUST subclass `Exception` directly, per
  `constraints.md` §"Public-surface constraints". Carries the offending
  `github_url: str` attribute.

### `livespec_runtime.cross_repo.providers.github_process`

The budgeted-`gh` SUPPORT MODULE of the `cross_repo.providers.github`
section above. It exists because `providers/github.py` was decomposed
for size; the provider remains the entry point consumers import, and
this module is where the provider's failure vocabulary and its single
process-wide `GithubBudgetedClient` are DEFINED. `providers.github`
re-exports `GithubFailure`, `GithubQueryFailed`, and
`GithubBudgetUnmeasurable` from here, and those three names are ratified
under the provider's own section.

⚠️ The client this module owns is built with `max_attempts=1` ON PURPOSE.
Retry policy for this provider belongs to `cross_repo.retry`, one layer
up — the layer that knows a retry-exhausted query degrades to
`RefStatus.UNKNOWN`. A second retry loop inside the transport would
multiply the attempt count the resolver chose.

- `GithubQueryFailed` — frozen, slotted, kw-only dataclass carrying
  `argv: str` (REQUIRED, shell-quoted so an operator can rerun the
  query), `detail: str` (REQUIRED), and `http_404: bool = False`. A `gh`
  query that did NOT produce an answer. Deliberately NOT inhabited by
  "gh answered, and the answer was no": a 404 on the branch-existence
  probe means the branch is gone, and a PR in state `CLOSED` is a state;
  both are answers and both stay on the success track.
- `GithubFailure` — the `TypeAlias` for the union
  `GithubQueryFailed | GithubBudgetUnmeasurable`, the same alias the
  provider section documents.
- `budgeted_gh(*, resource: str) -> IOResult[GhInvocation,
  GithubFailure]` — issue ONE budgeted `gh` read through the module's
  process-wide client, or name the query that did not answer. `resource`
  is the shlex-joined `gh` argument tail and doubles as the client's
  cache key.
- `spawn_gh(*, argv: list[str]) -> GhInvocation` — spawn one `gh` argv,
  reporting what it printed or why it never ran. It sets `GH_DEBUG=api`,
  which is what makes the response headers observable on stderr.
- `budget_failure(*, failure: GithubBudgetFailure, argv: str) ->
  GithubFailure` — restate a budget refusal in this provider's failure
  vocabulary. A `GithubBudgetUnmeasurable` passes through carrying the
  `gh` argv; a `GithubBudgetDeferred` (which no read of this provider
  can produce, since none is declared deferrable) is mapped to a
  `GithubQueryFailed` rather than widening the ratified union to a third
  variant no caller could observe.
- `stderr_indicates_http_404(*, stderr: str | None) -> bool` — True iff
  any stderr line ends with the structured `(HTTP 404)` marker. Matching
  the trailing marker rather than a bare `404` substring is what stops
  URL fragments and body text from reading as a not-found response.

### `livespec_runtime.cross_repo.retry`

- `RetryExhausted` — frozen, slotted, kw-only dataclass carrying
  `attempts: int` and `detail: str`, describing what the LAST failing
  attempt reported. It is normalised rather than generic in the
  caller's failure type, so this module names no domain's error
  vocabulary.
- `retry_with_backoff(*, fn: Callable[[], IOResult[T, E]]) ->
  IOResult[T, RetryExhausted]` — invokes `fn` with the 3-attempt
  1s/2s backoff policy (see §"Retry policy" below for the full
  description, including the reserved-but-unused 4.0s constant).
  Returns `fn()`'s success value, re-lifted onto the success track,
  on the first attempt that lands there; after all three attempts
  fail it returns an `IOFailure` carrying `RetryExhausted`.
  Exceptions raised by `fn` are caught broadly and folded onto the
  same failure track. Callers MUST translate an `IOFailure` into
  `RefStatus.UNKNOWN` at their own resolution boundary. There is NO
  `None` sentinel: testing for one never matches, so a caller that
  did would treat retry exhaustion as a success and manufacture the
  silent fallback `constraints.md` §"Forbidden patterns" forbids.
  Backoff delays use `time.sleep` directly so tests can monkeypatch.

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
  work-item record shared by every impl-plugin store. **Twenty-five
  fields.** Required (no default), in order: `id: str`, `type: WorkItemType`,
  `status: WorkItemStatus`, `title: str`, `description: str`,
  `origin: Origin`, `gap_id: str | None`, `rank: str`,
  `assignee: str | None`, `depends_on: tuple[DependsOnRaw, ...]`,
  `captured_at: str`, `resolution: Resolution | None`,
  `reason: str | None`, `audit: AuditRecord | None`,
  `superseded_by: str | None`. Optional-on-read (defaulted `= None`
  unless noted, written explicitly on append), in order:
  `spec_commitment_hint: str | None`, `acceptance_criteria: str | None`,
  `notes: str | None`, `supersedes: str | None`,
  `admission_policy: AdmissionPolicy | None`,
  `acceptance_policy: AcceptancePolicy | None`,
  `blocked_reason: StoredBlockedReason | None`,
  `factory_safety: FactorySafety | None`,
  `review_requirement: ReviewRequirement | None`,
  `awaits_scope_override: bool = False`. Every optional-on-read field
  reads back as its default (`None`, or `False` for
  `awaits_scope_override`) for a legacy record lacking it.
  `awaits_scope_override` is a materialized current-state signal,
  backed by the `awaits-scope-override` beads label in the beads
  substrate — consumer `livespec_orchestrator_beads_fabro` sets it to
  reflect that label. The record schema is codified HERE, in this
  repo's own
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
  CrossRepoManifest, sibling_status_lookup: Callable[[str, str],
  RefStatus] | None = None) -> Lane` — the single lane authority
  (net-new). The board lane **is** the state, with one derived overlay.
  Overlay logic:
  stored `ready` + any open dep → `Lane("blocked", "dependency")`;
  stored `blocked` → `Lane("blocked", <stored blocked_reason>)`; every
  other state → `Lane(<status>, None)`. "Open dep" reuses the
  `resolve_ref`/`RefStatus` notion: a dep blocks iff it resolves to
  `OPEN` (any kind), is unparseable (fail-closed), or is a
  `sibling_work_item` that does not resolve to `CLOSED` (also
  fail-closed — an unresolved cross-repo blocker must not let a
  candidate slip through as ready). `CLOSED` never blocks; `UNKNOWN`
  blocks for the `sibling_work_item` kind ONLY — a `local` UNKNOWN (a
  missing id) does NOT block, since `no-orphan-dependency` owns that
  case, and `pull_request`/`branch` UNKNOWN keeps its
  tolerate-partial-visibility semantics — so lane and readiness agree by
  construction.
- `Lane` — frozen, slotted, kw-only dataclass: `name: LaneName`,
  `reason: BlockedReason | None` (non-None iff `name == "blocked"`).
- `LaneName` — `Literal["backlog", "pending-approval", "ready",
  "active", "acceptance", "blocked", "done"]` (the 7 rendered lanes).
- `BlockedReason` — `Literal["needs-human", "infra-external",
  "dependency"]` (the *rendered* reason; note the asymmetry vs. the
  2-valued stored `StoredBlockedReason`).
- `is_item_ready(*, item: WorkItem, index: dict[str, WorkItem],
  manifest: CrossRepoManifest, sibling_status_lookup: Callable[[str,
  str], RefStatus] | None = None) -> bool` — re-expressed as
  `lane_of(...).name == "ready"`. Relocated from the beads-fabro
  orchestrator's `commands/_cross_repo.py` as a **pure predicate**:
  sibling status arrives through the optional injected
  `sibling_status_lookup`, and local status is derived in-module from
  the supplied `index` rather than injected, so there is **no `runtime →
  beads` back-edge**. The beads store-reading stays in the orchestrator.
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

### `livespec_runtime.credentials`

SHARED-RUNTIME contract per `spec.md` §"Scope boundary": `livespec` core
names NO slot for credential self-heal, so this module concretizes
nothing upstream. The consuming producer is each orchestrator CLI's
process-entry boundary — `livespec-orchestrator-beads-fabro`'s
`.claude-plugin/scripts/bin/_bootstrap.py` imports `decide_credentials`
and `wrapper_launch_failure` and performs the impure act the returned
decision prescribes. The module is PURE: it reads no environment, spawns
no process, touches no filesystem, and NEVER raises.

- `CREDENTIAL_REEXEC_SENTINEL` — the `str` constant
  `"LIVESPEC_CREDENTIAL_REEXEC"`, the environment-variable name a
  performer MAY set before re-exec. Best-effort ONLY: measured
  2026-08-10, no tested credential wrapper preserves it, because
  rebuilding the ambient environment is exactly what a wrapper is for.
  Performers MUST NOT rely on it alone.
- `CREDENTIAL_REEXEC_ARGV_MARKER` — the `str` constant
  `"--livespec-credential-reexec"`, the LOAD-BEARING one-hop loop guard.
  A performer MUST append it to the `Reexec.argv` vector before
  `os.execvp`, and MUST strip every occurrence from `sys.argv` before
  its own argument parser sees it; `decide_credentials` is called on the
  UNSTRIPPED argv. Its presence anywhere in `argv` means "already
  re-execed". The guard is the OR of this marker and the env sentinel:
  whichever survives the hop terminates the recursion.
- `Proceed` — frozen, slotted, kw-only dataclass with the single field
  `kind: Literal["proceed"]`. The no-op decision: the required secrets
  are present, so run normally.
- `Reexec` — frozen, slotted, kw-only dataclass carrying
  `argv: tuple[str, ...]` (REQUIRED) and `kind: Literal["reexec"]`.
  `argv` is the literal vector for `os.execvp(argv[0], argv)`, namely
  `[*credential_wrapper, executable, *argv]`. This module deliberately
  does NOT append the argv marker: placement is the performer's concern,
  and `Reexec.argv` stays the exact wrapper-prefixed vector.
- `Fail` — frozen, slotted, kw-only dataclass carrying `message: str`
  (REQUIRED) and `kind: Literal["fail"]`. Reached when the secrets are
  still absent AFTER a re-exec, or when they are absent and no
  `credential_wrapper` is configured. `message` is an actionable
  diagnostic naming what is missing.
- `CredentialDecision` — the `TypeAlias` for the three-variant union
  `Proceed | Reexec | Fail`, discriminated on the `Literal[...]`-typed
  `kind` field exactly as `cross_repo.types.DependsOnEntry` is, so
  pyright narrows union members on `match decision.kind: ...` dispatch.
- `decide_credentials(*, required: Sequence[str], credential_wrapper:
  Sequence[str], environ: Mapping[str, str], executable: str, argv:
  Sequence[str]) -> CredentialDecision` — the total decision function.
  `required` names the secret environment variables the CLI needs;
  `credential_wrapper` is the `.livespec.jsonc` argv-prefix (possibly
  empty); `environ` is a snapshot of the process environment. It NEVER
  raises and performs no I/O, so it is exhaustively testable without a
  process.
- `wrapper_launch_failure(*, required: Sequence[str],
  credential_wrapper: Sequence[str]) -> Fail` — the fail-soft
  diagnostic a performer returns when the wrapper handoff itself could
  not be launched.

### `livespec_runtime.attention_item`

SHARED-RUNTIME contract per `spec.md` §"Scope boundary": `livespec`
core names no slot for it. Consuming producers are the orchestrator,
overseer, and console-facing components of the livespec family that
construct attention records.

- `AttentionKind` — a closed `Literal` whose members are exactly
  `human-valve`, `impl`, `spec`, `plan`, `hygiene`, `internal`,
  `host-only`. The set MUST be closed. Adding a member is a
  minor-version bump per `non-functional-requirements.md`
  §"Versioning" for wire consumers, and MUST be treated as coordinated
  for consumers that exhaustively match on the type.
- `AttentionUrgency` — a closed `Literal` of exactly `high`, `medium`,
  `low`.
- `HandoffKind` — a closed `Literal` of exactly `drive`,
  `livespec-op`, `plan`, `shell`.
- `SourceRef` — frozen, slotted, kw-only. Fields: `repo: str`,
  `work_item: str | None = None`, `path: str | None = None`.
- `Handoff` — frozen, slotted, kw-only. Fields: `kind: HandoffKind`,
  `command: str`, `action_id: str | None = None`. A `Handoff` MUST
  carry an executable action, never a bare pointer.
- `AttentionItem` — frozen, slotted, kw-only. Fields: `id: str`,
  `kind: AttentionKind`, `urgency: AttentionUrgency`, `summary: str`,
  `source_ref: SourceRef`, `handoff: Handoff`. Constructing an
  `AttentionItem` whose `id` fails `validate_attention_item_id` MUST
  raise `InvalidAttentionItemIdError`. Validation happens at
  construction, so no `AttentionItem` value can exist with an invalid
  id.
- `InvalidAttentionItemIdError` — raised when an `AttentionItem` is
  constructed with an `id` that fails `validate_attention_item_id`. It
  MUST subclass `Exception` directly, per `constraints.md`
  §"Public-surface constraints". Its message MUST name the rejected id.
- `validate_attention_item_id(*, id: str) -> bool` — the stable-ID
  grammar. An id MUST be colon-separated. Two-part ids
  `<prefix>:<subject>` MUST be accepted for prefixes `impl` and
  `plan`. Three-part ids `<prefix>:<class>:<subject>` MUST be accepted
  for prefixes `host-only`, `valve`, `hygiene`, `spec`, and `internal`.
  Every
  component after the prefix MUST be non-empty and MUST NOT be purely
  decimal, so that ids are stable natural keys rather than positional
  indices.

The DECLARED kind-to-prefix mapping, per `constraints.md`
§"Public-surface constraints", is the single source of truth the
mechanical lockstep check asserts against:

| `AttentionKind` | stable-ID prefix | arity |
|---|---|---|
| `human-valve` | `valve` | three-part |
| `impl` | `impl` | two-part |
| `spec` | `spec` | three-part |
| `plan` | `plan` | two-part |
| `hygiene` | `hygiene` | three-part |
| `internal` | `internal` | three-part |
| `host-only` | `host-only` | three-part |

`human-valve` is the ONE entry whose prefix differs in literal text
from its kind. The difference is retained deliberately, to preserve
every already-emitted `valve:` natural key. Changing any prefix in this
table is a MAJOR-version change, because it invalidates ids already in
circulation.

### `livespec_runtime.needs_attention`

SHARED-RUNTIME contract per `spec.md` §"Scope boundary": `livespec`
core names no slot for it. Consuming producers are the same set named
above.

- `SpecNextOutput` — frozen, slotted, kw-only. Fields: `op: str`,
  `spec_target: str`, `summary: str`, `command: str`,
  `urgency: AttentionUrgency = "medium"`.
- `ImplNextOutput` — frozen, slotted, kw-only. Fields:
  `work_item: str`, `summary: str`, `command: str`,
  `urgency: AttentionUrgency = "high"`.
- `WorkItemHumanValveLane` — frozen, slotted, kw-only. Fields:
  `verb: str`, `work_item: str`, `summary: str`, `action_id: str`,
  `command: str`, `urgency: AttentionUrgency = "high"`.
- `PlanThreadOutput` — frozen, slotted, kw-only. Fields: `topic: str`,
  `path: str`, `summary: str`, `command: str`,
  `urgency: AttentionUrgency = "medium"`.
- `HygieneScanFinding` — frozen, slotted, kw-only. Fields: `type: str`,
  `resource: str`, `path: str`, `summary: str`, `command: str`,
  `urgency: AttentionUrgency = "low"`.
- `compose_needs_attention(*, repo: str, spec_next: SpecNextOutput |
  None = None, impl_next: ImplNextOutput | None = None,
  human_valve_lanes: Iterable[WorkItemHumanValveLane] = (),
  plan_threads: Iterable[PlanThreadOutput] = (),
  hygiene_scan: Iterable[HygieneScanFinding] = ()) ->
  list[AttentionItem]`.

The composer MUST be PURE: it MUST NOT read a ledger, journal,
filesystem, or configuration; it MUST NOT resolve an executable
command; and it MUST receive every fact as an already-derived injected
input. Ordering MUST be deterministic for a given input.

Because every returned item is constructed, `compose_needs_attention`
MUST propagate `InvalidAttentionItemIdError` when any injected input
composes an invalid id. It MUST NOT omit the offending candidate, and
MUST NOT return a partial list alongside a suppressed failure. Refusing
the call is the ratified surfaced-failure form for this library.

The composed id for each input class MUST be:

| Input class | Composed id | Kind |
|---|---|---|
| `WorkItemHumanValveLane` | `valve:<verb>:<work_item>` | `human-valve` |
| `ImplNextOutput` | `impl:<work_item>` | `impl` |
| `SpecNextOutput` | `spec:<op>:<spec_target>` | `spec` |
| `PlanThreadOutput` | `plan:<topic>` | `plan` |
| `HygieneScanFinding` | `hygiene:<type>:<resource>` | `hygiene` |

The kinds `internal` and `host-only` are producer-constructed and have
NO composer input class; producers construct those items directly.

### `livespec_runtime.hygiene_scan`

SHARED-RUNTIME contract per `spec.md` §"Scope boundary": `livespec` core
names NO slot for repository hygiene scanning. This module is the
family's SINGLE ratified import path; its seven companion modules
(`hygiene_scan_cli`, `hygiene_scan_context`, `hygiene_scan_findings`,
`hygiene_scan_types`, `hygiene_scan_worktree_dirt`,
`hygiene_scan_worktree_merge`, `hygiene_scan_worktrees`) are
size-decomposition split-outs declared internal below and MUST NOT be
imported directly. The consuming producers are
`livespec-orchestrator-beads-fabro` and `livespec-orchestrator-git-jsonl`
(both call `scan_hygiene` from their `commands/needs_attention.py` and
splice the returned list into `compose_needs_attention`), and `livespec`
itself (its `dev-tooling/reap_stale_worktrees.py` imports
`detect_stale_worktrees` and `GitWorktree`).

- `scan_hygiene(*, repo_path: Path, repo_name: str | None = None, now:
  datetime | None = None, stale_days: int = 30, include_prs: bool = True,
  runner: CommandRunner | None = None) -> list[AttentionItem]` — the
  family's entry point: current repo hygiene findings, already normalized
  to the ratified `livespec_runtime.attention_item.AttentionItem` shape.
  ⛔ THE RAILWAY TERMINATES HERE AND THE RETURN TYPE IS HELD ON PURPOSE.
  Widening it to `IOResult` is a coordinated multi-repo change, because
  both orchestrators consume this signature across a repo boundary; it
  MUST NOT be taken as a side effect of putting a leaf on the railway.
- `detect_stale_worktrees(*, repo_path: Path, runner: CommandRunner |
  None = None) -> list[GitWorktree]` — the stale-worktree CANDIDATE set
  for `repo_path`. The second signature held for the same cross-repo
  reason: `livespec`'s worktree reaper consumes it directly.
- `stale_worktree_findings(*, context: ScanContext) ->
  IOResult[list[HygieneScanFinding], CommandUnavailable]` — the same
  detection expressed as findings, on the railway. It takes a
  `ScanContext` the family builds internally, so `scan_hygiene` is the
  practical entry point for a consumer that does not hold one.
- `GitWorktree` — frozen, slotted, kw-only dataclass: a parsed
  `git worktree list --porcelain` record. Fields: `path: Path`
  (REQUIRED), `head: str | None = None`, `branch: str | None = None`,
  `detached: bool = False`, `prunable_reason: str | None = None`.
- `CommandResult` — frozen, slotted, kw-only dataclass: a captured
  command result for the injectable git/gh reads. Fields:
  `stdout: str = ""`, `stderr: str = ""`, `returncode: int = 0`.
- `CommandUnavailable` — frozen, slotted, kw-only dataclass carrying
  `argv: str` and `detail: str` (both REQUIRED): a command the scan
  depends on could not be SPAWNED. Deliberately NOT inhabited by "the
  command ran and exited non-zero" — every reader in this subsystem
  already branches on `returncode`.
- `CommandRunner` — the `TypeAlias` for the injectable command seam
  every entry point above accepts as `runner`. It is what lets a
  consumer drive the scan against fixtures instead of a live repo, per
  `non-functional-requirements.md` §"Test discipline".
- `ScanContext` — frozen, slotted, kw-only dataclass: the resolved git
  context shared by the hygiene checks. Fields: `repo_path: Path`,
  `repo_name: str`, `primary_path: Path`, `current_path: Path`,
  `base_ref: str`, `default_branch: str`, `now: datetime`,
  `stale_after: timedelta`, `runner: CommandRunner` (all REQUIRED). It
  is the argument type of `stale_worktree_findings`.
- `main(*, argv: list[str], environ: Mapping[str, str], stdout: TextIO,
  stderr: TextIO, runner: CommandRunner | None = None) -> int` — the
  injectable CLI adapter for `livespec-hygiene-scan`, returning a
  process exit code. Every process input and output is a parameter, so
  the adapter is testable without a process.
- `run() -> int` — the process entry point: wires the real `sys.argv`,
  `os.environ`, and standard streams into `main` and returns its exit
  code. This is the console-script half of the pair; it performs the I/O
  `main` refuses to reach for.

IMPL CO-REQUISITE — the entry point's two additive re-exports. `CommandRunner` appears in the `runner` parameter of BOTH `scan_hygiene` and `detect_stale_worktrees`, and `ScanContext` is the argument type of `stale_worktree_findings`; today neither is in `livespec_runtime/hygiene_scan.py`'s `__all__`, so a consumer passing `runner=` cannot name the type it is passing. `hygiene_scan.py` already IMPORTS `CommandRunner`; it MUST also re-export `ScanContext` and add both to `__all__`, taking it from 8 names to 10. Adding a public symbol is **Minor** per `non-functional-requirements.md` §"Versioning".

IMPL CO-REQUISITE — the seven narrowings. Each of the following modules is DECLARED INTERNAL; its `__all__` narrows to the empty list. Names stay module-level and public in Python terms, so nothing is renamed and no cross-module private import is created:

- `livespec_runtime.hygiene_scan_cli` — `__all__` narrows from 2 names to `[]`, dropping `main`, `run`.
- `livespec_runtime.hygiene_scan_context` — `__all__` narrows from 9 names to `[]`, dropping `DEFAULT_STALE_DAYS`, `GH_READ_BUDGET_FLOOR`, `budgeted_gh_read`, `build_context`, `git`, `parse_worktrees`, `quote_path`, `run_command`, `worktrees`.
- `livespec_runtime.hygiene_scan_findings` — `__all__` narrows from 4 names to `[]`, dropping `GH_PR_FIELDS`, `primary_health_findings`, `stale_branch_findings`, `stale_pr_findings`.
- `livespec_runtime.hygiene_scan_types` — `__all__` narrows from 5 names to `[]`, dropping `CommandResult`, `CommandRunner`, `CommandUnavailable`, `GitWorktree`, `ScanContext`.
- `livespec_runtime.hygiene_scan_worktree_dirt` — `__all__` narrows from 4 names to `[]`, dropping `WorktreeDirt`, `removal_caveat`, `worktree_dirt`, `worktree_subject`.
- `livespec_runtime.hygiene_scan_worktree_merge` — `__all__` narrows from 3 names to `[]`, dropping `branch_was_rebase_merged`, `head_is_merged`, `head_is_patch_equivalent`.
- `livespec_runtime.hygiene_scan_worktrees` — `__all__` narrows from 2 names to `[]`, dropping `detect_stale_worktrees`, `stale_worktree_findings`.

⚠️ `hygiene_scan_cli.main` and `hygiene_scan_cli.run` are narrowed HERE, not deleted: `livespec_runtime/hygiene_scan.py` imports them and re-exports them under its own ratified `__all__`, and the console-script entry keeps pointing at the same callables. What narrows is the second, undocumented import path.

### `livespec_runtime.spec_governance`

SHARED-RUNTIME contract per `spec.md` §"Scope boundary": `livespec` core
names NO slot for it — it is the LOADER core's own specification points
at. `livespec` core's own `SPECIFICATION/constraints.md`, in its "Locked
vendored libs" constraint, names `livespec_runtime.spec_governance`
explicitly as the reason the `livespec_runtime` package cannot be pruned
from core's vendored tree.
The consuming producers are `livespec` core
(`.claude-plugin/scripts/livespec/spec_governance/registry.py` imports
`ConfigValueType`, `ManifestRow`, and `manifest_rows`;
`.../spec_governance/default_block.py` imports `documented_defaults` and
`verify_default_block`), `livespec`'s own dev-tooling checks
(`spec_governance_manifest.py`, `spec_governance_template.py`), and the
`check-spec-governance-default-block` verifier shipped by
`livespec-driver-claude`, `livespec-driver-pi`, `livespec-overseer`,
`livespec-console-beads-fabro`, `livespec-orchestrator-beads-fabro`, and
`livespec-orchestrator-git-jsonl`, all of which import
`verify_livespec_jsonc_default_block`.

- `ConfigValueType` — the `TypeAlias` for `str`: the declared type of a
  manifest row's value.
- `ManifestRow` — frozen, slotted, kw-only dataclass: the wire
  projection of one registry row. Fields: `key: str`,
  `value_type: ConfigValueType`, `safe_default` (the row's declared safe
  default), `per_proposal_override: str | None`, and
  `allowed_values: list[str]` (all REQUIRED).
- `BlockDrift` — frozen, slotted, kw-only dataclass naming the three
  ways a documented block can disagree with the manifest. Fields:
  `missing: list[str]`, `extra: list[str]`, `default_drift: list[str]`
  (all REQUIRED).
- `BlockVerification` — frozen, slotted, kw-only dataclass: the result of
  comparing one source file's default block to the manifest. Fields:
  `documented: dict[str, Any] | None`, `expected: dict[str, Any]`, and
  `drift: BlockDrift | None` (all REQUIRED). A `drift` of `None` means
  no disagreement; a `documented` of `None` means the file documents no
  defaults.
- `UnterminatedGovernanceBlockError` — raised when a `spec_governance`
  comment block OPENS but never balances. It MUST subclass `Exception`
  directly, per `constraints.md` §"Public-surface constraints". It exists
  so a malformed block is a FAILURE rather than folded into
  `documented_defaults`' absence-shaped `None`, which would let a
  truncated block read as "this file documents no defaults" — the wrong
  direction for a drift detector.
- `manifest_rows() -> list[ManifestRow]` — load the hosted
  spec-governance API-key manifest.
- `documented_defaults(*, text: str) -> dict[str, Any] | None` — extract
  the commented `spec_governance` object from one source file's TEXT
  (the caller owns the read). `None` is an ABSENCE with exactly one
  meaning: no block, a non-object block, or an empty one. A malformed
  block raises `UnterminatedGovernanceBlockError`; malformed JSON raises
  `json.JSONDecodeError`.
- `verify_default_block(*, text: str, manifest: list[ManifestRow]) ->
  BlockVerification` — compare one commented defaults block against the
  manifest's safe defaults.
- `verify_livespec_jsonc_default_block(*, path: Path) ->
  Result[dict[str, Any], str]` — verify one `.livespec.jsonc` file
  against the hosted manifest. Expected disagreements ride the `Failure`
  track carrying a human-readable reason; this is the entry point every
  fleet member's `check-spec-governance-default-block` verifier maps onto
  a process exit code.

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
      "pinned": "v0.25.0" // x-release-please-version
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
livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.25.0" } # x-release-please-version
```

Or as a runtime dependency:

```toml
[project]
dependencies = [
    "livespec-runtime>=0.2.0",
]

[tool.uv.sources]
livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.25.0" } # x-release-please-version
```

The tag value in `[tool.uv.sources]` MUST match the `compat.pinned`
value in `.livespec.jsonc` for the consumer; drift between the two is
the consumer's responsibility to enforce (doctor does not yet cross-
check them).

## System dependencies

- `gh` CLI — REQUIRED in any environment where consumers invoke
  `resolve_ref` against `PullRequestDependency` or `BranchDependency`
  entries. The runtime does NOT shell-detect `gh`'s presence; absence
  surfaces as an `OSError`-shaped transport failure (a missing binary
  raises `FileNotFoundError`, not `CalledProcessError`, which can only
  arise once the command actually runs), which the provider folds onto
  its failure track as `GithubFailure` rather than raising, and which
  (via the retry layer) collapses to `RefStatus.UNKNOWN`.
- `gh auth status` — MUST be successful for the `gh` invocations to
  succeed. Authentication is the consumer environment's responsibility.
- `openssl` CLI — REQUIRED in any environment where consumers mint
  GitHub App installation tokens via `livespec_runtime.github_auth`
  (the production RS256 signer shells out to it). Like `gh`, it is
  NOT pinned by this library; the consumer environment owns the
  install.
- The Python runtime dependencies outside the standard library are
  `returns` (the `Result`/`IOResult` types that appear in the public
  signatures above — a consumer cannot express those contracts without
  it) and `typing_extensions` (for `assert_never` on Python <3.11 —
  the project's `requires-python` is `>=3.10.16`). The authoritative
  current list lives in `pyproject.toml` and `uv.lock`.

## Versioning

Semver bump rules and the consumer pin-and-bump mechanism live in
`non-functional-requirements.md` §"Versioning". Surface-change
classifications (additions / removals / refactors) are referenced
by `spec.md` §"Public surface" and by the per-symbol bullets above.
