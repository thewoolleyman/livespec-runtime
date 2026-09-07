# 001 — Charter: drain the runtime backlog through the factory

Opened 2026-09-06 at the maintainer's direction, in a session named for this
plan rather than for a role. It is the same-tenant analogue of
`livespec-dev-tooling`'s `dev-tooling-backlog-drain` plan (epic
`livespec-dev-tooling-kcoslm`), which in turn applies the console repo's
`retire-overseer-and-redesign-control-plane-around-console` decisions D1, D4
and D5: tmux is a retired transport, the resident LLM foreman role is deleted,
and every foreman capability reduces to an orchestrator primitive that already
exists. The maintainer's intent, kept verbatim from the dev-tooling opening:

> I want to work them all off and close them because I think some of them are
> critical to the stability of the ecosystem. But others may be cruft and not
> actually necessary. And I don't want to have to directly manage all of the
> tmuxes.

> Something has to own the forest, because you LLMs ALWAYS lose the forest for
> the trees.

This plan owns this repository's forest. Nothing here is a new substrate; it
is a discipline over primitives that exist today, plus one harness-level
mechanism (§7) added because the dev-tooling drive session stalled twice on
its first day for want of it.

## 1. The forest is frozen

`research/002-snapshot-2026-09-06.json` lists every open work item in the
`livespec-runtime` tenant at the moment this plan opened: 18 items, by id,
status, type, priority and title. That list is this plan's scope, whole and
fixed.

- **Exit gate.** The plan is complete when every id in the snapshot is
  `closed`, or carries a recorded disposition (a scope event on this epic
  naming the id and one of the sorting outcomes in §5), AND the worktree root
  `~/.worktrees/livespec-runtime/` holds no worktree that the triage did not
  explicitly keep (§5, hygiene).
- **Nothing filed after the snapshot extends the plan.** A new item is either
  admitted under §4 or it is out of scope. Inventing an item is not progress
  on anything this plan measures.
- **Status is never written here.** Progress is read fresh from the ledger.
  The snapshot is an id list, not a status board; a status column in a file is
  a shadow ledger.

## 2. Roles — there is no foreman

| Role | Who | What it does |
|---|---|---|
| Engine | the orchestrator's dispatcher loop | Takes the `ready` set into fabro runs under `wip_cap` (10 here), accepts on green under `acceptance_mode: ai-only`. Exists; needs no seat. |
| Drive session | one LLM session resumed with `plan runtime-backlog-drain` | The D4 role: triage, rulings with the maintainer, the thin hand-driven set, `needs-attention` reads, re-dispatch, handoffs on this epic, and the loop of §8. |
| Maintainer | the human | Rules on triage batches; answers the human-gated valves; restarts the drive session when it dies. |

Dropped for this repository, by reference to console D5: the `foreman` skill
and its pane roster, one-action-per-tick budget, `foreman-act` proposals,
escalation JSON files, heartbeat files, tmux-named worker seats, and the
grooming seat. The `overseerd` daemon may keep running for other repositories;
this plan does not read it and does not write anything it reads.

The drive session resumes from the ledger alone: this epic's typed
`next_action`, its handoff and scope-event comments, and the `context`
envelope. It needs no chat history and no tmux state.

## 3. Execution rule — everything goes through the factory

The only execution verbs the drive session may use for a work item are
`drive --action impl:<id>` and the dispatcher loop. A tmux worker session is
never started for a work item.

**The factory is unproven here and is measured first.** The dispatch journal
in this repository shows 28 outcomes, most failed, and no event since
2026-08-21; every PR merged since then is a pin bump or hand work. So tier 0
of §6 is one canary dispatch of a small `ready` item, measured by its journal
`outcome` event before any ordering below is trusted. A canary failure is
itself the first `factory-path-defect` item, admitted under §4.

**Exemption is a closed enum.** An item may be worked by hand, through the
ordinary worktree → PR → merge protocol, only when it is one of:

- `infra-in-person` — the change is a host, secret, registrar, or billing act
  that no sandbox can perform (console D4 item 1).
