---
topic: public-surface-inventory-completes-shipped-modules
author: claude-opus-5
created_at: 2026-09-06T12:14:42Z
spec_commitments:
  impl_followups:
    - id_hint: narrow-github-budget-split-out-modules
      description: |
        Land the github_budget narrowing Proposal 2 declares: narrow `__all__` to `[]` in github_budget_client, github_budget_client_support, github_budget_measurement, and github_budget_types; add GithubBudgetResult and GithubBudgetTransport to livespec_runtime/github_budget.py's re-exports and `__all__`; delete those four rows from tests/public-surface-debt.json (they go stale only when the `__all__` empties, because the inventory check reads the tree). Commit subject carries a `!` marker and a BREAKING CHANGE footer so release_bump_classification accepts the surface delta; the Major classification releases as a MINOR 0.X.0 bump under the pre-major provision.
    - id_hint: narrow-hygiene-scan-split-out-modules
      description: |
        Land the hygiene_scan narrowing Proposal 3 declares: narrow `__all__` to `[]` in hygiene_scan_cli, hygiene_scan_context, hygiene_scan_findings, hygiene_scan_types, hygiene_scan_worktree_dirt, hygiene_scan_worktree_merge, and hygiene_scan_worktrees; re-export ScanContext from livespec_runtime/hygiene_scan.py and add it and CommandRunner to its `__all__`; delete those seven rows from tests/public-surface-debt.json. Same `!` / BREAKING CHANGE commit discipline and the same Major-released-as-minor classification.
    - id_hint: declare-attention-cross-repo-public-api-residue
      description: |
        Resolve the cross_repo_public_api residue Proposal 6e names. Re-run livespec-dev-tooling's central fleet consumption measurement (the authoritative vantage; a repo-local oracle cannot see a sibling's import), and if it confirms this proposal's local finding, declare livespec_runtime/needs_attention.py::compose_needs_attention and livespec_runtime/hygiene_scan.py::scan_hygiene in pyproject.toml's [tool.livespec_dev_tooling].cross_repo_public_api with their consuming members named. The key is tightening-only, so declaring them ARMS the Result-return rule over two functions whose non-IOResult return types are deliberately held for cross-repo reasons; expect the dual-shape consumer wiring to land in the consuming repos FIRST, per the livespec-dev-tooling-dx8l shape the key's own comment describes.
---

## Proposal: Ratify livespec_runtime.credentials

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md

### Summary

Ratify `livespec_runtime.credentials` in full. Add a `### livespec_runtime.credentials` section to `contracts.md` §"Module-level public surface" carrying one bullet for each of the eight names in the module's `__all__`, and drop the family from `spec.md` §"Public surface"'s acknowledged-debt paragraph (the consolidated replacement paragraph is in Proposal 6). No `__all__` changes, so the change is additive prose and triggers no Versioning classification; the module's row in `tests/public-surface-debt.json` goes stale on landing and MUST be deleted in the same changeset.

### Motivation

`spec.md` §"Public surface" records this module as ACKNOWLEDGED DEBT and requires that it be "ratified or explicitly declared internal in a subsequent proposal". This is that proposal, filed under `livespec-runtime-x87`, which carries the prepared payload from `plan/runtime-backlog-drain/research/005-mqsxsu4-public-surface-reconciliation.md` §5b after `livespec-runtime-mqsxsu.4` delivered the mechanical half (the inventory check and the shrink-only register, released as v0.23.0) and stopped short of the documentation half for want of spec-lane authorization.

RATIFY rather than declare internal, on measured evidence. `livespec-orchestrator-beads-fabro`'s `.claude-plugin/scripts/bin/_bootstrap.py` performs a PRODUCT import of `decide_credentials` and `wrapper_launch_failure` at its process-entry boundary, and its `tests/bin/test_bootstrap.py` monkeypatches `livespec_runtime.credentials.decide_credentials` by dotted path in six places. Both functions are ALREADY declared in this repo's `pyproject.toml` `[tool.livespec_dev_tooling].cross_repo_public_api` key as cross-boundary product imports, measured centrally by livespec-dev-tooling's fleet consumption row. A module whose functions the fleet's own consumption measurement names cannot honestly be called implementation detail.

Every one of the eight exported names is reachable from that consumer: the two constants are the loop guard the performer must append and strip, the three dataclasses plus their union alias are the decision the performer matches on, and the two functions are the entry points. There is no name in this `__all__` that a narrowing could honestly remove.

### Proposed Changes

