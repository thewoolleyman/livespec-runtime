# tests/consumer/

Top-of-pyramid consumer-style test tier (epic li-scetier Wave 4,
work-item li-scetrn). Unlike `tests/livespec_runtime/` (which mirrors
the source tree one-to-one at the unit tier), this directory does NOT
mirror a source module — it is a behavior tier keyed off
`SPECIFICATION/scenarios.md`.

Conventions:

- Tests import ONLY `livespec_runtime`'s public surface (per
  `SPECIFICATION/contracts.md` §"Module-level public surface") and
  drive consumer-shaped workflows, asserting on consumer-visible
  RETURN VALUES (`RefStatus`) and error TYPES
  (`CrossRepoSchemaError`, `NonCanonicalGithubUrlError`) — never
  internal shape (argv lists, private helpers, retry internals).
- `gh` is never invoked live; `subprocess.run` is monkeypatched with
  the recorded fixture payloads under
  `tests/livespec_runtime/cross_repo/providers/fixtures/`.
- The node-id prefix `tests.consumer` is the integration-tier-or-above
  allowlist entry declared in `pyproject.toml`
  `[tool.livespec_dev_tooling].scenario_tiers`; `tests/heading-coverage.json`
  maps every `## Scenario:` heading (many-to-one) to a test here, which
  `check-heading-coverage` enforces under the dev-tooling v0.9.0
  scenario-tier rule.

The four `test_github_app_*` / `test_work_item_*` modules carry the 32
`github_auth` and `work_items` scenarios ratified as v025 (work-item
`livespec-runtime-a27`), one test per scenario. Their side-effecting seams
are INJECTED rather than patched: `MintSeams` is passed through
`mint_installation_token` / `credential_helper.main`, and the token
provider's clock is passed through its constructor — both parameters
default to the production surface (`DEFAULT_MINT_SEAMS`, `time.time`), so
omitting the injection would attempt a real openssl sign and a real network
mint. The one genuine process spawn in this tier is `openssl`, offline, for
the RS256 sign/verify round-trip that scenario names.
