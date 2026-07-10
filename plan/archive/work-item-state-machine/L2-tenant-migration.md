# L2 tenant migration — `livespec-runtime` beads tenant ✅ DONE

The fleet-wide **L2 migration** (the 9-tenant lockstep schema migration;
fleet anchor `livespec-35s3zo`) applied to **this repo's own
`livespec-runtime` beads tenant**, after the L0 (`v0.5.0`) and L1a
releases landed the tooling. `livespec-runtime` is a thin tenant for L2
purposes (decision 42: its spec carries no work-item schema; only the
**tenant data** migrates — custom-status registration + `rank` backfill).

**References (CORE design of record):**
`/data/projects/livespec/plan/work-item-state-machine/research/04-slice-plan.md`
(§"L2 — migration") + `03-decision-log.md` (decisions 36 + 39).

Migration run **2026-06-29**. All tenant commands wrapped in the fleet
env wrapper (`with-livespec-env.sh`, which injects the tenant password).

## Step 1 — register the 5 custom lifecycle statuses

```bash
with-livespec-env.sh bd config set status.custom \
  "backlog,pending-approval,ready:active,active:wip,acceptance:wip"
```

Registers the five non-native lifecycle states as beads custom statuses
(the `<name>:<category>` suffix maps each to its beads category;
`backlog` / `pending-approval` take the default). `blocked` → native
`blocked` and `done` → native `closed`, so they need no custom entry.
This completes the 7-state `WorkItemStatus` surface
(`### livespec_runtime.work_items.types`) on the tenant. Idempotent
config write; existing items' stored status values are untouched.

## Step 2 — backfill the required `rank` field (legacy-seed)

`rank` is the sole ordering authority and strictly required in the new
schema; pre-migration rows carried no `metadata.rank` (each read back
through the store-adapter **bottom sentinel**, `~`). The backfill seeds a
real `rank` for **every** existing item via the orchestrator's
`rebalance-ranks` **legacy-seed** primitive (decision 39): order the
WHOLE set by the legacy `priority → captured_at → id` key (so the new
`rank` order matches the old effective priority order), then assign `N`
evenly-spaced fresh base-62 keys via
`livespec_runtime.work_items.rank.n_keys_between(a=None, b=None, n=N)`.

`captured_at ⇄ created_at` (the beads-native column). Each key was
written **surgically** with `bd update <id> --set-metadata rank=<key>`,
which sets only `metadata.rank` and **preserves** the rest of each
record's metadata (notably the merge-evidence `audit` objects on the
closed L0/WI-A work-items). `priority` (the beads-native column) survives
harmlessly but is no longer the logical ordering field.

### The applied `id → rank` mapping (15 items, legacy order)

| #  | rank | id | priority | captured_at (created_at) |
|---:|------|----|---------:|--------------------------|
| 0  | `a0` | `livespec-runtime-90k`     | 1 | 2026-06-12T22:27:17Z |
| 1  | `a1` | `livespec-runtime-ani`     | 1 | 2026-06-13T01:12:53Z |
| 2  | `a2` | `livespec-runtime-kyk`     | 2 | 2026-06-11T20:36:00Z |
| 3  | `a3` | `livespec-runtime-l4yojx`  | 2 | 2026-06-29T06:44:21Z |
| 4  | `a4` | `livespec-runtime-lel76i`  | 2 | 2026-06-29T09:46:32Z |
| 5  | `a5` | `livespec-runtime-lxgk3g`  | 2 | 2026-06-29T09:46:33Z |
| 6  | `a6` | `livespec-runtime-tscgce`  | 2 | 2026-06-29T09:46:34Z |
| 7  | `a7` | `livespec-runtime-rfwfie`  | 2 | 2026-06-29T09:46:36Z |
| 8  | `a8` | `livespec-runtime-ocekuv`  | 2 | 2026-06-29T09:46:38Z |
| 9  | `a9` | `livespec-runtime-emz`     | 2 | 2026-06-29T12:29:19Z |
| 10 | `aA` | `livespec-runtime-x1docp`  | 3 | 2026-05-26T00:00:00Z |
| 11 | `aB` | `livespec-runtime-y2hd44`  | 3 | 2026-05-26T00:00:00Z |
| 12 | `aC` | `livespec-runtime-nlx`     | 3 | 2026-06-09T04:40:10Z |
| 13 | `aD` | `livespec-runtime-hvs`     | 3 | 2026-06-09T04:45:32Z |
| 14 | `aE` | `livespec-runtime-pcy`     | 3 | 2026-06-14T03:06:03Z |

(All 15 items are `closed`; the tenant had no live/open items at
migration time, so this is a pure historical re-key. New items filed
post-migration receive their `rank` from the orchestrator's append path.)

## Verification (post-migration)

- `status.custom` = `backlog,pending-approval,ready:active,active:wip,acceptance:wip`.
- All **15** items carry a **real, non-sentinel** `metadata.rank`; none
  missing, none `~`.
- Ranks are **unique** and, sorted, reproduce the legacy
  `priority → captured_at → id` order exactly.
- The **9** records carrying merge-evidence `audit` metadata retained it
  (surgical `--set-metadata` write).

The `livespec-runtime` tenant is now on the new (7-state status + `rank`)
schema. Nothing in the repo's product code or spec changed for L2 — only
the tenant data — so this note is the in-repo formalization of the
migration (decision 42 / slice-plan §L2).
