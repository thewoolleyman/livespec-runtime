# 003 — Work list: rewriting the `github_auth` / `work_items` scenarios (livespec-runtime-bda)

Authored 2026-09-07 by the independent read-only ratification reviewer that BLOCKED
`scenarios-github-auth-and-work-items` (auto-spawn, model opus), at the drive session's
request, after its report truncated three times in the message channel. Preserved here
verbatim because it is the work list for the rewrite and the scratchpad it was written to
is session-scoped. Every claim in it was spot-checked against the tree by the drive
session before the proposal was left un-ratified; see the blocker comment on
`livespec-runtime-bda` for that verification and the summary.

Standing on it: 9 defective scenarios of 32 — 2 fixable immediately, 7 gated on
`livespec-runtime-zvj` correcting the contract first. The reviewer's ordering call
(land `zvj` alone, do not bundle) was adopted and authorized by the maintainer.

---

# Work list — `scenarios-github-auth-and-work-items`

Independent ratification review, self-contained record.

- **Proposal:** `/home/ubuntu/.worktrees/livespec-runtime/spec/drain-2-batch-1/SPECIFICATION/proposed_changes/scenarios-github-auth-and-work-items.md`
- **Verdict:** BLOCKERS — do not ratify these bytes.
- **content_digest:** `ebfb71d7e052604cfb063c9f42183c21fd04c93e2b43d9212d9ceb4d76a1b582`
- **reviewed_at:** `2026-09-07T12:11:04Z`
- **Tally:** 32 scenarios reviewed — **23 sound, 9 defective.** (Corrected once, from an
  initial 26/6: B2 touches seven scenarios, not three.) No tenth defect surfaced while
  writing this file; see §"Anything not yet reported".

Gating test applied throughout: *would the corrected line make `scenarios.md` contradict
`contracts.md` as currently ratified?* For all seven B2 items the answer is yes —
contracts.md still declares `-> GithubAppConfig`, `-> bytes`, `-> str` and "MUST raise" —
so railway-accurate scenarios cannot land before `livespec-runtime-zvj` without trading a
falsehood for a contradiction.

**2 fixable in the proposal alone (items 1 and 9). 7 gated on `livespec-runtime-zvj`
(items 2–8).**

---

## Item 1 — FIXABLE NOW

**Heading**

`## Scenario: record identity is a stable sha256 over the canonical serialization`

**Wrong line, verbatim**

```
And changing only the supersedes pointer does not change the value
```

**Why it is wrong**

`work_item_record_identity` canonicalizes via `_work_item_to_dict`, which is
`asdict(item)` — every dataclass field, `supersedes` included
(`livespec_runtime/work_items/reduce.py`, `_work_item_to_dict` / `_record_identity`).
The row's own cited test,
`tests/livespec_runtime/work_items/test_reduce.py:128-138`
(`test_record_identity_is_independent_of_supersedes_pointer_only`), carries the comment
"supersedes is part of the canonical serialization, so a record that supersedes another
has a DIFFERENT identity from the original even if all other fields match (the pointer is
content)" and asserts `!=`. The test's NAME is what produced this defect; its assertion is
the contrary.

**Replacement line, verbatim** (or simply delete the line)

```
And a record that supersedes another has a different identity from the record it amends, because the supersedes pointer is part of the canonical serialization
```

