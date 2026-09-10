# Agent instructions

## Codex dogfooding (OpenAI Codex CLI/TUI)

This repo's `/livespec:*` and orchestrator surfaces can be dogfooded from
OpenAI Codex CLI/TUI, not just Claude Code. Unlike the Claude path (plugins
enabled PER PROJECT via a committed `.claude/settings.json`), Codex plugin
enablement is **HOST-WIDE**: each registration persists in `~/.codex/config.toml`
and applies to every project on the host. Codex offers no project-scoped plugin
enablement, so there is no committed-settings analogue for the Codex path.

Install the three family plugins host-wide: livespec CORE (the artifact carrier
that ships the spec-side prose and wrappers), the `livespec-driver-codex` Codex
Driver (which supplies the `/livespec:*` operation surface over core's prose),
and the selected orchestrator plugin:

```bash
# livespec CORE (spec-side prose + wrappers; no skills of its own):
codex plugin marketplace add thewoolleyman/livespec
codex plugin add livespec@livespec

# The Codex Driver (supplies the spec-side /livespec:* operation surface):
codex plugin marketplace add thewoolleyman/livespec-driver-codex
codex plugin add livespec@livespec-driver-codex

# The selected orchestrator plugin (ships its own Codex skills):
codex plugin marketplace add thewoolleyman/livespec-orchestrator-beads-fabro
codex plugin add livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro
```

Once installed, Codex operations are driven via `codex exec` and NAME-selected as
`<plugin>:<op>` (for example, `livespec:next`,
`livespec-orchestrator-beads-fabro:list-work-items`) rather than as
`/`-prefixed slash commands. The distributed Drivers resolve their prose at
runtime; no `AGENTS.md` skill-to-prose mapping is required. See
`livespec/SPECIFICATION/contracts.md` §"Plugin distribution" and
`livespec/SPECIFICATION/non-functional-requirements.md` §"Codex dogfooding
contracts" for the authoritative install and resolution contracts.

The Codex TUI picker displays skills by short name with the plugin as context.
In `/skills` → `List skills` (or the `@` picker), search the operation name,
for example `orchestrate`; the row renders as
`orchestrate (livespec-orchestrator-beads-fabro)` with kind `Skill`. The
colon-qualified form `livespec-orchestrator-beads-fabro:orchestrate` is still
valid for prompt / `codex exec` name selection and model-visible skill
references, but it is not the picker row operators should expect.

## Agent operating posture

When the user gives a clear directive, carry the obvious next step through
without re-asking. In particular, once a task asks for repo mutation, the
worktree -> PR path below already answers "should I commit?", "should I push?",
and "should I open the PR?". Keep confirmation gates for genuinely ambiguous
scope choices and destructive or high-blast-radius actions not already
authorized in the current task.

For maintainer-owned livespec spec gates, do not materialize
`SPECIFICATION/proposed_changes/` files on the maintainer's behalf unless the
task explicitly asks for that operation. Prepare and validate the proposal
payload instead: findings JSON, the human-readable spec delta, and the exact
handoff command or next action for the maintainer to run through
`livespec:propose-change` / `livespec:revise`.

## Beads runtime operations

This repo's live work-item state is the `livespec-runtime` beads/Dolt tenant on
the shared dolt-server (`127.0.0.1:3307`). `.beads/config.yaml` carries only
committable connection coordinates; the tenant password is injected at call time
by `/usr/local/bin/with-livespec-env.sh`. Run `bd` and orchestrator operations
that touch the real tenant under that wrapper. `LIVESPEC_BEADS_FAKE=1` is for
hermetic tests and CI only, not for reading or writing the live tenant.

If a tenant-level `bd` write emits an auto-backup warning that includes a Dolt
backup permission denial for the tenant user, treat it as correct by design.
Tenant users are not granted backup rights; host-managed backup jobs own real
backups. Do not file work-items or attempt fixes for that warning alone.

## Backlog drive — the drain is done; no foreman seat here, ever

The plan `runtime-backlog-drain` DRAINED this repository's backlog and is
ARCHIVED at `plan/archive/runtime-backlog-drain/` (ledger epic
`livespec-runtime-c7toen`, closed 2026-09-07). All 18 items in its frozen
snapshot are closed. Its `SessionStart` hook
(`.claude/hooks/backlog_drive_directive.py`) retires itself once the plan
directory is gone, so it now prints nothing; the file is kept as the record of
that mechanism. Read the archived charter,
`plan/archive/runtime-backlog-drain/research/001-charter-runtime-backlog-drain.md`,
before reviving any of its reasoning.

**What round 1 left behind is now itself discharged.** Its three named carriers
were inherited by round 2 and closed there on 2026-09-07: `cgsjjm` was
re-scoped and shipped, and `vll` and `qov` were closed as NOT ACTIONABLE HERE
with their ask transferred by name (see round 2's carriers below). Round 1's
charter remains the fuller statement of the consume-leg reasoning.

**Two rules survive the plan and bind this repository generally:**

- **Do not invoke `/livespec-overseer:foreman` for this repository**, and do
  not start a tmux worker session for a work item. The console repo's
  `retire-overseer-and-redesign-control-plane-around-console` plan retired tmux
  as a transport (its decisions D1, D4, D5); this repo applies that, as
  `livespec-dev-tooling` does under its `dev-tooling-backlog-drain` plan.
- **Everything executes through the factory.** The only execution verbs for a
  work item are `drive --action impl:<id>` and the dispatcher loop. Hand work
  through worktree → PR → merge is allowed only for an item labelled
  `factory-exempt:infra-in-person` or `factory-exempt:factory-path-defect`.

**Round 2 DRAINED this repository's backlog and is archived at
`plan/archive/runtime-backlog-drain-2/`** (ledger epic
`livespec-runtime-53j3cs`). All ten items in its 2026-09-07 freeze are closed.
It also ratified two spec revisions — v024, correcting `contracts.md`'s
`ready_sort_key` bullet to the aging-aware factory the tree already shipped, and
v025, landing 32 `github_auth` / `work_items` scenarios plus the public-surface
exemption record. Its `SessionStart` hook retires itself once the plan directory
is gone, so it now prints nothing.

**What round 2 transferred out, by name** — the archive rule requires these be
stated exactly, and they are the only carriers:

- `livespec-runtime-a27` — owes the consumer-tier tests for all 32 v025
  scenarios, and OWNS every `"test": "TODO"` row those scenarios added to
  `tests/heading-coverage.json`. The pre-commit gate refuses a TODO row with no
  owning `work_item`, so this item is what keeps those rows legal rather than
  silent debt.
- `livespec-runtime-s5k` — the detection-coverage anchor, named by
  `dispatcher.detection_coverage_anchor`. An ANCHOR, not a unit of work: it is
  never done and MUST NOT be closed. Only `record_detection_run` writes to it.
- `livespec-dev-tooling-kcoslm` (other tenant) — carries the producer ask for
  BOTH consume legs. When livespec-dev-tooling ships an IMPORTABLE check module
  for the item-provenance ratchet or a factory-bypass audit, file FRESH consume
  items rather than reopening `vll` / `qov`: the consume shape depends on what
  the producer actually ships. Both legs owe FAIL-CAPABILITY proof before the
  gate is trusted green — a check that passes vacuously is worse than no check,
  and both exist precisely because prose enforcement was measured to fail.

**If you open a further plan here**, its own charter carries its scope freeze, its
admission rule and its loop discipline — those were properties of the drain
plans, not of this repository, and they retired with them. Two findings are
worth keeping. A drive-session turn that ends with no scheduled wakeup and no
running monitor has stalled, whatever else it accomplished. And round 2's
measured result: every defect it found was caught by a MECHANICAL check and none
by careful reading — a clause enumerator surfaced a spec drift via a vanished
test node id, a timestamp comparison caught a future-dated `created_at` that
would have refused its own reviews, the pre-push gate caught orphaned coverage
rows, the pre-commit gate caught an unowned TODO, and the archive gate caught a
coverage record earned over the wrong tree. Reading produced confident, wrong
prose repeatedly, including from the drive session itself. Build the check.

## Stop the line for breakages

**Stop the line for breakages.** When shared factory or fleet tooling is BROKEN
— a bad model or adapter config, a stale-but-fixable plugin build a session
dispatches through, a mint or credential outage, a gate wedged by a defect —
HALT, fix the root cause or notify its owner and WAIT for the fix, and resume
only on the NORMAL path once the fix rolls out through the ordinary channel
(release → `ensure-plugins` → reload → normal dispatch). Never pin a build,
re-route, or otherwise route around a breakage to keep your own work moving: a
broken-window workaround normalizes the outage, hides it from a real fix, and
validates only your private path, not the one every other session and fleet
member uses. A transient (a rate-limit window that resets, an intermittent
ENOSPC) is waited out and retried on the normal path; a permanent tool
limitation is designed within — neither is a bypass. This is the local face of
the closed factory-exempt enum above: `factory-exempt:factory-path-defect`
admits an item whose deliverable IS the fix to the broken factory path — worked
by hand precisely because a factory run cannot repair the factory — never a
hand-run to route ordinary work around a breakage, which the drain charter
forbids as the leak it exists to close. Fleet source: the livespec
`agent-disciplines.md` discipline §"A factory or tooling BREAKAGE stops the
line" (maintainer ruling 2026-09-10).

## Decision authority — when to ask, proceed, or self-resolve

Fleet-standard guidance, ported from
`livespec/AGENTS.md` §"When to ask, proceed, or self-resolve" and
`livespec-orchestrator-beads-fabro/AGENTS.md` §"Drive authorized work to
completion; do not over-ask". The default is to decide and report, not to
escalate.

**Why every governed member carries this.** On 2026-08-20 a track in this
fleet sat roughly sixteen hours parked on a picker whose option 1 was its own
recorded next action, and five self-decidable engineering calls were escalated
as standing maintainer questions. The investigation found the guidance was
real but partial: `AGENTS.md` is authored per repo and nothing propagates it,
so sessions in the repos that lacked it were reading a file that never told
them what they were allowed to decide.

- **Drive authorized work to completion; do not over-ask.** When the maintainer
  names a goal and says to finish or continue it, execute the WHOLE arc —
  implement, dispatch, PR, merge, iterate, archive — without pausing to confirm
  each already-authorized step. An operator-flow step that says "present
  options and let the user select" is satisfied by a standing directive once
  the goal is named; do not re-prompt. Default to acting, then reporting
  outcomes.
- **A recorded next action is an instruction, not a menu.** When a handoff, a
  work-item, or a plan timeline names exactly one next action, take it.
  Re-presenting it as option 1 of a picker is the stall shape above.
- **Research before gating.** If a question is answerable by reading the code,
  the spec, the docs, or by testing on a live system, do that, decide,
  implement, and report for objection. Reserve gates for genuine product or
  values calls, irreversible or outward-facing actions, and secret or
  host-mutation authorization.
- **Only ask on genuine doubt, one thing at a time.** Self-resolve trivial
  wording fixes, internal-consistency repairs, and items clearly aligned with
  established preferences, presenting each with its disposition. When a gate is
  warranted, ask exactly one question per turn.
- **One investigation, one finding, one question.** When a focused
  investigation surfaces unrelated discrepancies, finish the original question
  first and surface only the load-bearing finding; log side observations
  briefly. Cosmetic drift never blocks on its own.
- **Prescribed destructive ops are pre-authorized.** When a destructive git
  operation is the codified mechanism of an adopted workflow — the
  `git commit --amend` of the Red→Green step, for instance — the adoption is
  the authorization. Keep per-instance gating for ad-hoc `--amend`,
  force-push, `reset --hard`, or `branch -D` on unmerged branches.
- **An unratified filter inside a check is conformance, not ratification.**
  Narrowing, excluding, or filtering inside an enforcement check to match what
  the ratified spec already says is a conformance fix — implement it and report
  it. It only becomes a ratification question when the change would make the
  check assert something the spec does not.
- **A question you can answer with a recommendation is a finding, not a
  maintainer question.** If you can state the options, the costs, and which one
  you would pick, you have already done the deciding work. Decide it, record
  the reasoning where the work is tracked, and report it as decided.

## Repository mutation protocol

Every repo change uses a worktree → PR → merge → cleanup path. Treat
leaving dirty state, committing on the primary checkout, or asking the
user whether to commit as failures of the workflow, not as acceptable
stopping points.

1. Confirm the primary checkout before editing:

   ```bash
   git -C /data/projects/livespec-runtime config --get livespec.primaryPath
   git -C /data/projects/livespec-runtime status --short --branch
   ```

2. If the change will modify tracked files, create a dedicated worktree
   from the primary checkout's `master` and do all edits there. Every
   worktree lives under the per-user root `~/.worktrees/livespec-runtime/<branch>`.
   Create it with the worktree-discipline pack's recipe, which adds the
   worktree under that root, provisions the gitignored pack into it, and
   runs the hydrate hook (run it from the primary checkout):

   ```bash
   mise exec -- just worktree-create <branch>
   ```

   A raw `mise exec -- git -C /data/projects/livespec-runtime worktree add -b <branch>
   "$HOME/.worktrees/livespec-runtime/<branch>" master` also yields a usable
   worktree — the pre-commit and pre-push hooks install the pack before
   any gate reads it, so the worktree can commit and push with no
   `just bootstrap` — but it skips hydration, so prefer the recipe.

   `just bootstrap` registers `~/.worktrees` as one of mise's
   `trusted_config_paths`, so a freshly created worktree's `.mise.toml`
   is auto-trusted and the first `mise exec` inside it never stalls on a
   "config not trusted" prompt.

3. Use `mise exec -- git commit ...` and `mise exec -- git push ...` so
   the mise-managed lefthook hooks actually run. Never pass
   `--no-verify`; if a hook fails, fix the cause or halt with the
   failure.
4. Open a PR, wait for required checks, and merge through the PR using
   the repo's rebase-merge discipline.
5. After merge, refresh `/data/projects/livespec-runtime` to
   `origin/master`, remove the feature worktree, delete the local
   branch, and verify the primary checkout is clean on `master`.

Do not leave orphaned worktrees. If a session must stop before cleanup,
record the active worktree path, branch, PR, validation state, and next
action in the relevant handoff document.

## Red-Green-Replay commit protocol

Product `.py` changes are committed via a 2-step single-commit TDD ritual,
enforced by the `red_green_replay` commit-refuse hook (it inspects the staged
tree and writes `TDD-*` trailers). The final result is ONE commit carrying the
test, the impl, and both trailer sets.

1. **Red commit.** Stage the test file ALONE — no impl — and commit with a
   `fix:`/`feat:` subject. The hook runs pytest on the staged tree; the staged
   test MUST fail on pytest (non-zero exit). An `ImportError` or a collection
   error counts as a failure to the hook, BUT you SHOULD prefer a genuine
   assertion failure so Red proves the behavior is actually unimplemented
   rather than merely unimportable — see the new-module stub technique below.
   It records `TDD-Red-*` trailers (test path, failure reason, test-file
   checksum, output checksum, captured-at).
   - Gotcha: the impl must be UNMODIFIED on disk at the Red commit, because the
     hook's pytest reads the on-disk module. If the impl already carries the
     change the test passes, and the hook rejects with `test-passed-at-red`.
2. **Green amend.** Stage the impl and run `git commit --amend`. The hook sees
   the `TDD-Red-*` trailers + the staged impl, re-runs the SAME test (now
   passing), and records `TDD-Green-*` trailers. The test file bytes MUST be
   byte-identical across the Red→Green pair; to change the test, author a fresh
   Red commit.

### New-module stub technique (avoiding false reds)

When the impl module under test does NOT exist yet, the natural Red would be an
`ImportError` or a collection error rather than an assertion failure. The hook
accepts that as a failing Red, but it does not prove the behavior is
unimplemented — only that the module is unimportable. To make Red fail on a
genuine assertion instead:

1. At Red time, create the impl module as a minimal **stub** on disk — enough
   that the test imports and runs, but its assertion FAILS (e.g. a function
   that returns a wrong/sentinel value, or raises `NotImplementedError` only
   when that still yields an assertion failure rather than a collection error).
2. The stub must NOT make the test pass — a passing test at Red trips the
   hook's `test-passed-at-red` gate.
3. Then the **Green amend** replaces the stub with the real implementation that
   makes the assertion pass.

This keeps Red honest: it proves the behavior is unimplemented, not merely that
the module is missing.

**Exempt:** changesets with no product `.py` (docs, spec, work-items, shell,
config) use `chore(...)` / `docs(...)` / `chore(spec):` subjects and skip the
ritual entirely. Always use `mise exec -- git ...` so the hooks fire; never
pass `--no-verify`.

## CI runner routing

`CI_RUNNER_LABELS` (a repo variable, never a `.github/workflows/` edit —
`check-no-workflow-edits` forbids that here) routes this repo's gating
`pull_request`/`push` CI matrix. As of 2026-08-17 it points at the ARC k3s
scale set `livespec-runtime-k3s` (livespec-s43svm.16's per-repo real-traffic
cutover), proven by this changeset's own required checks. The podman pool
alternative stays configured but idle for this repo. See
`livespec/plan/fleet-ci-runner-pool/research/k3s-arc-kueue-migration.md`
("Real-traffic cutover log") and the `livespec-s43svm.16` ledger comments for
the full cross-repo cutover record.
