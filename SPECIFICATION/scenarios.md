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
Then CrossRepoSchemaError is raised
And the error detail names "slack_thread" as the unknown kind
And the error detail enumerates the four valid kinds

## Scenario: parse_depends_on_entry rejects missing required field

Given a dict {"kind": "pull_request", "repo": "livespec"}
When parse_depends_on_entry is invoked
Then CrossRepoSchemaError is raised
And the error detail names "number" as the missing field

## Scenario: parse_cross_repo_manifest accepts minimal target

Given a dict {"livespec": {"github_url": "https://github.com/thewoolleyman/livespec"}}
When parse_cross_repo_manifest is invoked
Then the result is a CrossRepoManifest with one target keyed by "livespec"
And that target's local_clone is None
And that target's default_branch is "master"

## Scenario: non-canonical github_url raises NonCanonicalGithubUrlError

Given a github_url "git@github.com:thewoolleyman/livespec.git"
And a BranchDependency referring to that target
And the provider's branch_exists_on_remote is invoked with that url
When the provider tries to split the owner/name
Then NonCanonicalGithubUrlError is raised
And the error carries the offending url verbatim