- `factory-path-defect` — the item IS a defect in the path a factory run takes
  in this repo (the commit hooks, the gate runner, the sandbox image, the
  dispatcher's typed inputs), so a factory run cannot fix it (console D4 item
  3).

The classification is made at triage time and recorded in the scope event, not
improvised when a run fails. The default is dispatchable. An exempt item
carries a ledger label naming its reason, `factory-exempt:infra-in-person` or
`factory-exempt:factory-path-defect`, and nothing else counts as an exemption.
The label is the carrier because the orchestrator's `factory-bypass-audit`
takes `--allow-label` as its exemption policy, so the same label that
authorizes the hand-worked PR is the one the gate in §7 reads.

**A failed run is re-dispatched or groomed, never hand-fixed.** When a factory
run fails on a dispatchable item, the response is one of: re-dispatch (when
the journal outcome is transient or the failure is in the run's own
environment), `groom` (when the item is oversized or non-converging), or a
discovered-during child under §4 (when the failure exposes a factory-path
defect). Hand-fixing a dispatchable item because "it's quicker" is the leak
this rule exists to close.

**Master red blocks every dispatch.** The dispatcher's master-green gate
refuses a run while master CI is red, so every tick (§8) reads master CI
first, and a red master is the tick's only work until it is green.

## 4. Anti-yak-shaving — what may be filed

A new work item may be created in this tenant during this plan only when it
is one of:

1. A **child of an open epic** that is itself in the snapshot.
2. A **discovered-during** defect that blocks a snapshot item or the canary of
   §3, filed with `--deps discovered-from:<snapshot-id>` so the provenance is
   a ledger edge, not a sentence.
3. A **consolidation** that closes two or more snapshot items into one.
4. One of the **two consume-leg children this plan files for itself** (§7).

Anything else is one line in a `PARKING LOT` comment on this epic and is not
filed. A parked idea is reviewed only when the snapshot is drained or when a
snapshot item turns out to depend on it.

## 5. Triage — the sorting rule and the batches

Every snapshot item receives exactly one disposition from the console program
board's sorting rule:

- **keep** — dispatchable as written; enters the ready set in priority order.
- **re-scope** — the intent survives but the shape does not; the item is
  rewritten (title, acceptance) before dispatch, or handed to `groom`.
- **superseded-by-transport** — the item exists only to serve the tmux /
  overseer transport that console D1 and D5 retire; close with that reason.
- **consolidate** — the item duplicates or fragments another; close into the
  survivor and record the survivor id.
- **close** — the item is cruft: no longer true, already landed, or not worth
  its own cost; close with the reason.

Two things the dev-tooling plan did not have to sort are in scope here:

- **Hygiene.** Fourteen worktrees dated 2026-07-18 to 2026-08-21 sit under
  `~/.worktrees/livespec-runtime/`, against this repository's own rule that no
  worktree is left orphaned. Each is disposed alongside the item it served:
  removed as merged, removed as abandoned, or kept by name with the item that
  still needs it.
- **The two unarchived plans.** `homelab-loop-hardening-runtime` is anchored
  to a snapshot epic and stays its own plan. `credential-reexec-loop-guard`
  has no anchor epic and a pre-Planning-Lane `handoff.md`; its disposition is
  ruled in batch 1.

With 18 items, triage is expected to be one batch. Dispositions are presented
grouped by class, not one item at a time, and recorded as scope events on
this epic once ruled. The closures the ruling authorizes are executed against
the ledger with the scope event named in the close reason. A disposition the
drive session is confident about is proposed as decided; only genuine doubt
is put as a question, and one question per turn.

## 6. Ordering

After triage, work is dispatched in this order, each tier drained before the
next is opened except where a dependency edge forces otherwise:

0. **The canary** (§3): one small dispatchable item, run to a journal
   `outcome`, before anything else.
1. **Factory-path defects** — anything that makes a factory run in this repo
   fail for reasons unrelated to the item it carries. Worked by hand where the
   factory cannot, under the `factory-path-defect` label.
2. **Enforcement-suite correctness** — checks that pass vacuously, pass on a
   half-pair, or fail on a true positive. A false green here poisons every
   later tier's evidence.
3. **The P1 items and the open epic's children.**
4. **The long tail** in priority order.