In `SPECIFICATION/contracts.md`, §"Module-level public surface", INSERT the following `###` section immediately after `### `livespec_runtime.github_auth.credential_helper`` and immediately before `### `livespec_runtime.attention_item``. That placement puts the pure decision brain next to the credential-helper surface that shares its subject; section ORDER inside the inventory is not load-bearing, and a maintainer who prefers to append it with the other shared-runtime families may do so without changing this proposal's substance.

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

In `SPECIFICATION/spec.md`, §"Public surface", `livespec_runtime.credentials` is removed from the acknowledged-debt paragraph. The consolidated replacement paragraph, covering all five families at once, is in Proposal 6 of this file so the five sections do not each rewrite the same prose.

In `tests/public-surface-debt.json`, DELETE the `livespec_runtime.credentials` row. The register is shrink-only and this row is stale the moment the section above lands: `tests/livespec_runtime/test_public_surface_inventory.py::test_the_debt_register_carries_no_stale_rows` fails with `now ratified in contracts.md (delete the row)` until it is deleted. It MUST therefore be deleted in the revise changeset itself.

No `## ` heading is added, changed, or removed, so `tests/heading-coverage.json` needs no new entry for this section — the existing `contracts.md` / `## Module-level public surface` entry already covers it, and its mapped test is precisely the inventory check that reads these bullets. Proposal 6 records the heading-coverage co-edits this file DOES make.

No `__all__` changes, so `non-functional-requirements.md` §"Versioning" is not engaged and no release-bump classification is owed for this section.

## Proposal: Ratify the livespec_runtime.github_budget facade and declare its four split-out modules internal

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Dispose of all five `github_budget` modules. RATIFY the facade `livespec_runtime.github_budget` with one bullet per exported name, and DECLARE INTERNAL its four size-decomposition split-outs (`github_budget_client`, `github_budget_client_support`, `github_budget_measurement`, `github_budget_types`) by narrowing each `__all__` to `[]`. The facade additionally gains `GithubBudgetResult` and `GithubBudgetTransport` as re-exports so every type naming a ratified signature is expressible from the ratified import path. Net Versioning classification: Major (removals) plus Minor (two additions), released as one MINOR `0.X.0` bump under the pre-major provision.

### Motivation

`spec.md` §"Public surface" records "the `livespec_runtime.github_budget` family" as ACKNOWLEDGED DEBT requiring ratify-or-declare-internal. The five modules export 56 name-slots between them, and a blanket disposition would be wrong in either direction.

WHY THE FACADE IS RATIFIED, not internal. `GithubBudgetUnmeasurable` is already a member of the RATIFIED failure union `GithubFailure` documented under `### livespec_runtime.cross_repo.providers.github`, so any consumer that lands on that provider's failure track holds one of this family's records and must be able to name its type. Proposal 5 of this file ratifies `cross_repo.providers.github_process`, whose `budgeted_gh` and `budget_failure` signatures name `GhInvocation` and `GithubBudgetFailure`. A type that appears in a ratified signature is consumer-visible by construction; calling it implementation detail would be false.

WHY THE FOUR SPLIT-OUTS ARE INTERNAL, not ratified. Measured across the nine fleet member checkouts on this host on 2026-09-06, NO repository outside this one imports any `github_budget*` module: the only importers are `livespec_runtime.cross_repo.providers.github_process` and the vendored copies of this same package that siblings carry under `.claude-plugin/scripts/_vendor/`. The split-outs exist because `file_lloc` hard-gates this repo at 250 LLOC, not because anyone asked for four import paths. Ratifying them would pin plumbing as v1 stable API: `github_budget_client_support` exports `header_value`, `int_option`, `mapping_option`, `poll_interval`, and `backoff_seconds`, and this repo's own `pyproject.toml` `total_absence_returns` block already describes `header_value` and `mapping_option` as helpers reading a mapping the caller ALREADY HOLDS. Declaring them stable API would contradict a declaration this repo has already made about them. Nine of the thirteen `github_budget_measurement` names are re-exported by the facade and stay reachable there; the four that are not (`RATE_LIMIT_RESOURCE`, `gh_argv`, `gh_headers`, `gh_status_code`, `snapshot_from_headers`, `record_budget_signal`) are the `gh`-shaped internals `gh_transport` exists to encapsulate.

MIXED DISPOSITION IS DELIBERATE, and is offered for objection. The work-item's acceptance describes each family section as either ratifying the family or declaring it internal; this section does both, module by module, because that is what the consumption evidence supports and because the acceptance's own wording scopes each branch PER MODULE ("a `###` section per module"; "the `__all__` narrowing named per module"). The alternative — ratifying all five — is available and is a strictly larger commitment: it would add 37 more bullets and pin the client's option-reading helpers as stable API. A maintainer who prefers it can take this section's ratified bullets and drop the narrowing at revise.