**Gating:** none. Consistent with the current contract bullet ("over the record's canonical
serialization; the value a superseding record carries in `supersedes`").

**Side chore, not a spec matter:** rename
`test_record_identity_is_independent_of_supersedes_pointer_only` to say what it asserts.

---

## Item 2 — GATED on `livespec-runtime-zvj`

**Heading**

`## Scenario: load the App config from the tenant's credential-wrapper environment`

**Wrong lines, verbatim**

```
Then the return value is a GithubAppConfig with app_id "12345" and that private_key_pem
And api_url is DEFAULT_API_URL, "https://api.github.com"
And installation_id is None
```

**Why it is wrong**

`load_github_app_config(*, environ) -> Result[GithubAppConfig, GithubAppAuthError]`
(`livespec_runtime/github_auth/config.py`). The return value is `Success(GithubAppConfig(...))`,
not a `GithubAppConfig`.

**Replacement lines, verbatim**

```
Then the result is a Success carrying a GithubAppConfig with app_id "12345" and that private_key_pem
And that config's api_url is DEFAULT_API_URL, "https://api.github.com"
And its installation_id is None
```

---

## Item 3 — GATED on `livespec-runtime-zvj`

**Heading**

`## Scenario: App config resolution fails closed naming every missing variable`

**Wrong line, verbatim**

```
Then GithubAppAuthError is raised
```

**Why it is wrong**

Nothing is raised. `load_github_app_config` returns `Failure(GithubAppAuthError(...))`. The
cited test asserts `assert not is_successful(result)` then reads `result.failure().detail`
(`tests/livespec_runtime/github_auth/test_config.py:88-95`).

**Replacement line, verbatim**

```
Then the result is a Failure carrying GithubAppAuthError
```

**Also re-anchor the following three Ands** from "its detail" to "the error's detail". Their
substance is correct as written and needs no other change: the real detail names both
variables, points at the tenant's `credential_wrapper`, and there is no fleet fallback.

---

## Item 4 — GATED on `livespec-runtime-zvj`

**Heading**

`## Scenario: RS256 signing with openssl round-trips against openssl verify`

**Wrong line, verbatim**

```
Then the returned bytes are a signature that openssl verifies against the key's public half over that signing input
```

**Why it is wrong**

`sign_rs256_with_openssl(*, signing_input, pem) -> IOResult[bytes, GithubAppAuthError]`
(`livespec_runtime/github_auth/signing.py`). The success value is `IOSuccess(bytes)`.

**Replacement line, verbatim**

```
Then the result is an IOSuccess carrying bytes that openssl verify accepts against the key's public half over that signing input
```

---

## Item 5 — GATED on `livespec-runtime-zvj`

**Heading**

`## Scenario: an unloadable private key is an expected misconfiguration surfaced as GithubAppAuthError`

**Wrong lines, verbatim**

```
Then GithubAppAuthError is raised with an actionable detail naming the key as unloadable
And no other exception type escapes
```

**Why it is wrong — three separate errors in two lines**

1. Nothing is raised: the function returns `IOFailure(GithubAppAuthError(...))`. Its own
   docstring says the error is "now carried on the failure track rather than raised".
2. "no OTHER exception type escapes" understates it — *nothing* escapes now.
3. "naming the key as unloadable" does not match the actual detail, which reads
   "openssl could not sign with the App private key (exit N); verify GITHUB_PRIVATE_KEY
   holds the App's PEM private key as injected by the tenant's credential_wrapper". The
   cited test asserts `"GITHUB_PRIVATE_KEY" in failure.detail`
   (`tests/livespec_runtime/github_auth/test_mint_railway.py:45-65`).

**Replacement lines, verbatim**

```
Then the result is an IOFailure carrying GithubAppAuthError whose detail names GITHUB_PRIVATE_KEY and the tenant's credential_wrapper
And no exception escapes at all
```

---

## Item 6 — GATED on `livespec-runtime-zvj`

**Heading**

`## Scenario: minting with a pinned installation performs no discovery`

**Wrong line, verbatim**

```
Then the returned value is that token
```

**Why it is wrong**

`mint_installation_token(*, config, issued_at, seams) -> IOResult[str, GithubAppAuthError]`
(`livespec_runtime/github_auth/mint.py`). The success value is `IOSuccess(token)`.

**Replacement line, verbatim**

```
Then the result is an IOSuccess carrying that token
```

**Keep unchanged:** `And the seams' http_get was never called` — correct
(`resolve_installation_id` returns early on a non-empty pin).

---

## Item 7 — GATED on `livespec-runtime-zvj`

**Heading**

`## Scenario: minting discovers the sole installation when none is pinned`

**Wrong line, verbatim**

```
And the returned value is the minted token
```

**Replacement line, verbatim**

```
And the result is an IOSuccess carrying the minted token
```

**Keep unchanged:** `Then the seams' http_post targets /app/installations/777/access_tokens`
— correct.

---

## Item 8 — GATED on `livespec-runtime-zvj`

**Heading**

`## Scenario: minting with several installations and no pin fails closed directing the operator to pin one`

**Wrong line, verbatim**

```
Then GithubAppAuthError is raised
```

**Why it is wrong**

Returns `IOFailure(GithubAppAuthError(...))`. The cited test reads the detail off the
failure track (`tests/livespec_runtime/github_auth/test_mint.py:156-161`).

**Replacement line, verbatim**

```
Then the result is an IOFailure carrying GithubAppAuthError
```

**Keep unchanged:** both following Ands are true — the real detail is "the App has 2
installations; set GITHUB_APP_INSTALLATION_ID to pin the one to mint for", and no access
token is requested.

---

## Item 9 — FIXABLE NOW

**Heading**

`## Scenario: the App JWT signing input is an RS256 header.payload with caller-injected time`

**Wrong line, verbatim**

```
And the decoded claims carry iss "12345" and an exp whose distance from iat is under GitHub's 600-second App-JWT cap
```

**Why it is wrong**

`_JWT_SKEW_SECONDS = 60`, `_JWT_TTL_SECONDS = 540`, so `iat = issued_at - 60` and
`exp = issued_at + 540`. `exp - iat = 600` **exactly** — at the cap, not under it. A
consumer-tier test written as `assert exp - iat < 600` fails.

**Replacement line, verbatim**

```
And the decoded claims carry iss "12345", an iat backdated 60 seconds for clock skew, and an exp 540 seconds past the injected issued_at — under GitHub's 10-minute App-JWT cap
```

**Gating:** none. contracts.md §signing says only "The JWT lifetime MUST stay under GitHub's
10-minute App-JWT cap", which the 540-from-issuance framing satisfies. This is also the
module docstring's own framing.

---

## Fixes outside the 9 — all fixable now

- **The census sentence.** 43 documented public names, 42 absent from today's
  `scenarios.md`, not 37/36. Measured with the inventory test's own method (`__all__` per
  module, `# @generated` port excluded, whole-word match): 17 `github_auth` (config 3,
  credential_helper 2, errors 1, mint 5, provider 2, signing 4) + 26 `work_items`
  (lifecycle 6, rank 3, reduce 4, store 1, types 12). The single hit in today's file is
  `main`, which is the prose over-credit the inventory test's own HONEST LIMIT paragraph
  warns about.
