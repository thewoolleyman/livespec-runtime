# Archive — frozen pre-cutover impl-tracking snapshot

This directory holds the **frozen, read-only** plaintext impl-tracking
store from before livespec-runtime cut its work-item tracking over from
`livespec-impl-plaintext` (JSONL files at the repo root) to
`livespec-impl-beads` (a per-repo beads/Dolt **tenant database** on the
shared dolt-server, tenant name `livespec-runtime`).

| File | What it is |
|---|---|
| `work-items.jsonl` | The pre-cutover work-items store (`livespec-impl-plaintext` substrate). |
| `memos.jsonl` | The pre-cutover memos store (`livespec-impl-plaintext` substrate). |

## Cutover

The cutover landed via the flip PR that switched `.livespec.jsonc`'s
`implementation.plugin` from `livespec-impl-plaintext` to
`livespec-impl-beads` and added the `.beads/config.yaml` beads client
config (epic li-qngbn3, Phase 5 / work-item li-ws2iv4). From that PR
onward, this repo's live work-item tracking is the `livespec-runtime`
tenant DB; these JSONL files are a point-in-time snapshot retained only
for audit and rollback.

The migration into the tenant DB preserved the records at full parity
(the snapshot here is **byte-unmodified** from its repo-root location —
only `git mv`'d here, never edited). The migrated tenant holds the same
records, keyed `livespec-runtime-<suffix>`.

## Do not edit

These files are frozen. The tenant Dolt DB is the source of truth for
live tracking. Do not edit, append to, or re-point tooling at these
files.

## Reversing the cutover

The flip is reversible: revert the flip PR (which restores
`.livespec.jsonc` to the `livespec-impl-plaintext` block and the JSONL
paths) and `git mv` these two files back to the repo root. The frozen
snapshot here is the rollback source.