### Proposed Changes

In `SPECIFICATION/contracts.md`, §"Module-level public surface", INSERT the following `###` section after `### `livespec_runtime.hygiene_scan`` (Proposal 3) and before `### `livespec_runtime.spec_governance`` (Proposal 4).

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
- `GithubBudgetedClient` — a slotted, kw-only dataclass (deliberately NOT
  frozen: it is the ONE stateful object in the family, holding the
  conditional-read cache and the mutation-pacing clock). Fields:
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

*Versioning classification, per `non-functional-requirements.md`
§"Versioning".* Removing a public symbol is **Major**, which the
PRE-MAJOR PROVISION releases as a MINOR `0.X.0` bump rather than
`1.0.0`. The commit that lands the narrowing MUST therefore carry a `!`
marker and a `BREAKING CHANGE:` footer, which is also what
`release_bump_classification` requires: that check reads `__all__` under
`source_trees` and refuses a bump weaker than the surface delta. Runtime
blast radius is nil — `__all__` governs the DECLARED surface and
`import *`, not direct imports, and no consumer imports these modules —
but the conservative classification is the correct one and the cheaper
error. This is the same disposition the `github_auth.mint` narrowing took
under `livespec-runtime-mqsxsu.4` (research/005 §4a), released as
v0.23.0.

In `SPECIFICATION/spec.md`, §"Public surface", the `github_budget` family is removed from the acknowledged-debt paragraph; see Proposal 6 for the consolidated replacement text.

*Effect on `tests/public-surface-debt.json`.* The register is
shrink-only: a row is stale, and MUST be deleted, once its module is
ratified, is declared internal, or stops exporting. The RATIFIED module
in this family goes stale the moment its `###` section lands, so its row
MUST be deleted in the revise changeset itself or
`tests/livespec_runtime/test_public_surface_inventory.py` fails. The
DECLARED-INTERNAL modules' rows do NOT go stale until the `__all__`
narrowing lands, because the check reads the tree rather than the prose;
their rows MUST therefore be deleted in the narrowing changeset, which
this proposal declares as a spec→impl commitment rather than leaving
implicit.

Concretely: delete the `livespec_runtime.github_budget` row in the revise changeset (stale on ratification), and delete the `github_budget_client`, `github_budget_client_support`, `github_budget_measurement`, and `github_budget_types` rows in the narrowing changeset (stale when their `__all__` empties, because `_exporting_modules()` drops a module with no non-empty `__all__`).

No `## ` heading is added, so `tests/heading-coverage.json` needs no new entry for this section.

## Proposal: Ratify the livespec_runtime.hygiene_scan entry point and declare its seven split-out modules internal

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Dispose of all eight `hygiene_scan` modules. RATIFY the entry point `livespec_runtime.hygiene_scan` with one bullet per exported name, and DECLARE INTERNAL its seven size-decomposition split-outs by narrowing each `__all__` to `[]`. The entry point additionally gains `CommandRunner` and `ScanContext` as re-exports, because both already appear in signatures it exports. This section also disposes of the `main` / `run` launcher pair that research/005 §4c deliberately deferred to the family decision: they are ratified as the console-script surface. Net classification: Major (removals) plus Minor (two additions), released as one MINOR `0.X.0` bump under the pre-major provision.

### Motivation

`spec.md` §"Public surface" records "`livespec_runtime.hygiene_scan` and its companion modules" as ACKNOWLEDGED DEBT requiring ratify-or-declare-internal. Eight modules export 37 name-slots.

WHY THE ENTRY POINT IS RATIFIED. Three names are consumed ACROSS REPO BOUNDARIES by product code, and the module's own source says so: `scan_hygiene`'s docstring carries a `⛔ THE RAILWAY TERMINATES HERE, AND THE SIGNATURE IS HELD ON PURPOSE` note naming `livespec-orchestrator-beads-fabro` and `livespec-orchestrator-git-jsonl` as callers from their `commands/needs_attention.py`, and `detect_stale_worktrees` carries the same note. Verified directly: both orchestrators' `commands/needs_attention.py` import `scan_hygiene`, and `livespec/dev-tooling/reap_stale_worktrees.py` imports `detect_stale_worktrees` and `GitWorktree`. A module carrying an in-source cross-repo signature hold is the opposite of implementation detail.

