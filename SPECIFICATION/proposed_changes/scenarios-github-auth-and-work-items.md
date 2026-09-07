---
topic: scenarios-github-auth-and-work-items
author: claude-opus-5
created_at: 2026-09-07T12:01:43Z
spec_commitments:
  impl_followups:
    - id_hint: consumer-tier-scenario-tests-github-auth-work-items
      description: |
        Write integration-tier tests under tests/consumer/ (node-id prefix tests.consumer per pyproject scenario_tiers) that drive the 32 new github_auth and work_items scenarios as a consumer would, then replace the TODO in each new tests/heading-coverage.json row with the test's node id. Until it lands the rows stay TODO with their acknowledged-tier reason, which the heading_coverage check permits during transition.
    - id_hint: scenarios-github-auth-and-work-items-carrier-close
      description: |
        livespec-runtime-bda (already filed, gap-id:gap-vjxowbbp) is this proposal's carrier and closes on ratification, with the heading-coverage co-edit landed in the same changeset so just check stays green; verify by re-running detect-impl-gaps and confirming gap-vjxowbbp is no longer returned.
---

## Proposal: scenarios-github-auth-and-work-items

### Target specification files

- SPECIFICATION/scenarios.md
- SPECIFICATION/spec.md

### Summary

Add 32 Gherkin scenarios to scenarios.md covering the consumer-observable behaviour of the ratified github_auth and work_items public surfaces, record the conscious exemptions for the remaining data carriers, constants, seams and type aliases in spec.md §"Public surface", and co-edit tests/heading-coverage.json with acknowledged-TODO rows. Closes the scenario half of gap-vjxowbbp: 42 of the two families' 43 documented public names appeared nowhere in scenarios.md.

### Motivation