- **Two uncovered names.** `FactorySafety` (`types.py:42`) and `ReviewRequirement`
  (`types.py:45`) belong in the `work_items` `Literal`-aliases bullet of the exemption
  record. After the proposal, 41 of 43 are covered; these two are in neither bucket, so the
  closing completeness claim is false and gap-vjxowbbp's acceptance criterion is unmet for
  them.
- **Direction word.** The exemption record says "exercised … inside the scenarios
  **above**" but sits above all 50 scenarios. Should read "below".
- **`credential_helper.run`'s justification.** "not unit-observable" is wrong — it is
  trivially monkeypatchable via `sys.argv` / `os.environ`. The exemption itself stands on
  "no behavior of its own beyond wiring", which is true. Fix the reason, keep the
  exemption.
- **Relocate the exemption record** out of `scenarios.md` into `spec.md` §"Public surface"
  — already this repo's venue for consciously-excluded public surface (the section
  `tests/public-surface-debt.json` names as its authority). Clears the template-compliance
  violation in the same pass.

---

## Ordering call

**I would ratify `zvj` first, then the scenarios rewritten railway-accurately on the
corrected contract. I would not ratify the bundle.**

The bundling argument dissolves on inspection. Its whole appeal is avoiding a window in
which `scenarios.md` and `contracts.md` disagree — but there is no such window, because the
scenarios never entered the spec. They are pending in `proposed_changes/` and staying
there. During the gap `scenarios.md` simply says nothing about the railway, and silence is
not disagreement. The only way to manufacture the transient contradiction is to ratify the
scenarios before `zvj`, which is exactly what is not happening.