WHY THE SEVEN COMPANIONS ARE INTERNAL. Measured across the nine fleet member checkouts on this host on 2026-09-06, every external import of this subsystem goes through `livespec_runtime.hygiene_scan`; the only importers of `hygiene_scan_cli`, `hygiene_scan_context`, `hygiene_scan_findings`, `hygiene_scan_types`, `hygiene_scan_worktree_dirt`, `hygiene_scan_worktree_merge`, and `hygiene_scan_worktrees` are this package's own modules and the vendored copies of this same package siblings carry under `.claude-plugin/scripts/_vendor/`. They exist because `file_lloc` hard-gates this repo at 250 LLOC. Ratifying `hygiene_scan_worktree_merge.head_is_patch_equivalent` or `hygiene_scan_context.quote_path` as v1 stable API would recreate exactly the debt this proposal exists to retire.

THE `main` / `run` QUESTION, ANSWERED. research/005 §4c registered these two with the reasoning that narrowing them ahead of the family decision "would pre-empt the very proposal that must decide whether the family is ratified or declared internal". Decided here: the pair is RATIFIED on `livespec_runtime.hygiene_scan`, because `livespec-hygiene-scan` is a console entry point this library ships and `main`'s fully-injectable signature (argv, environ, stdout, stderr, runner) is a real testable contract rather than an accident. The DUPLICATE pair on `hygiene_scan_cli` is narrowed with the rest of that module, so the launcher has exactly one ratified import path. research/005 §4's aside is worth restating: a whole-file word-boundary match CREDITS the bare words `main` and `run` from unrelated prose in the inventory, which is why the check's first obligation is at MODULE level and why this decision had to be made explicitly rather than allowed to pass.

MIXED DISPOSITION IS DELIBERATE, and is offered for objection on the same terms as Proposal 2: the acceptance's branches are scoped per module, the evidence splits per module, and a maintainer who prefers to ratify all eight can take these bullets and drop the narrowing at revise.

### Proposed Changes

In `SPECIFICATION/contracts.md`, §"Module-level public surface", INSERT the following `###` section immediately after `### `livespec_runtime.needs_attention``, at the end of the inventory. That placement puts it next to the `AttentionItem` and `HygieneScanFinding` surfaces its own signatures name.

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

*Versioning classification, per `non-functional-requirements.md`
§"Versioning".* Removing a public symbol is **Major**, which the
PRE-MAJOR PROVISION releases as a MINOR `0.X.0` bump rather than
`1.0.0`. The commit that lands the narrowing MUST therefore carry a `!`
marker and a `BREAKING CHANGE:` footer, which is also what
`release_bump_classification` requires: that check reads `__all__` under
`source_trees` and refuses a bump weaker than the surface delta. Runtime
blast radius is nil — `__all__` governs the DECLARED surface and
`import *`, not direct imports, and no consumer imports these modules —
but the conservative classification is the correct one and the cheaper
error. This is the same disposition the `github_auth.mint` narrowing took
under `livespec-runtime-mqsxsu.4` (research/005 §4a), released as
v0.23.0.

In `SPECIFICATION/spec.md`, §"Public surface", the `hygiene_scan` family is removed from the acknowledged-debt paragraph; see Proposal 6 for the consolidated replacement text.

*Effect on `tests/public-surface-debt.json`.* The register is
shrink-only: a row is stale, and MUST be deleted, once its module is
ratified, is declared internal, or stops exporting. The RATIFIED module
in this family goes stale the moment its `###` section lands, so its row
MUST be deleted in the revise changeset itself or
`tests/livespec_runtime/test_public_surface_inventory.py` fails. The
DECLARED-INTERNAL modules' rows do NOT go stale until the `__all__`
narrowing lands, because the check reads the tree rather than the prose;
their rows MUST therefore be deleted in the narrowing changeset, which
this proposal declares as a spec→impl commitment rather than leaving
implicit.

Concretely: delete the `livespec_runtime.hygiene_scan` row in the revise changeset (stale on ratification), and delete the seven companion rows in the narrowing changeset.

No `## ` heading is added, so `tests/heading-coverage.json` needs no new entry for this section.

## Proposal: Ratify livespec_runtime.spec_governance

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/spec.md

### Summary

Ratify `livespec_runtime.spec_governance` in full. Add a `### livespec_runtime.spec_governance` section to `contracts.md` §"Module-level public surface" carrying one bullet for each of the nine names in the module's `__all__`, and drop it from `spec.md` §"Public surface"'s acknowledged-debt paragraph. No `__all__` changes, so the change is additive prose and triggers no Versioning classification.

### Motivation

`spec.md` §"Public surface" records this module as ACKNOWLEDGED DEBT requiring ratify-or-declare-internal. It is the most widely consumed module in the whole debt register, and the case for ratifying it is the strongest of the five.