gap-vjxowbbp ("New public symbols (github_auth / work_items) lack scenarios.md entries") was carried by livespec-runtime-vbofkr, absorbed into livespec-runtime-mqsxsu.4, and its scenario half was consciously deferred in plan runtime-backlog-drain research/005 §5b on the reasoning that scenarios ride the propose-change that ratifies a family. That venue has since occurred twice, v020 and v021, and scenarios.md was untouched both times; git log on it stops at v019. vbofkr, mqsxsu.4 and x87 are closed, so nothing carried the gap id until livespec-runtime-bda was filed on 2026-09-07 as its carrier, and this proposal is that item's payload. Measured with the same whole-word method the public-surface inventory test uses — `__all__` per module across both families, the `# @generated` `_fractional_indexing` port excluded as that test's own register excludes it: 43 documented public names, 42 absent from scenarios.md (the single hit is `main`, which is a prose over-credit of exactly the kind that test's HONEST LIMIT paragraph warns about), against a file that DOES name cross_repo symbols verbatim (resolve_ref 9 hits, RefStatus 10), so the hole is real and not stylistic. scenarios.md's own header says a new public symbol SHOULD land with at least one scenario. The integration-tier constraint on coverage rows is acknowledged rather than dodged: consumer-tier tests for these families do not exist yet, and writing them is declared as this proposal's impl follow-up.

### Proposed Changes

`SPECIFICATION/scenarios.md` MUST gain the following 32 scenarios, appended after the existing ones, verbatim. Each states consumer-observable behaviour already ratified in `contracts.md` §"Module-level public surface" for the `github_auth` and `work_items` families; no clause changes.

SEQUENCING. Two of the scenarios below describe behaviour whose ratified prose was corrected after this proposal was first authored, and this proposal MUST be revised only after both corrections are on master, or it will contradict `contracts.md` instead of restating it. The seven `github_auth` railway assertions depend on v023 (`github-auth-railway-signatures`, ratified 2026-09-07), which is already landed. The `ready_sort_key` scenario depends on `ready-sort-key-aging-signature`, filed alongside this proposal: `livespec_runtime/work_items/lifecycle.py` gained the aging-aware factory in commit `b678542` without a matching `contracts.md` edit, so the ratified bullet still declares the retired `ready_sort_key(item: WorkItem)` shape. Because `revise` processes pending proposals in creation-time order and this proposal is the older of the two, the correction MUST be ratified with `--only-topic ready-sort-key-aging-signature` first.

## Scenario: load the App config from the tenant's credential-wrapper environment

Given an environment mapping with GITHUB_APP_ID "12345" and GITHUB_PRIVATE_KEY set to a PEM
And no GITHUB_APP_INSTALLATION_ID and no GITHUB_API_URL
When load_github_app_config is invoked with that environ
Then the result is a Success carrying a GithubAppConfig with app_id "12345" and that private_key_pem
And that config's api_url is DEFAULT_API_URL, "https://api.github.com"
And its installation_id is None

## Scenario: App config resolution fails closed naming every missing variable

Given an environment mapping where GITHUB_APP_ID is the empty string and GITHUB_PRIVATE_KEY is absent
When load_github_app_config is invoked with that environ
Then the result is a Failure carrying GithubAppAuthError
And the error's detail names BOTH GITHUB_APP_ID and GITHUB_PRIVATE_KEY as missing
And the error's detail points the operator at the consuming tenant's credential_wrapper
And no fleet credential is consulted as a fallback

## Scenario: the optional installation pin and API-root override are carried into the config

Given an environment mapping with both required secrets, GITHUB_APP_INSTALLATION_ID "777" and GITHUB_API_URL "https://ghe.example/api/v3"
When load_github_app_config is invoked with that environ
Then the GithubAppConfig carries installation_id "777" and api_url "https://ghe.example/api/v3"

## Scenario: b64url encodes with the URL-safe alphabet and no padding

Given raw bytes whose standard base64 form contains "+", "/" and trailing "="
When b64url is invoked with those bytes
Then the result uses only the URL-safe alphabet
And the result carries no "=" padding

## Scenario: the App JWT signing input is an RS256 header.payload with caller-injected time

Given app_id "12345" and issued_at 1_700_000_000
When jwt_signing_input is invoked with them
Then the result is two b64url segments joined by "."
And the decoded header declares alg "RS256"
And the decoded claims carry iss "12345", an iat backdated 60 seconds for clock skew, and an exp 540 seconds past the injected issued_at — under GitHub's 10-minute App-JWT cap

## Scenario: normalize_pem re-wraps a flattened key and passes a well-formed PEM through unchanged

Given a private key flattened to one line by a secrets manager, with its newlines collapsed to whitespace
When normalize_pem is invoked with it
Then the result has the BEGIN and END armor lines and 64-column body lines of a real PEM
And when the flattening instead wrote the newlines as literal backslash-n, those are restored to real newlines and the key's existing line structure is preserved rather than re-wrapped
And when normalize_pem is invoked with an already well-formed PEM ending in exactly one newline the result is byte-identical to the input

## Scenario: RS256 signing with openssl round-trips against openssl verify

Given a well-formed RSA private key PEM and a signing input
When sign_rs256_with_openssl is invoked with them
Then the result is an IOSuccess carrying bytes that openssl verify accepts against the key's public half over that signing input

## Scenario: an unloadable private key is an expected misconfiguration surfaced as GithubAppAuthError

Given a private_key_pem that openssl cannot load
When sign_rs256_with_openssl is invoked with it
Then the result is an IOFailure carrying GithubAppAuthError whose detail names GITHUB_PRIVATE_KEY and the tenant's credential_wrapper
And no exception escapes at all

## Scenario: minting with a pinned installation performs no discovery

Given a GithubAppConfig whose installation_id is "777"
And MintSeams whose http_post answers POST /app/installations/777/access_tokens with a token
When mint_installation_token is invoked with that config and an issued_at
Then the result is an IOSuccess carrying that token
And the seams' http_get was never called

## Scenario: minting discovers the sole installation when none is pinned

Given a GithubAppConfig whose installation_id is None
And MintSeams whose http_get answers GET /app/installations with exactly one installation, id 777
When mint_installation_token is invoked with that config
Then the seams' http_post targets /app/installations/777/access_tokens
And the result is an IOSuccess carrying the minted token

## Scenario: minting with several installations and no pin fails closed directing the operator to pin one

Given a GithubAppConfig whose installation_id is None
And MintSeams whose http_get answers GET /app/installations with two installations
When mint_installation_token is invoked with that config
Then the result is an IOFailure carrying GithubAppAuthError
And the error's detail directs the operator to set GITHUB_APP_INSTALLATION_ID
And no access token is requested

## Scenario: the provider mints on first use and caches in process memory only

Given an InstallationTokenProvider over a config, MintSeams that count mints, and an injectable clock
When token() is called for the first time
Then exactly one mint occurs and its token is returned
And when token() is called again within the refresh horizon the same token is returned with no further mint
And the token is never written to disk or any store

## Scenario: the provider re-mints transparently once the 55-minute refresh horizon passes

Given an InstallationTokenProvider whose clock is advanced past TOKEN_REFRESH_SECONDS, 3300 seconds, after the first mint
When token() is called
Then a fresh mint occurs before the roughly 60-minute installation-token expiry
And the caller receives the new token without handling expiry itself
And TOKEN_REFRESH_SECONDS is 3300

## Scenario: the credential helper answers an https get with x-access-token and a freshly minted token

Given argv ["get"], an environ carrying the App secrets, stdin describing protocol=https host=github.com, and MintSeams injected through main's seams parameter so no real openssl sign or network mint is attempted
When credential_helper.main is invoked over injected streams
Then stdout carries username=x-access-token and password=<the minted installation token>
And the exit code is 0

## Scenario: the credential helper emits no credential for a non-https context

Given argv ["get"] and stdin describing protocol=ssh
When credential_helper.main is invoked
Then stdout is empty
And the exit code is 0, which git reads as "no credential from this helper"

## Scenario: the credential helper's store and erase are no-ops for the ephemeral token

Given argv ["store"] or ["erase"] with any stdin
When credential_helper.main is invoked
Then nothing is written or removed anywhere
And stdout is empty and the exit code is 0

## Scenario: the credential helper fails closed with the actionable diagnostic on stderr

Given argv ["get"], an https context, and an environ missing GITHUB_PRIVATE_KEY
When credential_helper.main is invoked
Then stderr carries the GithubAppAuthError detail naming the missing variable and the tenant's credential_wrapper
And stdout is empty
And the exit code is non-zero

## Scenario: a legacy record reads its optional-on-read fields back as their defaults

Given a WorkItem constructed with only the fifteen required fields, including a real non-sentinel rank
When its optional-on-read fields are read
Then spec_commitment_hint, acceptance_criteria, notes, supersedes, admission_policy, acceptance_policy, blocked_reason, factory_safety and review_requirement are None
And awaits_scope_override is False

## Scenario: record identity is a stable sha256 over the canonical serialization

Given two WorkItem records equal in every field
When work_item_record_identity is computed for each
Then both values are identical and of the form sha256:<64 hex digits>
And changing any content field changes the value
And a record that supersedes another has a different identity from the record it amends, because the supersedes pointer is itself part of the canonical serialization

## Scenario: supersession reduction keeps only heads and surfaces concurrent divergence

Given records A and B for one id where B's supersedes names A's identity
And records C and D for another id that both supersede the same ancestor and neither supersedes the other
When reduce_work_item_heads is invoked over all of them
Then the first id maps to exactly (B,)
And the second id maps to both C and D, ordered by the deterministic (captured_at, identity) tie-break, rather than being silently resolved

## Scenario: materialize picks one head per id and is the identity collection for a one-record-per-id substrate

Given the divergent heads C and D for one id
When materialize_work_items is invoked
Then that id maps to the winner of the full (captured_at, identity) tie-break — the greatest captured_at, and on equal captured_at the greatest per-record identity
And when every id has exactly one record the result maps each id to that record unchanged

## Scenario: random_id_suffix yields a six-character base32 suffix that varies across calls

When random_id_suffix is invoked many times
Then every value is exactly six characters from the lowercase base32 alphabet
And the values are not all identical

## Scenario: a store facade satisfies WorkItemStore structurally and round-trips append then read

Given an in-memory facade class with read_work_items() and append_work_item(*, item) and no inheritance from WorkItemStore
When it is checked against the WorkItemStore protocol by static assignability — never isinstance, because WorkItemStore is not @runtime_checkable and isinstance against it raises TypeError
Then it satisfies the protocol
And after append_work_item with a record, read_work_items yields that record
And read_work_items is empty before any append

## Scenario: lane_of overlays blocked/dependency on a ready item with an open dependency

Given a WorkItem with stored status "ready" whose depends_on names a local id
And an index in which that local id is not done
When lane_of is invoked with the item, the index and a manifest
Then the result is Lane(name="blocked", reason="dependency")
And when that local id is done in the index the result is Lane(name="ready", reason=None)

## Scenario: lane_of renders a stored blocked item with its stored reason

Given a WorkItem with stored status "blocked" and blocked_reason "needs-human"
When lane_of is invoked
Then the result is Lane(name="blocked", reason="needs-human")
And for a stored blocked_reason "infra-external" the rendered reason is "infra-external"
And a stored blocked item with an open dependency still renders its stored reason, not "dependency"

## Scenario: lane_of leaves every other stored state as its own lane with no reason

Given WorkItems with stored status "backlog", "pending-approval", "active", "acceptance" and "done"
When lane_of is invoked for each
Then each result is Lane(name=<that status>, reason=None)

## Scenario: an unresolved sibling_work_item dependency fails closed while a missing local id does not block

Given a CrossRepoManifest whose targets declare the sibling repo, without which resolution short-circuits to RefStatus.UNKNOWN before the lookup is consulted at all
And a ready WorkItem whose depends_on names a sibling_work_item in that repo
And a sibling_status_lookup that returns RefStatus.UNKNOWN for it
When is_item_ready is invoked
Then the result is False
And when the lookup returns RefStatus.CLOSED the result is True
And a ready WorkItem whose depends_on names a local id absent from the index is ready, because no-orphan-dependency owns that case

## Scenario: is_item_ready agrees with lane_of by construction

Given any WorkItem, index, manifest and optional sibling_status_lookup
When is_item_ready and lane_of are both invoked with the same arguments
Then is_item_ready is True exactly when lane_of(...).name == "ready"

## Scenario: ready_sort_key orders by rank, then an aging tier within that rank, then id

Given a key built by calling the ready_sort_key factory with a now and no ready_since_lookup
And ready WorkItems with ranks "a0", "a1" and "a1" and ids "z", "b" and "a"
When they are sorted by that key
Then the order is rank "a0" first, then the two "a1" items ordered by id "a" before "b"
And when a ready_since_lookup is injected instead, an item ready LONGER than ready_aging_threshold_hours — 24 hours by default — sorts ahead of its equal-rank newer siblings, longest wait first
And rank remains the primary key, so an aged item is never promoted across a rank tier
And an item whose ready instant is unknowable, because no lookup was injected or the lookup returned None, takes no age advantage and keeps the id tie-break
And a naive now or a naive looked-up instant is read as UTC rather than failing on mixed awareness

## Scenario: key_between yields a rank key strictly between its neighbors, with None as an open end

Given neighbor keys a and b with a < b
When key_between is invoked with them
Then the result k satisfies a < k < b
And key_between(a=None, b=None) yields a first key, key_between(a=k, b=None) yields a key after k, and key_between(a=None, b=k) yields a key before k

## Scenario: n_keys_between yields n evenly spaced sorted keys

Given neighbor keys a and b and n of 5
When n_keys_between is invoked with them
Then the result is a list of 5 distinct keys, each strictly between a and b, in ascending order
And n of 0 yields an empty list

## Scenario: the bottom sentinel sorts strictly after every real rank key

Given BOTTOM_SENTINEL and any key the fractional-indexing library can generate
When the two are compared as strings
Then BOTTOM_SENTINEL sorts after the real key
And BOTTOM_SENTINEL uses a character outside the base-62 alphabet so no generated key can ever equal or follow it
And a store adapter substitutes it only for a legacy line lacking rank; the WorkItem.rank domain field never carries it

`SPECIFICATION/spec.md` §"Public surface" MUST gain the following exemption record, appended as the final paragraphs of that section, verbatim. It lands in `spec.md` rather than in `scenarios.md` because a normative prose register is not a Gherkin scenario, and `scenarios.md` holds only scenario blocks; `spec.md` §"Public surface" is already this repository's venue for consciously-excluded public surface, being the section that names `tests/public-surface-debt.json` as its authority.

Consciously exempted from scenario coverage, with the reason recorded here so the decision is
ratified rather than implied (every name below is exercised as a Given or a Then inside the
`scenarios.md` scenarios for these two families, and none carries behaviour of its own):

- `github_auth`: `GithubAppConfig` and `DEFAULT_API_URL` (data carrier and constant, exercised by the
  config scenarios); `GithubAppAuthError` (the single domain error, exercised by every fail-closed
  scenario); `MintSeams`, `SignRs256`, `HttpJson` and `DEFAULT_MINT_SEAMS` (the injected seam bundle
  and its protocol shapes, exercised by every mint scenario); `TOKEN_REFRESH_SECONDS` (a constant,
  asserted inside the refresh-horizon scenario); `credential_helper.run` (process wiring of the real
  streams — it carries no behaviour of its own beyond passing `sys.argv`, `os.environ` and the real
  streams to `main`, whose behaviour every credential-helper scenario already covers, and the process
  entry point itself is covered by the console-script contract in `contracts.md`).
- `work_items`: `WorkItemStatus`, `AdmissionPolicy`, `AcceptancePolicy`, `StoredBlockedReason`,
  `WorkItemType`, `Origin`, `Resolution`, `LaneName`, `BlockedReason`, `FactorySafety` and
  `ReviewRequirement` (closed `Literal` value sets with no behaviour beyond typing; the last two are
  carried as the `WorkItem.factory_safety` and `WorkItem.review_requirement` fields the
  legacy-defaults scenario reads back as `None`); `DependsOnRaw` (a type alias); `AuditRecord` and
  `Lane` (frozen data carriers, exercised by the identity and lane scenarios); `_fractional_indexing`
  (the verbatim CC0 port of `rocicorp/fractional-indexing`, underscore-private, outside the 43
  documented names by the same `# @generated` exclusion the public-surface inventory test applies,
  documented for attribution and covered by its own ported tests in
  `tests/livespec_runtime/work_items/test__fractional_indexing.py`).

CO-EDIT, applied in the same ratification changeset (the file is outside the spec target and is therefore carried by the spec commitment below rather than by `resulting_files`): `tests/heading-coverage.json` MUST gain one row per new scenario. Because no consumer-tier test exists yet for these two families, every row is a `TODO` entry whose `reason` explicitly acknowledges the integration-tier requirement, which non-functional-requirements.md §"Test discipline" permits during transition; each reason also names the unit-tier test that exercises the behaviour today. The rows, verbatim:

```json
[
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: load the App config from the tenant's credential-wrapper environment",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_config.test_both_secrets_present_returns_config_with_defaults."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: App config resolution fails closed naming every missing variable",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_config.test_empty_values_are_treated_as_missing_and_all_named."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: the optional installation pin and API-root override are carried into the config",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_config.test_optional_installation_id_pin_and_api_url_override_are_carried."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: b64url encodes with the URL-safe alphabet and no padding",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_signing.test_b64url_uses_urlsafe_alphabet_without_padding."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: the App JWT signing input is an RS256 header.payload with caller-injected time",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_signing.test_jwt_signing_input_is_rs256_header_dot_backdated_claims."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: normalize_pem re-wraps a flattened key and passes a well-formed PEM through unchanged",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_signing.test_normalize_pem_rewraps_flattened_single_line."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: RS256 signing with openssl round-trips against openssl verify",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_signing.test_sign_rs256_with_openssl_round_trips_with_openssl_verify."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: an unloadable private key is an expected misconfiguration surfaced as GithubAppAuthError",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_mint_railway.test_sign_rs256_routes_an_unloadable_key_to_the_failure_track."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: minting with a pinned installation performs no discovery",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_mint.test_pinned_installation_mints_without_discovery."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: minting discovers the sole installation when none is pinned",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_mint.test_sole_installation_discovery_resolves_and_mints."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: minting with several installations and no pin fails closed directing the operator to pin one",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_mint.test_multiple_installations_require_a_pin."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: the provider mints on first use and caches in process memory only",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_provider.test_calls_within_the_refresh_horizon_reuse_the_cached_token."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: the provider re-mints transparently once the 55-minute refresh horizon passes",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_provider.test_refresh_fires_at_the_horizon_before_the_token_actually_expires."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: the credential helper answers an https get with x-access-token and a freshly minted token",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_credential_helper.test_get_answers_x_access_token_username_and_minted_password."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: the credential helper emits no credential for a non-https context",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_credential_helper.test_get_non_https_context_emits_no_credential."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: the credential helper's store and erase are no-ops for the ephemeral token",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_credential_helper.test_store_and_erase_are_noops_for_the_ephemeral_token."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: the credential helper fails closed with the actionable diagnostic on stderr",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.github_auth.test_credential_helper.test_get_missing_env_fails_closed_with_actionable_diagnostic."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: a legacy record reads its optional-on-read fields back as their defaults",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_types.test_work_item_admission_policy_defaults_to_none."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: record identity is a stable sha256 over the canonical serialization",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_reduce.test_record_identity_is_independent_of_supersedes_pointer_only."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: supersession reduction keeps only heads and surfaces concurrent divergence",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_reduce.test_divergent_heads_are_both_surfaced."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: materialize picks one head per id and is the identity collection for a one-record-per-id substrate",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_reduce.test_divergent_heads_materialize_picks_greatest_captured_at."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: random_id_suffix yields a six-character base32 suffix that varies across calls",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_reduce.test_random_id_suffix_format."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: a store facade satisfies WorkItemStore structurally and round-trips append then read",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_store.test_append_then_read_round_trips."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: lane_of overlays blocked/dependency on a ready item with an open dependency",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_lifecycle.test_lane_of_ready_with_open_local_dep_is_blocked_dependency."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: lane_of renders a stored blocked item with its stored reason",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_lifecycle.test_lane_of_stored_blocked_wins_over_open_dependency."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: lane_of leaves every other stored state as its own lane with no reason",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_lifecycle.test_lane_of_passes_non_overlay_states_through."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: an unresolved sibling_work_item dependency fails closed while a missing local id does not block",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_lifecycle.test_is_item_ready_false_for_ready_with_unresolved_sibling_dep."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: is_item_ready agrees with lane_of by construction",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_lifecycle.test_is_item_ready_agrees_with_lane_of_by_construction."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: ready_sort_key orders by rank, then an aging tier within that rank, then id",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_lifecycle.test_ready_sort_key_orders_aged_equal_rank_items_ahead_of_newer_ones."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: key_between yields a rank key strictly between its neighbors, with None as an open end",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_rank.test_key_between_midpoint_is_strictly_between_neighbors."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: n_keys_between yields n evenly spaced sorted keys",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_rank.test_n_keys_between_returns_n_evenly_spaced_sorted_keys."
 },
 {
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "heading": "## Scenario: the bottom sentinel sorts strictly after every real rank key",
  "test": "TODO",
  "reason": "Consumer-tier test not yet written; this row acknowledges non-functional-requirements.md \u00a7\"Test discipline\" (\"Scenario-tier coverage\"): the mapped test MUST sit at the integration tier (tests.consumer.* or pytest.mark.integration). Owed by the spec commitment consumer-tier-scenario-tests-github-auth-work-items. Unit-tier coverage exists today at tests.livespec_runtime.work_items.test_rank.test_bottom_sentinel_sorts_strictly_after_every_real_key."
 }
]
```

Every one of the 43 public names in the two families is thereby either the subject of a scenario in `scenarios.md` or named in the exemption record in `spec.md` §"Public surface"; the acceptance criterion of gap-vjxowbbp ("at least one scenario entry, or consciously exempted with the reason recorded") is satisfied and the enumerator MUST no longer return that gap id.