Bundling would therefore buy nothing, and would cost the independent review that a change
to what consumers catch deserves: `livespec-orchestrator-beads-fabro` catches
`GithubAppAuthError` at two call sites per `provider.py`'s docstring. That is a change
reviewers should see on its own merits, not as a rider on 32 scenarios. Filing `zvj`
naming **the code as authority** is the right call and closes the actual hazard, which was
someone reading contracts.md and "fixing" three working functions to match stale prose.

Keep the proposal pending rather than withdrawing it: 23 of 32 scenarios are sound, the
exemption record is sound modulo two names, and the 32 heading-coverage rows are exactly
right — 32 rows against 32 new headings, no duplicates, no orphans either direction, and
every cited unit-tier node id resolves to a real test function on disk. Fix items 1 and 9
and the five census/exemption items now, so the only open blocker is the wording `zvj`
settles, and the re-file becomes a mechanical pass over seven Thens.

### Scope note for `zvj`

Three bullets are false, one is merely terse, and two that look suspicious are correct.

- `load_github_app_config(...) -> GithubAppConfig` + "raises" → `-> Result[GithubAppConfig,
  GithubAppAuthError]`, returns `Failure`.
- `sign_rs256_with_openssl(...) -> bytes` + "MUST raise" → `-> IOResult[bytes,
  GithubAppAuthError]`.
- `mint_installation_token(...) -> str` + "Every EXPECTED failure raises" → `-> IOResult[str,
  GithubAppAuthError]`. The second half, "caller bugs propagate as built-ins", stays true.
- **Terse but not false:** the `SignRs256` / `HttpJson` seam-shape bullet gives no return
  types; both are `IOResult`. Worth stating for completeness.
- **Leave alone — the asymmetry is deliberate.** `InstallationTokenProvider.token() -> str`
  genuinely raises: it re-raises the exact error rather than `unwrap()`ing it, because the
  boundary consumers catch must not change. `credential_helper.main(...) -> int` catches
  `GithubAppAuthError` and returns exit 1. A blanket "everything is railway now" correction
  would introduce a fresh falsehood at both.
- **Do not promote non-surface names.** `mint.py`'s `__all__` comment records that
  `resolve_installation_id`, `http_get_json` and `http_post_json` stay module-level and
  importable but are deliberately NOT declared surface.

---

## Non-blocking observations — complete list

**These two change what a test author would write, not just the prose.**

1. **Sibling-dependency scenario has an unstated Given.**
   `## Scenario: an unresolved sibling_work_item dependency fails closed while a missing local id does not block`
   — its leg `And when the lookup returns RefStatus.CLOSED the result is True` depends on a
   Given it never states. `_resolve_sibling_work_item`
   (`livespec_runtime/cross_repo/resolve.py:94-105`) returns `UNKNOWN` when
   `repo not in manifest.targets`, **before** `sibling_status_lookup` is consulted. With a
   manifest that does not declare the sibling repo, the CLOSED leg yields `False`, not
   `True`. Add a Given that the manifest declares the sibling repo, or a test author will
   write a test that passes for the wrong reason.
2. **`WorkItemStore` is not `@runtime_checkable`.**
   `## Scenario: a store facade satisfies WorkItemStore structurally and round-trips append then read`
   — "checked against the WorkItemStore protocol" must mean static assignability (what
   `tests/livespec_runtime/work_items/test_store.py` does with
   `store: WorkItemStore = _InMemoryStore()`), never `isinstance`, which raises
   `TypeError`. Say so in the scenario text before the consumer-tier test is written.

**Prose and precision.**

3. **`normalize_pem` "byte-identical to the input"** holds only for a PEM ending in exactly
   one newline: the impl does `raw.replace("\\n","\n").strip()` then returns `text + "\n"`,
   so a well-formed PEM *without* a trailing newline gains one. Separately, the
   literal-backslash-`n` input takes the early `if "\n" in text` return and is never
   re-wrapped, so "64-column body lines" is guaranteed only for the whitespace-collapsed
   single-line case. contracts.md carries the same loose wording, so this is inherited, not
   introduced by the proposal.