`livespec` core's OWN specification names it. `livespec/SPECIFICATION/constraints.md` §"Locked vendored libs" states that the `livespec_runtime` package and its `.vendor.jsonc` entry are NOT removed "because core consumes it at runtime beyond that one subtree — notably `livespec_runtime.spec_governance`, the loader for the manifest this specification names as the single declarative source". A module a SIBLING'S RATIFIED SPEC names as the loader for its single declarative source cannot be this library's implementation detail.

Measured across the nine fleet member checkouts on this host on 2026-09-06, eight repositories import it in product or dev-tooling code: `livespec` core (`spec_governance/registry.py` takes `ConfigValueType`, `ManifestRow`, `manifest_rows`; `spec_governance/default_block.py` takes `documented_defaults` and `verify_default_block`; its dev-tooling checks `spec_governance_manifest.py` and `spec_governance_template.py` take `manifest_rows` and the verifier trio), plus `livespec-driver-claude`, `livespec-driver-pi`, `livespec-overseer`, `livespec-console-beads-fabro`, `livespec-orchestrator-beads-fabro`, and `livespec-orchestrator-git-jsonl`, each of whose `check-spec-governance-default-block` verifier imports `verify_livespec_jsonc_default_block`. Three of the nine names — `documented_defaults`, `manifest_rows`, `verify_default_block` — are already declared in this repo's `pyproject.toml` `[tool.livespec_dev_tooling].cross_repo_public_api` key as measured cross-boundary product imports.

The remaining names are reachable from those entry points: `ConfigValueType` and `ManifestRow` are what `manifest_rows` returns, `BlockVerification` and `BlockDrift` are what `verify_default_block` returns, and `UnterminatedGovernanceBlockError` is the failure a caller of `documented_defaults` must expect — this repo's own `total_absence_returns` block records that the exception exists SPECIFICALLY so a malformed block is a failure rather than folded into that function's absence-shaped `None`. A consumer cannot honour that distinction without being able to name the exception. No name here can be honestly narrowed.

### Proposed Changes

In `SPECIFICATION/contracts.md`, §"Module-level public surface", INSERT the following `###` section after `### `livespec_runtime.github_budget`` (Proposal 2), at the end of the inventory.

### `livespec_runtime.spec_governance`

SHARED-RUNTIME contract per `spec.md` §"Scope boundary": `livespec` core
names NO slot for it — it is the LOADER core's own specification points
at. `livespec/SPECIFICATION/constraints.md` §"Locked vendored libs"
names `livespec_runtime.spec_governance` explicitly as the reason the
`livespec_runtime` package cannot be pruned from core's vendored tree.
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

In `SPECIFICATION/spec.md`, §"Public surface", `livespec_runtime.spec_governance` is removed from the acknowledged-debt paragraph; see Proposal 6 for the consolidated replacement text.

In `tests/public-surface-debt.json`, DELETE the `livespec_runtime.spec_governance` row. It is stale the moment the section above lands, so it MUST be deleted in the revise changeset itself.

No `__all__` changes, so `non-functional-requirements.md` §"Versioning" is not engaged. No `## ` heading is added, so `tests/heading-coverage.json` needs no new entry for this section.

## Proposal: Ratify livespec_runtime.cross_repo.providers.github_process as a support module of the providers.github section

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Close the ONE genuine gap in the register — the module registered as `gap-not-yet-recorded-as-debt` rather than acknowledged debt — by ratifying `livespec_runtime.cross_repo.providers.github_process` as a support module of the already-ratified `### livespec_runtime.cross_repo.providers.github` section, with one bullet per exported name. This takes research/005 §5a option 1, the option that research recommended and the work-item's acceptance specifies. No `spec.md` edit is needed: this module was never inside the debt paragraph.

### Motivation

`livespec_runtime.cross_repo.providers.github_process` is the only row in `tests/public-surface-debt.json` carrying `disposition: gap-not-yet-recorded-as-debt`. `spec.md` §"Public surface"'s debt paragraph does not cover it — that paragraph's "and its companion modules" attaches to `hygiene_scan` alone — so it is a fresh gap rather than recorded debt. It exists because `providers/github.py` was decomposed for size, which moved surface out from under a ratified heading without anyone deciding what the new module is.

research/005 §5a offered two options and recommended the first: document the module under its own `###` section naming it a support module of the provider, rather than widening the debt paragraph to name it, because "the module is inside a ratified family, and recording a fresh module as debt the same day it is noticed is how the original 70 accumulated". The work-item's acceptance adopts that recommendation by name.

