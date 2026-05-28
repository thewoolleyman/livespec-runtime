# tests/

Mirrors `livespec_runtime/` one-to-one (per the
`tests_mirror_pairing` discipline).

Conventions:

- pytest is the test framework (`uv run pytest tests/` or
  `just check-per-file-coverage` for the per-file 100% gate).
- Every directory under `tests/` (except `fixtures/` subtrees)
  carries a `CLAUDE.md` per `check-claude-md-coverage`.
- `tests/heading-coverage.json` is the heading-coverage registry
  consumed by `check-heading-coverage` (canonical aggregate slug
  per epic li-univck Phase 3.3 self-host wiring, work-item
  li-runwir).