Cross-tenant items — livespec core contract questions, check code that
belongs in `livespec-dev-tooling`, fleet fan-out legs owned by another
repository — follow the console plan's never-work-around rule: file or link
the item in the owning tenant, record the path as a comment here, and do not
substitute a runtime-side workaround.

## 7. Durability — three layers plus the harness

The console plan's `never-work-around-upstream-dependencies` note measured
that a rule written in three places was ignored anyway, and the dev-tooling
drive session showed the same on 2026-09-06: with the loop of §8 written in
its charter, it handed off and parked twice, and could not say how a fresh
context would do better. So this plan carries the same three layers and adds
a fourth that does not depend on the model remembering anything:

- **Ledger.** Every ruling is a scope event; every session end is a handoff
  with a typed `next_action`; every closure names its scope event. The
  `next_action` text always ends with the standing instruction to arm the
  loop of §8 before the resumed session's first turn ends.
- **Repo prose.** `AGENTS.md` names this plan as the owner of the backlog,
  says the `foreman` skill is not to be invoked here, gives the one command
  that resumes the drive, and states that a drive session that ends a turn
  with no scheduled wakeup and no running monitor has stalled.
- **Harness.** A `SessionStart` hook in this repository's committed
  `.claude/settings.json` (`.claude/hooks/backlog_drive_directive.py`) prints
  the drive directive into every new session's context while
  `plan/runtime-backlog-drain/` exists unarchived: the plan slug, the resume
  command, the loop rule, and the order of the first tick. The harness
  injects it; the model does not have to recall it. When the plan archives,
  the hook goes quiet on its own.
- **Mechanical.** Two children, and only two, filed by this plan for itself.
  Both are **consume legs**: the check code is a `livespec-dev-tooling`
  deliverable under the never-work-around rule, filed there by the
  dev-tooling plan, and this repository wires the pack's checks in when they
  ship.
  1. **Item-provenance ratchet** — any item created after the snapshot
     instant must have a `parent` in the snapshot or a `discovered-from` edge
     to a snapshot item, or the check is red.
  2. **Factory-bypass gate** — the orchestrator's report-only
     `factory-bypass-audit`, consumed as a red gate here with the exemption
     enum of §3 as its allow policy.

Until both consume legs land, the §3 and §4 rules are prose plus the harness
hook, and every handoff says so.

## 8. The loop without panes

The drive session IS the loop. On resume its first turn, in order: read the
typed `next_action`; read master CI; run `needs-attention` and put any
human-gated valve to the maintainer as one question; act on what is ripe; and
arm a self-paced wakeup (the harness `loop` skill) or a monitor before the turn
ends. A turn that ends without one of those armed is a stall, whatever else it
accomplished.

Each tick re-checks three sources: the dispatch journal's `outcome` events,
`needs-attention`, and the open pull requests, with master CI read first per
§3. It acts on what is ripe and writes nothing when nothing changed. Healthy
waits are silent. A tick report lists what changed, by id, and does not
re-argue standing items.

Two operational rules learned on 2026-09-06: GitHub reads driven by a shell
loop or a sleep are refused by this family's rate-limit hook, so the loop's
GitHub reads use `gh api --cache <duration>` and bulk listings compared
locally; and a `bd` write's auto-backup permission warning is by design and
is never a finding.

What survives from the foreman contract is its evidence discipline only:
verify by the authoritative source (`bd show --json`, `gh pr view`, the
journal's `outcome` event), never by a peer's claim; carry a claim's hedge or
re-measure it; route before escalating; state capacity only from a capacity
verdict, and say "unknown" when there is none.

## 9. Known limits

- Nothing here keeps the drive session alive across a host restart, a
  usage-limit kill, or a context wind-down. The state survives in the ledger
  and the hook re-arms the directive; a human types the resume command. That
  is a one-line manual step, the same trade the console redesign makes.
- The factory's viability in this repository is asserted by nobody until the
  canary of §6 reports. Every ordering above is hedged on that outcome.
- The `factory-bypass-audit` allow-label policy is named here from the
  dev-tooling charter's reading of its source and has not been exercised in
  this repository. It is hedged until the first use measures it.
