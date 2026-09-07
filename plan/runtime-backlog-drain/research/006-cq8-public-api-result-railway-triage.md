# 006 — `public_api_result_typed` triage for `livespec-runtime-cq8`

Prepared 2026-09-07 by the factory implement stage for
`livespec-runtime-cq8` ("Adopt the public-API Result railway so the
`pure_trees` un-gating can re-land"), parent epic `livespec-dev-tooling-idlx`
in the dev-tooling tenant.

This file IS the disposition record the item's first acceptance criterion asks
for. The drive session copies §3 into the ledger comment on
`livespec-runtime-cq8` and §6 into a comment on `livespec-dev-tooling-idlx`.

## 1. The probe, re-derived rather than trusted

The item's FINDING comment (2026-09-06T18:10Z) supplies a recipe that needs a
`livespec-dev-tooling` checkout carrying `46c5daba`. A fabro sandbox has no
sibling checkout and installs dev-tooling from this repo's gated pin, so the
recipe as written cannot run here. The un-gating was reproduced instead by
calling the INSTALLED check's own `_scan` with the `pure_trees` role-absence
gate stepped over — no fork, no edit, no weakened copy:

```python
from livespec_dev_tooling.checks import public_api_result_typed as chk
from livespec_dev_tooling.config import load_config, resolve_check_universe

config = load_config(repo_root=Path.cwd())
root, universe = resolve_check_universe()
sources = {rel: (root / rel).read_text(encoding="utf-8") for rel in universe}
offenders = chk._scan(
    cwd=Path.cwd(),
    pure_trees=(Path("livespec_runtime"),),   # what 46c5daba stops gating away
    config=config,
    sources=sources,
)
```

`pure_trees=("livespec_runtime",)` is the same universe `role_trees()` would
yield were the key armed, so this measures the post-46c5daba behaviour of the
check as PINNED here, not of a reconstructed older one.

**It reproduced the FINDING comment's 16-function set exactly**, at
`1c211eb` + this branch's base, against dev-tooling `1.53.6`. That is a
stronger corroboration than the recipe would have given: the same set falls out
of a checker two minor versions newer than the one the FINDING measured, so the
set is a property of THIS TREE and not of a particular dev-tooling build.

Fail-capability is proven by the same run in the other direction: the GATED
entry point (`just check-public-api-result-typed`) exits 0 on this tree emitting
"role key declared NOT APPLICABLE", while the un-gated `_scan` exits 1 with 16
offenders.

## 2. What actually convicts each function

Every disposition below rests on the check's own machinery, not on reading the
source and guessing. Two facts were computed per function — the local clause
(a)/(b)/(c)/(e) verdict from `_no_expected_failure_mode._local_analysis`, and
the SHORTEST clause-(d) propagation path to a locally-disqualified callee:

| function | convicted by |
|---|---|
| `extract_rate_limit_headers` | (d) via `_headers_named` |
| `extract_conditional_headers` | (d) via `_headers_named` |
| `_headers_named` (private, not itself flagged) | unresolvable callee — it calls its injected `wanted` predicate PARAMETER |
| `gh_transport` | I/O call (the nested `transport` closure reaches `record_budget_signal`) |
| `int_option` | clause (a) — one `raise` |
| `manifest_rows` | I/O call — `importlib.resources` read |
| `verify_default_block` | (d) via `documented_defaults` → `_comment_block` (the `UnterminatedGovernanceBlockError` raise) |
| `parse_cross_repo_manifest` | (d) via `_parse_cross_repo_target` (the `CrossRepoSchemaError` raise) |
| `lane_of` | (d) via `_has_open_dependency` → `_entry_blocks` |
| `is_item_ready` | (d) via `lane_of` |
| `resolve_ref` | I/O call — the `gh` provider |
| `scan_hygiene` | (d) via `stale_branch_findings` → `hygiene_scan_context.git` |
| `detect_stale_worktrees` | (d) via `hygiene_scan_context.worktrees` → `git` |
| `snapshot_from_headers` | clause (e) — `X | None` |
| `hygiene_scan_cli.main`, `credential_helper.main` | I/O call — stream writes and the scan / mint they drive |
| `hygiene_scan_cli.run`, `credential_helper.run` | (d) via the module's own `main` |

## 3. The dispositions — all 16

⚠️ **THE ITEM'S THREE-LETTER TAXONOMY HAS NO CELL FOR FOUR OF THESE, and that
is a finding rather than a bookkeeping nuisance.** Acceptance criterion 1 offers
(a) "put on the railway", (b) "declared supervisor", (c) "checker flags
wrongly". Acceptance criterion 4 then REQUIRES that `scan_hygiene` and
`detect_stale_worktrees` keep their current return types — a genuine
expected-failure surface that is neither converted nor a false positive. (a) is
excluded for them by criterion 2 (it means "converted"), (b) is plainly wrong,
and (c) would file them upstream as CHECKER DEFECTS, which they are not and
which would mislead `livespec-dev-tooling-idlx`. A fourth letter is used:

- **(d) HELD** — a genuine expected-failure path whose conversion is owed but is
  a COORDINATED MULTI-REPO change this repo cannot land alone.

Every function still carries exactly one letter.

### (a) GENUINE — converted onto the railway here: **NONE**

**This is the item's headline result and it is a measured claim, not a
shortfall.** Every one of the 16 is either already correct, a config gap, or
gated behind a sibling repo. §5 states the search that produced it.

### (b) CONFIG GAP — outermost supervisor entry point (3)

| # | function | disposition |
|---|---|---|
| 1 | `livespec_runtime/hygiene_scan_cli.py:27` `main` | **(b)** — the `livespec-hygiene-scan` console script's tested core, whose `int` IS the process exit code (0 / 2 on usage error); declared in `supervisor_entry_files` by this changeset. **CLEARED.** |
| 2 | `livespec_runtime/hygiene_scan_cli.py:64` `run` | **(b)** — the process entry that wires the real streams, i.e. the OUTERMOST supervisor of the same file, but `_is_exempt_supervisor` scopes livespec v177 member 4 to the NAMES `main` and `build_parser`, so declaring the file cannot reach it. **STILL FLAGGED; upstream finding §6.1.** |
| 3 | `livespec_runtime/github_auth/credential_helper.py:92` `run` | **(b)** — identical shape (`livespec-github-credential-helper` console script, `raise SystemExit(run())`), identical name-scoping bar. **STILL FLAGGED; upstream finding §6.1.** |

⛔ `credential_helper.py` was deliberately NOT added to `supervisor_entry_files`.
Its `main` is not in the flagged set, so the declaration would clear nothing,
while four other checks (`no_except_outside_io`, `no_write_direct`,
`supervisor_discipline`, `partition_completeness`) read that same key — the
declaration would RELAX three gates the file currently satisfies unaided, buying
nothing. A widening for no gain is not adoption.

### (c) NOT A VIOLATION — the checker over-applies (9)

| # | function | disposition |
|---|---|---|
| 4 | `github_budget_measurement.py:79` `snapshot_from_headers` | **(c)** — a total read of headers the caller already holds whose `None` means "this response reported no budget", which its own docstring separates from a MEASURED zero; declared in `total_absence_returns` (livespec v179 member 2) by this changeset. **CLEARED.** |
| 5 | `github_budget_measurement.py:98` `extract_rate_limit_headers` | **(c)** — pure and total over a string the caller holds; disqualified only by clause-(d) propagation from `_headers_named`, whose sole disqualifier is calling its injected PURE predicate parameter. |
| 6 | `github_budget_measurement.py:103` `extract_conditional_headers` | **(c)** — same function, same chain, same reason. |
| 7 | `github_budget_measurement.py:290` `gh_transport` | **(c)** — a total FACTORY that builds a closure and cannot itself fail; the I/O belongs to the returned transport at ITS call time, so a `Result` here would carry an uninhabited failure track. |
| 8 | `github_budget_client_support.py:101` `int_option` | **(c)** — pure over an ALREADY-PARSED options mapping; its one `raise` is the `MisshapedGithubBudgetOptionError` CALLER-BUG guard ratified alongside `mapping_option` (`livespec-runtime-8zu`), and the fleet rule is that bugs raise while `Result` carries EXPECTED failures. |
| 9 | `spec_governance.py:73` `manifest_rows` | **(c)** — its read is `importlib.resources.files("livespec_runtime")`, this package's OWN data shipped inside the wheel; absence or malformed JSON is a corrupt installation, i.e. a bug, not an expected environment failure. (Independently also barred by §4's cross-repo hold.) |
| 10 | `work_items/lifecycle.py:88` `lane_of` | **(c)** — a total classifier over the in-memory `index` the caller holds; every resolution failure beneath it is already absorbed into a fail-closed boolean by `_entry_blocks`, so nothing expected escapes. |
| 11 | `work_items/lifecycle.py:126` `is_item_ready` | **(c)** — literally `lane_of(...).name == "ready"`, so it inherits row 10's reason exactly. |
| 12 | `cross_repo/resolve.py:57` `resolve_ref` | **(c)** — its expected failure modes are ALREADY inhabited as `RefStatus.UNKNOWN`; ratified `contracts.md` §"Retry policy" says callers "MUST translate an `IOFailure` into `RefStatus.UNKNOWN` at their own resolution boundary", so `UNKNOWN` IS the failure track and an `IOResult` would add a second, uninhabited one. |