4. **Legacy-defaults scenario lists 8 of the 10 optional-on-read fields.**
   `spec_commitment_hint` is omitted (`awaits_scope_override` is covered separately as
   `False`). Nothing false, just incomplete.
5. **The co-edit's atomicity rests on prose alone.** If `scenarios.md` lands without the 32
   JSON rows, `heading_coverage` fails on 32 headings at once. Carrying it as a spec
   commitment rather than in `resulting_files` is nonetheless correct — `resulting_files[]`
   paths are spec-target-relative (`"scenarios.md"`) and `tests/` sits outside
   `SPECIFICATION/`, so no atomic form is available.
6. **Template compliance.** The rule is a doctor-llm *subjective* judgment, not a mechanical
   gate: "`scenarios.md` content is Gherkin scenarios with the blank-line-delimited format;
   does NOT contain prose paragraphs outside scenario blocks"
   (`specification-templates/livespec/prompts/doctor-llm-subjective-checks.md:82-83`).
   Plainly: the inserted exemption record violates the literal rule. The file's existing
   intro is a header; a 16-line normative exemption register is not. Relocation (above)
   resolves it.

**Surfaced while writing this file — new since my earlier messages.**

7. **The credential-helper `get` scenario omits the seam injection.**
   `## Scenario: the credential helper answers an https get with x-access-token and a freshly minted token`
   gives `argv ["get"]`, an environ carrying the App secrets, and stdin — but never states
   that `MintSeams` are injected. `main`'s `seams` parameter defaults to
   `DEFAULT_MINT_SEAMS`, so a consumer-tier test written literally from this Given would
   attempt a real openssl sign and a real network mint and fail. Same class as
   observation 1, opposite failure mode: that one passes for the wrong reason, this one
   cannot pass at all. Add the injected seams to the Given.
8. **`materialize` tie-break Given is loose.**
   `## Scenario: materialize picks one head per id and is the identity collection for a one-record-per-id substrate`
   says the winner is "the head with the greatest captured_at". The impl takes `heads[-1]`
   from a sort on `(captured_at, identity)`, so with equal `captured_at` the greatest
   identity wins. Either give C and D distinct `captured_at` in the Given, or name the full
   `(captured_at, identity)` tie-break as the sibling `reduce` scenario already does.

---

## Anything not yet reported

**The count stays at 9.** I re-walked all 32 scenarios a second time while writing this
file, including every one I had passed quickly on the first pass: `random_id_suffix`'s
six-character base32 window (4 bytes → 7 significant chars, so the first 6 never touch
padding), `reduce`'s divergent-heads case with and without the ancestor present in the
stream, `materialize`'s `heads[-1]` tie-break, all three `lane_of` scenarios, both
`is_item_ready` scenarios, `ready_sort_key` (literally `attrgetter("rank", "id")`), all
three `rank` scenarios, both credential-helper no-op and no-credential paths, both provider
caching scenarios, `b64url`, and the legacy-defaults scenario against the 15 required /
10 optional field split.

Two things surfaced during that second pass, recorded as observations 7 and 8 above. Both
are test-authoring hazards, not false assertions — neither states something the code
contradicts — so neither becomes a tenth defect. Observation 7 is the more consequential of
the pair and I would fix it in the same pass as items 1 and 9.

The census in §"Fixes outside the 9" was computed mechanically over `__all__` rather than by
reading, so it is exhaustive by construction: `FactorySafety` and `ReviewRequirement` are
the only two names left uncovered, and there is no third.

One scenario deserves explicit mention as the model for the B2 rewrite:
`## Scenario: the optional installation pin and API-root override are carried into the config`
survives untouched, because it says "the `GithubAppConfig` carries …" rather than claiming
the *return value* is the config. That phrasing is what items 2, 4, 6 and 7 should imitate.