RE-MEASURED FOR THIS PROPOSAL, and the measurement has MOVED. research/005 §5a and the register row both describe this module as exporting `GithubFailure`, `GithubQueryFailed`, and `completed_gh`. At the current tree `completed_gh` NO LONGER EXISTS: commit d5063b0 ("feat(github_budget): route this repo's own GitHub reads through the budgeted client") replaced it, and the module now exports six names — `GithubFailure`, `GithubQueryFailed`, `budget_failure`, `budgeted_gh`, `spawn_gh`, and `stderr_indicates_http_404`. The section below documents what the tree actually exports, not what the prepared payload predicted. This is exactly the drift the mechanical inventory check exists to catch and is recorded here so the register row's reason is not read as current.

Two of the six names are already ratified: `providers/github.py` re-exports `GithubFailure` and `GithubQueryFailed` (and `GithubBudgetUnmeasurable`) from here, and the provider's ratified section documents the union. The new section names this module as where they are DEFINED and points at the provider section for the contract, so the two sections cannot drift apart. The four remaining names are the budgeted-`gh` seam itself.

### Proposed Changes

In `SPECIFICATION/contracts.md`, §"Module-level public surface", INSERT the following `###` section immediately after `### `livespec_runtime.cross_repo.providers.github`` and immediately before `### `livespec_runtime.cross_repo.retry``, so the support module sits directly under the section it supports.

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

In `tests/public-surface-debt.json`, DELETE the `livespec_runtime.cross_repo.providers.github_process` row — the register's only `gap-not-yet-recorded-as-debt` entry. It is stale the moment the section above lands, so it MUST be deleted in the revise changeset itself.

No `SPECIFICATION/spec.md` edit is owed by this section: the module was never named in the acknowledged-debt paragraph, which is precisely why it was a gap rather than debt.

No `__all__` changes, so `non-functional-requirements.md` §"Versioning" is not engaged. No `## ` heading is added, so `tests/heading-coverage.json` needs no new entry for this section.

## Proposal: Retire the acknowledged-debt paragraph and record the co-edits: scenarios, heading coverage, and the charge-point-7 dispositions

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/scenarios.md
- tests/heading-coverage.json

### Summary

The single place this file rewrites `spec.md` §"Public surface"'s acknowledged-debt paragraph, so the five family sections do not each edit the same prose. It also records what the other five sections deliberately do NOT do: no new `## ` heading is added anywhere, so `tests/heading-coverage.json` needs no new entry; no scenario is written for the ratified families, and the reason is recorded rather than left implicit; and the two dispositions the `homelab-loop-hardening-runtime` completeness review transferred to `livespec-runtime-x87` — F-04 (property-based tests / `cross_repo_public_api` for the attention modules) and F-05 (22 heading-coverage entries owned by a closed work-item) — are recorded, F-05 with a correction to its premise.

### Motivation

Three obligations converge on one section.

FIRST, the debt paragraph. `spec.md` §"Public surface" currently names four families as ACKNOWLEDGED DEBT and requires that each "MUST be ratified or explicitly declared internal in a subsequent proposal". Proposals 1-4 of this file discharge all four. Leaving the paragraph in place would leave the spec asserting debt it no longer carries; letting each of the four sections edit it would produce four conflicting rewrites of one paragraph.

SECOND, the scenario half of gap `gap-vjxowbbp`, absorbed from `livespec-runtime-vbofkr`, which asks that scenarios for the public symbols be "decided per module family in this reconciliation, co-edited with heading coverage in the same propose-change, or consciously exempted with the reason recorded". research/005 §5b decided `github_auth` and `work_items` (both already ratified, both consciously deferred to whichever proposal changes their behaviour) and deferred the 16 debt modules to this proposal, on the ground that "writing scenarios first would presume the answer". This section is where the answer is given.

THIRD, findings F-04 and F-05 of `plan/archive/homelab-loop-hardening-runtime/research/003-completeness-review-2026-09-06.md`, both transferred to `livespec-runtime-x87` by name in that review's re-verification table.

### Proposed Changes

### 6a. `SPECIFICATION/spec.md`, §"Public surface" — the debt paragraph

REPLACE the paragraph beginning `Some shipped modules remain outside the ratified inventory:` and ending `Each MUST be ratified or explicitly declared internal in a subsequent proposal.` WITH:

    Every shipped module that declares a public surface is now inside
    the ratified inventory or is explicitly declared internal there.
    The families that `contracts.md` §"Module-level public surface"
    ratifies as this library's SINGLE import path are
    `livespec_runtime.credentials`, `livespec_runtime.github_budget`,
    `livespec_runtime.hygiene_scan`, and
    `livespec_runtime.spec_governance`. Where a family's entry point is
    ratified, its size-decomposition split-out modules are declared
    INTERNAL and named as such in that family's section: consumers MUST
    import from the ratified entry point, and this repository MAY change
    a split-out's surface without a major classification. A module that
    ships a public surface and appears in NEITHER place is a defect
    rather than tolerated debt, and
    `tests/livespec_runtime/test_public_surface_inventory.py` fails on
    it.