Row 12 is a near-miss on livespec v183's sanctioned alternative spelling: it
would be declarable under `single_meaning_variants` but for
`_declarable_unions` limb (a), which reads ONLY the `A | B` alias spelling,
while `RefStatus` is a frozen dataclass carrying class-level constants. That
module's own docstring states the bound ("a consumer spelling its union another
way must re-spell it to declare it"), so this is a known strict end and not a
defect — but it is why a correctly-designed union gets no relief here. §6.2.

### (d) HELD — genuine, conversion owed, cross-repo coordinated (4)

| # | function | disposition |
|---|---|---|
| 13 | `hygiene_scan.py:52` `scan_hygiene` | **(d)** — ratified `contracts.md` marks it "⛔ THE RAILWAY TERMINATES HERE AND THE RETURN TYPE IS HELD ON PURPOSE"; both orchestrators call it from `commands/needs_attention.py`. `livespec-runtime-cgsjjm` owns arming it via `cross_repo_public_api`, sequenced behind dev-tooling's central fleet measurement. |
| 14 | `hygiene_scan_worktrees.py:65` `detect_stale_worktrees` | **(d)** — the same ⛔ clause, held for the same reason; `livespec`'s `dev-tooling/reap_stale_worktrees.py:249` consumes the signature directly. `livespec-runtime-cgsjjm` owns arming it. |
| 15 | `cross_repo/types.py:228` `parse_cross_repo_manifest` | **(d)** — genuinely raises `CrossRepoSchemaError` on malformed manifest input, the exact shape `parse_depends_on_entry` was converted for; but it is declared in `cross_repo_public_api` and all THREE consumers already wrap the raise in `@safe(exceptions=(CrossRepoSchemaError,))` shims, so converting here yields `Result[Result[...]]` in each. |
| 16 | `spec_governance.py:87` `verify_default_block` | **(d)** — genuine, and this repo's own `pyproject.toml` already records it as "convicted by that raise propagating through an unguarded call"; declared in `cross_repo_public_api`, called plainly by `livespec`'s `commands/spec_governance.py:171` and `dev-tooling/checks/spec_governance_template.py:169`. |

