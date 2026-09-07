# 001 — Charter: runtime backlog drain, round 2

Opened 2026-09-07 at the maintainer's direction ("create a new plan to hold all
the items identified in this repo, so overseerd will restart you. Drain
everything"). Round 1, `plan/archive/runtime-backlog-drain/` (epic
`livespec-runtime-c7toen`, archived 2026-09-07 after both gates), drained the
18-item snapshot of 2026-09-06 and left three named carriers plus a discharged
parking lot. This round owns everything open in the tenant at its freeze.

## 1. The doctrine is the drain-backlog skill, not this file

The operating rules — preconditions measured every resume, batch triage under
the seven-way sorting rule, factory-only execution with the closed exemption
enum, detached probe-gated engines, the loop without panes, anti-yak-shaving
admission, handoffs with one typed next action, and the exit gate — are
`livespec-overseer/.claude/skills/drain-backlog/SKILL.md`, the doctrine that
drained `livespec-dev-tooling`'s 258 items and this repository's 18. This
charter does not restate them; it binds this plan to them and records only
what is specific to this round. Round 1's charter remains the fuller local
statement of the same rules and is read-first for history.

## 2. The forest is frozen

`research/002-snapshot-2026-09-07.json` is the committed copy of the freeze
taken by `snapshot.py` at 2026-09-07T11:24:51Z (canonical for the skill's
scripts at `tmp/drain-backlog/snapshot.json`): TEN open items, by id —
`vll`, `qov`, `ld2`, `cgsjjm`, `pi3`, `2rg`, `cgw`, `bda`, `3r5`, `6tt`. That
list is this plan's scope, whole and fixed. Nine were filed by round 1 or at
its close-out; `pi3` arrived independently on 2026-09-07 and is admitted by
being open at the freeze. Status is read fresh from the ledger, never written
here; the snapshot's tiering is a heuristic the batch-1 ruling corrects.

Exit gate: every one of the ten is `closed` or carries a recorded
disposition in a scope event on this epic; no engine running; no worktree or
branch of this drain left behind; the final handoff names whatever is
transferred out. Then this plan archives through its own two gates — child
disposition and an independent completeness review — never on a status flip.

## 3. What this round already knows at the freeze

Measured before the first ruling, so the ruling starts from facts:

- The orchestrator package is NOT importable in this repo's environment, so
  `qov` (consume the orchestrator's `factory-bypass-audit` as a red gate) is
  not dispatchable as written; a red gate here must ship as an importable
  check, which is the same `livespec-dev-tooling` deliverable `vll` waits on.
- `cgsjjm` waits on dev-tooling's central fleet consumption measurement; that
  measurement is a read-only tool in the dev-tooling checkout and this round
  runs it rather than waiting to be told its result.
- Three items are spec-first (`2rg` needs one NFR clause, `3r5` is a spec
  reflow, `bda` is scenarios.md): they route through `propose-change` and
  `revise`, and the proposal files are the maintainer's to authorize.
- `ld2` is a consent dialogue, not a code change; it needs the maintainer at
  the keyboard and is never a factory item.
- `cgw` and `6tt` are dispatchable as written once acceptance criteria are
  authored at dispatch time.

## 4. Durability

Handoffs and scope events live on this epic; `overseerd` resumes a
context-threshold restart with "resume plan epic <id> in repository <path>;
read its ledger-held plan state", so the typed `next_action` is the restart
contract and is kept dispatchable whenever anything is. The SessionStart hook
`.claude/hooks/backlog_drive_directive.py` is re-pointed at this slug and
retires itself when this directory archives. Every closure names the batch
ruling in its close reason. A drive-session turn that ends with no scheduled
wakeup and no running monitor has stalled, whatever else it accomplished.