That test's debt register, `tests/public-surface-debt.json`, is shrink-only by construction, so once the last row is deleted the file and its two register-shaped assertions can go with it. Retiring them is NOT proposed here: the register also carries the `# @generated` third-party port's five out-of-scope names, which is a live exclusion that must stay declared somewhere. Whoever deletes the last `unratified_modules` row decides where that declaration lands.

### 6b. `SPECIFICATION/scenarios.md` — conscious exemption, with the reason

NO scenario is added by this proposal, and that is a decision rather than an omission. Per `non-functional-requirements.md` §"Test discipline", a `## Scenario:` heading obliges an INTEGRATION-TIER-OR-ABOVE mapped test in `tests/heading-coverage.json` — a consumer-shaped test that drives a real workflow against `tmp_path`-scoped checkouts. Per family:

- `credentials` — the ratified surface is a PURE total function over injected inputs that performs no I/O and never raises. Its consumer-visible behaviour is the performer's contract (append the argv marker; strip it before parsing; treat the guard as the OR of marker and sentinel), and that contract is stated in the contracts.md bullets above. A scenario would restate them without a consumer-observable workflow to drive. EXEMPT, reason recorded here.
- `spec_governance` — its consumer-observable behaviour is exercised by eight repositories' `check-spec-governance-default-block` verifiers, which is integration coverage this repository cannot host: the workflow is another repo's `.livespec.jsonc` being verified against the hosted manifest. EXEMPT here, and the cross-repo coverage is named rather than claimed as local.
- `hygiene_scan` — `scan_hygiene` and `detect_stale_worktrees` DO have consumer-visible workflows, and they are the two signatures held for cross-repo consumption. A consumer-tier scenario driving `scan_hygiene` against a `tmp_path` git repository would be real coverage. It is NOT written here because this proposal changes no hygiene-scan BEHAVIOUR — it documents the surface as shipped — and a scenario written in a documentation pass would be authored from the implementation rather than from a consumer's expectation, which is the failure mode `livespec-dev-tooling-0z11` records (heading coverage verifies that a scenario HAS a linked test, never that the Then-clause matches what the test asserts). RECORDED AS OWED, not exempt: the first proposal that changes hygiene-scan behaviour co-edits the scenario.
- `github_budget` and `cross_repo.providers.github_process` — their consumer-visible behaviour reaches a consumer only through the ratified `cross_repo.providers.github` surface, which already carries eight mapped `## Scenario:` headings in `tests/heading-coverage.json`. Duplicating them one layer down would make two entries that must move together silently. EXEMPT, reason recorded here.
- `github_auth` and `work_items` — unchanged from research/005 §5b: both are already ratified and export exactly what the inventory documents, so their scenario coverage rides whichever proposal changes their behaviour, not this reconciliation. Recorded as consciously deferred.

### 6c. `tests/heading-coverage.json` — what this proposal does and does not need

The heading-coverage registry tracks `## ` headings. Every section this file adds is a `### ` module section INSIDE the existing `contracts.md` / `## Module-level public surface` heading, and every prose edit lands under an existing `## ` heading (`spec.md` §"Public surface"; `non-functional-requirements.md` §"Versioning"). NO `## ` heading is added, changed, or removed anywhere in this proposal, so NO new registry entry is owed and every existing entry stays valid. The `## Module-level public surface` entry already maps to `tests.livespec_runtime.test_public_surface_inventory.test_every_exported_name_is_ratified_or_its_module_is_registered_as_debt`, which is precisely the test that reads the new sections.

The registry IS co-edited, for the two review findings below. Those edits are landing in the implementation changeset that files this proposal (work-item `livespec-runtime-x87`), NOT deferred to revise, because they are ownership and reason-field corrections that stand independent of whether this proposal is accepted.

### 6d. Finding F-05 — heading-coverage entries owned by a closed work-item

The review found 22 `test: "TODO"` entries whose `work_item` is `livespec-runtime-mqsxsu.2`, which is CLOSED. This is the liveness trap `livespec-runtime-nhs` re-pointed 29 entries to avoid; it passes today only because `no_todo_registry`'s `_probe_work_item_liveness` returns UNVERIFIED with no reachable tracker configured. Under the release tier (`LIVESPEC_FAIL_IF_HEADING_COVERAGE_TODOS_EXIST`), a reachable tracker would fail all 22.