## 4. Why no `cross_repo_public_api` name was converted

`pyproject.toml` already ratifies the ORDER, in the comment above the key:

> The blast radius of ever converting one is the `livespec-dev-tooling-dx8l`
> shape exactly — dual-shape consumer wiring lands FIRST, in the consuming
> repo, and the signature change only after.

Measured against the sibling checkouts available in this sandbox, the consumer
half is landed for `parse_cross_repo_manifest` (all three members hold shims)
and NOT landed for `verify_default_block`, `manifest_rows`, `lane_of`,
`is_item_ready`. But "landed" here means `@safe`-wrapping the RAISE, so even
the ready case breaks on a producer-side conversion — the shim would double-wrap
into a nested `Result` whose `.alt()` fires on the wrong track. Converting any
of the five from this sandbox is a silent runtime break of two orchestrators,
`livespec`, and a dev-tooling check, with no way to land the coordinating PRs.

Adding a parallel `*_result` producer surface was considered and rejected: it
would not clear a single offender (the raising function stays flagged), it
duplicates shims three consumers already have, and it ships speculative public
surface into a repo whose inventory check exists to stop exactly that.

## 5. The search behind "(a) = NONE"

The claim is that no flagged function is BOTH a genuine expected-failure path
AND convertible without a sibling repo. Partitioning the 16 leaves no residue:

- 3 are process entry points whose `int` is an exit code (rows 1–3);
- 3 are pure and total over data the caller already holds, with no failure to
  flow (rows 5–7);
- 1 has a `raise`, but it guards a CALLER BUG, which the rule does not reach
  (row 8, `int_option`);
