# scenarios.md — livespec-runtime

Gherkin scenarios covering the library's contract surface. Each
scenario corresponds to a public-surface path in `contracts.md`;
adding a new public symbol SHOULD land with at least one scenario
here.

## Scenario: resolve a closed pull-request dependency

Given a CrossRepoManifest declaring repo slug "livespec" with github_url "https://github.com/thewoolleyman/livespec"
And a PullRequestDependency with repo "livespec" and number 166
And gh pr view returns state "MERGED" on the first call
When resolve_ref is invoked with the entry, the manifest, and any local_status_lookup
Then the return value is RefStatus.CLOSED
And the retry layer makes exactly one gh invocation

## Scenario: resolve an open pull-request dependency

Given a CrossRepoManifest declaring repo slug "livespec-runtime" with github_url "https://github.com/thewoolleyman/livespec-runtime"
And a PullRequestDependency with repo "livespec-runtime" and number 2
And gh pr view returns state "OPEN" on the first call
When resolve_ref is invoked
Then the return value is RefStatus.OPEN

## Scenario: pull-request dependency under retry exhaustion

Given a CrossRepoManifest with a single configured repo
And a PullRequestDependency targeting that repo
And gh pr view raises CalledProcessError on every attempt
When resolve_ref is invoked
Then retry_with_backoff sleeps 1.0s after attempt 1
And retry_with_backoff sleeps 2.0s after attempt 2
And the return value after the third failure is RefStatus.UNKNOWN

## Scenario: pull-request dependency with unknown repo slug

Given a CrossRepoManifest declaring only repo slug "livespec"
And a PullRequestDependency with repo "livespec-runtime" and number 2
When resolve_ref is invoked
Then the return value is RefStatus.UNKNOWN
And no gh invocations are issued

## Scenario: branch dependency that no longer exists on remote

Given a CrossRepoManifest declaring repo slug "livespec-runtime"
And a BranchDependency with repo "livespec-runtime" and name "feat/old-merged-branch"
And branch_exists_on_remote returns False on the first call
When resolve_ref is invoked
Then the return value is RefStatus.CLOSED
And branch_merged_into_default is not invoked

## Scenario: branch dependency present but not yet merged

Given a CrossRepoManifest declaring repo slug "livespec-runtime" with default_branch "master"
And a BranchDependency with repo "livespec-runtime" and name "feat/cross-repo-types-li-aclzfe"
And branch_exists_on_remote returns True
And branch_merged_into_default returns False
When resolve_ref is invoked
Then the return value is RefStatus.OPEN

## Scenario: branch dependency present and merged into default

Given a CrossRepoManifest declaring repo slug "livespec-runtime"
And a BranchDependency with repo "livespec-runtime" and name "some-merged-branch"
And branch_exists_on_remote returns True
And branch_merged_into_default returns True
When resolve_ref is invoked
Then the return value is RefStatus.CLOSED

## Scenario: local dependency delegates to caller-supplied lookup

Given a LocalDependency with work_item_id "li-aclzfe"
And a local_status_lookup that returns RefStatus.OPEN for "li-aclzfe"
When resolve_ref is invoked
Then the return value is RefStatus.OPEN
And no gh invocations are issued

## Scenario: sibling work-item dependency without sibling_status_lookup

Given a CrossRepoManifest declaring repo slug "livespec"
And a SiblingWorkItemDependency with repo "livespec" and work_item_id "li-e7h6ki"
And no sibling_status_lookup is supplied
When resolve_ref is invoked
Then the return value is RefStatus.UNKNOWN
And no gh invocations are issued

## Scenario: parse_depends_on_entry rejects unknown kind

Given a dict {"kind": "slack_thread", "channel": "#engineering"}
When parse_depends_on_entry is invoked
Then a Failure carrying CrossRepoSchemaError is returned
And the error detail names "slack_thread" as the unknown kind
And the error detail enumerates the four valid kinds

## Scenario: parse_depends_on_entry rejects missing required field

Given a dict {"kind": "pull_request", "repo": "livespec"}
When parse_depends_on_entry is invoked
Then a Failure carrying CrossRepoSchemaError is returned
And the error detail names "number" as the missing field

## Scenario: parse_cross_repo_manifest accepts minimal target

Given a dict {"livespec": {"github_url": "https://github.com/thewoolleyman/livespec"}}
When parse_cross_repo_manifest is invoked
Then the result is a CrossRepoManifest with one target keyed by "livespec"
And that target's local_clone is None
And that target's default_branch is "master"

## Scenario: parse_cross_repo_manifest rejects target missing github_url

Given a dict {"livespec": {"default_branch": "main"}}
When parse_cross_repo_manifest is invoked
Then CrossRepoSchemaError is raised
And the error detail names "github_url" as the missing field for slug "livespec"

## Scenario: non-canonical github_url raises NonCanonicalGithubUrlError

Given a github_url "git@github.com:thewoolleyman/livespec.git"
And a BranchDependency referring to that target
And the provider's branch_exists_on_remote is invoked with that url
When the provider tries to split the owner/name
Then NonCanonicalGithubUrlError is raised
And the error carries the offending url verbatim

## Scenario: every attention kind has a matching stable-ID prefix

- **Given** the declared kind-to-prefix mapping in `contracts.md`
- **When** it is compared against the ratified `AttentionKind` members
  and the accepted prefix set of `validate_attention_item_id`
- **Then** the mapping MUST be total over the kinds, injective into the
  prefixes, and cover exactly the accepted prefix set — with no kind
  lacking a row, no accepted prefix absent from the mapping, and no two
  kinds sharing a prefix

## Scenario: validate_attention_item_id rejects an id whose component is purely decimal

- **Given** the attention item id `impl:42`
- **When** it is validated by `validate_attention_item_id`
- **Then** the result MUST be false, because a positional index is not a
  stable natural key

## Scenario: validate_attention_item_id accepts a well-formed three-part hygiene id

- **Given** the attention item id `hygiene:stale-worktree:my-repo`
- **When** it is validated by `validate_attention_item_id`
- **Then** the result MUST be true

## Scenario: composition surfaces an invalid candidate rather than shortening the list

- **Given** one candidate whose id is well-formed and one whose id is not
- **When** `compose_needs_attention` is called with both
- **Then** `InvalidAttentionItemIdError` is raised
- **And** the error message names the rejected id
- **And** no list is returned at all — the valid candidate MUST NOT be
  returned alone, because a shorter list is indistinguishable from an
  absence of attention

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