RESOLUTION, landed with this proposal: all 22 TODO entries are re-homed to `livespec-runtime-x87`. Their `reason` fields, which carry the provenance sentence "Adjudicated under livespec-runtime-mqsxsu.2", are left VERBATIM — the adjudication genuinely happened there; what moves is OWNERSHIP of replacing the placeholder, which is what the `work_item` field means per `no_todo_registry`'s entry-schema docstring.

CORRECTION TO THE FINDING'S ARITHMETIC, recorded because it changes what "no entry names a closed work item" requires: 28 entries name `mqsxsu.2`, not 22. The other six are MAPPED entries (a real test, not a TODO), and four further mapped entries name the closed `mqsxsu.4`, `cr4`, and `emu`. `no_todo_registry` reads `work_item` only on TODO entries, so those ten are outside the liveness rule — but they still NAME a closed item, and 15 sibling mapped entries carry no `work_item` field at all. For those ten the field is dropped rather than re-homed: pointing them at `livespec-runtime-x87` would assert that this item adjudicated tests it did not write, whereas their `reason` fields already carry the true provenance verbatim ("Adjudicated under livespec-runtime-mqsxsu.2", "resolved under livespec-runtime-mqsxsu.4", "Closed by livespec-runtime-cr4", "Closed by livespec-runtime-emu"). After both edits no entry's `work_item` names a closed work-item, and no provenance is lost.

### 6e. Finding F-04 — charge point 7's two unrecorded narrowings

The review recorded that property-based tests on the pure attention modules were not added and that "no `cross_repo_public_api` reconciliation artifact exists in this repository", and asked for either a conscious exemption or a fold into this item. Both are recorded in the `reason` fields of the two heading-coverage entries that own the subjects, and both are stated here:

PROPERTY-BASED TESTS — CONSCIOUSLY EXEMPTED, recorded on the `non-functional-requirements.md` / `## Test discipline` entry. `hypothesis` is a declared dev dependency and is used by exactly one test module, `tests/livespec_runtime/test_credentials.py`. The attention modules' ratified surface is dominated by a CLOSED FINITE domain — the declared kind-to-prefix mapping — and `tests/consumer/test_attention_lockstep.py` asserts that mapping is TOTAL over `AttentionKind` and injective into the prefixes, which is exhaustive enumeration over the closed set and is strictly stronger than sampling it. The one genuinely open-domain predicate is `validate_attention_item_id(*, id: str) -> bool`, covered by example across all five grammar classes the ratified grammar names, at both the consumer tier (`tests/consumer/test_attention_id_grammar.py`, five tests) and the unit tier (`tests/livespec_runtime/test_attention_item.py`, four tests). A `hypothesis` property over arbitrary component strings would be an ADDITION to that coverage, not a replacement for it, and is not owed by this pass.

`cross_repo_public_api` — THE FINDING'S PREMISE IS CORRECTED, and a residue is named; recorded on the `contracts.md` / `## Module-level public surface` entry. The artifact DOES exist: `pyproject.toml` `[tool.livespec_dev_tooling].cross_repo_public_api` carries FOURTEEN entries, each naming its consuming member and file, and the block's own comment records that the list was MEASURED centrally by livespec-dev-tooling's fleet consumption row against all nine members' master tarballs rather than asserted locally (record: `plan/rop-railway-enforcement/5cai-fleet-measurement.md` in that repo; filed as `livespec-dev-tooling-nkkv`). What is true is that NO entry names an attention module, and a local re-measurement for this proposal found that this is a genuine RESIDUE rather than an exemption: `livespec-orchestrator-git-jsonl`'s `commands/needs_attention.py` product-imports `livespec_runtime.needs_attention.compose_needs_attention`, and BOTH orchestrators' `commands/needs_attention.py` product-import `livespec_runtime.hygiene_scan.scan_hygiene`. Neither is declared. The key is TIGHTENING-ONLY — every entry ADDS a name to the Result-return rule's scope — so this is not a gate that is currently failing; it is a gate that is currently blind to two names. Declaring them is an implementation edit to `pyproject.toml` with real consequences (it arms the Result-return rule over two functions whose return types are DELIBERATELY held non-`IOResult` for cross-repo reasons, as both docstrings state), so it is filed as a spec→impl commitment below rather than smuggled into a documentation pass, and the authoritative re-measurement is dev-tooling's central fleet run rather than this host's sibling checkouts.