- 1 reads only its own in-wheel packaged data, whose absence is a corrupt
  install rather than an expected environment failure (row 9, `manifest_rows`);
- 2 are total classifiers whose sub-resolution failures are already absorbed
  fail-closed below them (rows 10–11);
- 1 already carries its failure as an inhabited, ratified non-success variant
  (row 12, `resolve_ref`);
- 1 has a legitimate-absence `None`, now declared (row 4);
- 4 are genuine and blocked on siblings (rows 13–16).

3 + 3 + 1 + 1 + 2 + 1 + 1 + 4 = 16. No residue.

The two that MOVED are the two whose remedy was a ratified DECLARATION rather
than a signature change, which is what "adoption" means for a repo in this
shape.

## 6. Findings owed to `livespec-dev-tooling-idlx`

### 6.1 Member 4's exemption is name-scoped and misses the fleet's own `run()` convention

`_is_exempt_supervisor` grants the supervisor exemption to `main() -> int` and
`build_parser() -> ArgumentParser`. This fleet's flat-layout convention is a
PAIR — `main(*, argv, environ, stdout, stderr, ...) -> int` as the tested core,
plus `run() -> int` wiring the real process streams and named in
`[project.scripts]`. `run` is the OUTER of the two, so the check exempts the
inner supervisor and convicts the outer one. Measured here: 2 of 16 (rows 2, 3),
and both are `[project.scripts]` console-script entry points.

This cannot be fixed consumer-side. Declaring the file changes nothing, and
renaming `run` to satisfy a name matcher would be detector evasion.

**Suggested remedy** (dev-tooling's call): admit a third name to member 4's
`_is_exempt_supervisor`, scoped to declared `supervisor_entry_files` exactly as
`main` already is — so it stays a per-file declaration a consumer must opt into,
not a bare name exempted everywhere.

### 6.2 Two `(c)` shapes the check flags that the ratified rule does not reach

1. **An injected pure-predicate parameter reads as doubt.** `_headers_named`
   takes `wanted: Callable[[str], bool]`, a PURE predicate, and calling it
   disqualifies the function under "an unresolvable callee ... doubt
   DISQUALIFIES" — then clause (d) propagates that to both public callers
   (rows 5, 6). `_no_expected_failure_mode`'s docstring already carves out the
   analogous case for I/O ("AN INJECTED SEAM IS NOT A BOUNDARY ... `run` is
   deliberately absent from the unresolved-receiver verb set"), but the
   callee-name limb has no matching carve-out. Cost measured here: 2 of 16.

2. **A closure factory is convicted for its closure's I/O.** `gh_transport`
   (row 7) is total — it builds and returns a function. `_clauses_a_and_b`
   and `calls_of` both walk nested `FunctionDef` bodies, so the returned
   transport's `record_budget_signal` write convicts the factory. Cost here:
   1 of 16.

Neither is a request to relax the rule. Both are cases where the rule's own
words ("a function with no expected failure mode has nothing to flow") and the
check's computation disagree.

### 6.3 The taxonomy gap

`livespec-runtime-cq8`'s acceptance criteria offer three outcomes and then
require a fourth (§3). Any sibling adoption item copying the same three-letter
frame will hit this the moment it meets a `cross_repo_public_api` name. The
fourth cell — genuine, conversion owed, blocked on a coordinated multi-repo
change — should be named in the epic so the four remaining adoption children do
not each invent their own spelling for it.

## 7. State after this changeset

The un-gated probe reports **14**, down from 16: `hygiene_scan_cli.main`
cleared by the `supervisor_entry_files` declaration, `snapshot_from_headers` by
the `total_absence_returns` declaration. All 14 residual are recorded above as
(b), (c) or (d); none is an unaccounted violation, and none was cleared by a
lever, an env var, a carve-out or a severity demotion.

⚠️ Both new declarations are UNVERIFIED LOCALLY until `pure_trees` is armed
here. `public_api_result_typed` runs `_report_bad_declarations` — the bound-1
and bound-3 staleness gates over `total_absence_returns` — AFTER the
`pure_trees` role-absence gate, a gate ORDER artifact the check's own docstring
states. The `snapshot_from_headers` entry was validated against
`_declared_absence_returns` by hand during this triage (bound 1: the annotation
is `GithubRateLimitSnapshot | None`; bound 3: it resolves to a top-level
function in that file) and will be verified mechanically the moment the
un-gating re-lands, which is the point of the epic.

`just check` is green at required coverage on this tree.
