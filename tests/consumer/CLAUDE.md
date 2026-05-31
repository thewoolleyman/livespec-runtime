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
