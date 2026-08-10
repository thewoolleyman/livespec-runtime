# Findings — the credential re-exec loop guard is inert

Design of record for `livespec-runtime-acf` (P1, `livespec-runtime` tenant).
Everything below was measured on 2026-08-10, with controls; nothing here is
inferred from reading the code alone.

## The mechanism, in plain terms

Several livespec CLIs need secrets (a database password, GitHub App
credentials). Rather than failing when a secret is missing, they **re-run
themselves** under the project's configured `credential_wrapper`, which is a
program whose job is to inject those secrets and then exec the real command.

That re-run could obviously loop forever, so there is a guard: before
re-running, the code sets an environment variable
`LIVESPEC_CREDENTIAL_REEXEC=1`. If the second attempt sees that variable AND
the secret is still missing, it stops with a clear error instead of re-running
again.

`livespec_runtime/credentials.py` states the assumption the guard rests on:

> A conforming credential wrapper preserves it across the re-exec (the
> reference wrapper strips only `OP_SERVICE_ACCOUNT_TOKEN` + `WRAPPER_STAGE`)

## The finding: no measured wrapper preserves it, including the reference one

The guard variable is carried in the environment — and a credential wrapper's
whole purpose is to *construct* a clean child environment. Measured:

| invocation | `LIVESPEC_CREDENTIAL_REEXEC` | arbitrary canary var |
|---|---|---|
| no wrapper (control) | `1` | `alive` |
| through `/usr/local/bin/with-livespec-env.sh` (the REFERENCE wrapper) | *empty* | *empty* |
| through homelab's `with-homelab-aws.sh …  hl param run …` | *empty* | — |

The canary column is the control that makes this a finding rather than a
guess: an ordinary unrelated variable is dropped too, so the wrapper is
building a fresh environment wholesale, not singling out the sentinel.

**So the documented assumption holds for zero measured wrappers, including the
reference implementation the comment names.** The loop guard has never been
able to fire anywhere in the fleet.

## Why nothing appeared broken until now

The guard is only *reached* when a required secret is still missing after one
hop. Fleet repos inject every required secret, so the second attempt succeeds
and the guard is never consulted. The latent defect only surfaces in a repo
whose wrapper genuinely cannot supply a required secret.

`scripts/bin/dispatcher.py` requires three:

    bootstrap(required=("BEADS_DOLT_PASSWORD", "GITHUB_APP_ID", "GITHUB_PRIVATE_KEY"))

Measured presence per wrapper (byte counts prove non-emptiness; no value was
ever printed):

| wrapper | tenant password | `GITHUB_APP_ID` | `GITHUB_PRIVATE_KEY` |
|---|---|---|---|
| fleet `with-livespec-env.sh` | 29 | 8 | 1649 |
| `with-dolt-server-env.sh` | 29 | 8 | 1680 |
| `with-openbrain-env.sh` | 41 | 8 | 1680 |
| homelab chain | 49 | **0** | **0** |
| `resume` `./with-resume-env.sh` | 46 | 8 | **0** |

## The failure this produces

With a secret unobtainable and the sentinel scrubbed, each attempt re-enters
the decision, sees the secret missing and the sentinel absent, and re-runs
again — unbounded.

Proven against the **pure** decision function with the measured inputs, so this
is a property of the logic and not of any one environment:

    level 1: Reexec      CONTROL, sentinel preserved  -> Fail    (terminates)
    level 2: Reexec      CONTROL, fleet-wrapper env   -> Proceed (the 9 green repos)
    level 3: Reexec
    level 4: Reexec
    level 5: Reexec

### Why it is SILENT, which is the expensive half

Every layer captures its child's output:

- `commands/drive.py:154` runs the dispatcher with
  `subprocess.run(..., capture_output=True)` and **no timeout**;
- `_bootstrap._self_heal_credentials` re-execs with `capture_output=True` too.

So each recursion level swallows the next, and **not one byte reaches stdout**
no matter how long it runs. Observed consequences:

- a **5-hour** silent hang dispatching into `homelab` (2 of 3 secrets absent);
- **three** "killed, no output" dispatches into `resume` (1 absent).

In every case: no work-item claimed, no sandbox started, nothing pushed —
recoverable state, but no diagnosis obtainable from outside the process.

Three prior sessions failed to name this. Each verified the wrapper injected
*its* secret, that the plugin shipped, and that the tenant, item and dispatch
lane were healthy. Every one of those checks was correct and none touched the
layer that was broken.

### How it was finally located, worth reusing

`PYTHONFAULTHANDLER=1` combined with `timeout -s ABRT`. `SIGINT` produced
nothing at all (rc=124, no traceback); `SIGABRT` with faulthandler enabled
dumped the exact blocking frame in one shot:

    selectors.select <- subprocess._communicate <- subprocess.run <- drive.py:154

Reach for that early on any silent hang.

## Design options for the fix

The requirement: carry the "a re-exec already happened" marker somewhere a
credential wrapper **cannot** remove, since removing ambient environment is
precisely what a wrapper is for.

**Option A — carry the marker in `argv` (RECOMMENDED).** Append a sentinel
token to the re-exec command line. A wrapper's contract is to exec the argv it
was handed, so argv survives by construction, whereas the environment is
explicitly rebuilt. `decide_credentials` already receives `argv`, so the pure
decision needs no new input — only a new predicate. Cost: the token becomes
part of the CLI surface and must be tolerated (and stripped) by the entry
points.

**Option B — bounded recursion depth.** Carry an integer depth in argv and
refuse past 1. Strictly more general than A and nearly the same change; useful
as belt-and-braces, not as the primary mechanism.

**Option C — require wrappers to allowlist the variable.** Rejected. It is the
status quo, it depends on every wrapper author including third-party adopters,
and the *reference* wrapper already fails it. A contract no implementation
satisfies is not a contract.

**Option D — infer from process ancestry.** Rejected as fragile and
platform-specific.

Recommendation: **A, with B's depth counter folded in**, so the guard is
independent of wrapper cooperation entirely.

## A second, independent hardening

Even with the loop fixed, `capture_output=True` with no timeout means any
future hang anywhere in the dispatch chain is equally invisible. The loop bug
made a hang possible; the buffering made it undiagnosable. These are separate
defects and either alone is worth fixing:

- give the dispatcher subprocess call a timeout, and/or
- stream the child's output instead of capturing it wholesale.

## What must NOT be done

Do not "fix" this by adding the sentinel to each wrapper's allowlist. That
re-implements Option C per wrapper, leaves every third-party adopter exposed,
and preserves a guard that fails silently and open. The guard must not depend
on the cooperation of the component it is guarding against.
