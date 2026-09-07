#!/usr/bin/env python3
"""
backlog drive directive — Claude Code SessionStart hook.

While `plan/runtime-backlog-drain/` exists unarchived, print the drive
directive so it lands in EVERY new session's context, whatever the session
was started for and whatever it remembers. This is the harness layer of the
plan's durability (charter §7): the dev-tooling drive session stalled twice
on 2026-09-06 with the loop rule written only in its charter, so this repo
does not rely on the model recalling it.

Stdlib only. Always exits 0. Prints nothing once the plan directory is gone
or has moved under `plan/archive/`, so the hook retires itself with the plan.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__: list[str] = ["main"]

SLUG = "runtime-backlog-drain-2"


def _project_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(env) if env else Path.cwd()


def main() -> int:
    plan_dir = _project_root() / "plan" / SLUG
    if not plan_dir.is_dir():
        return 0
    anchor = plan_dir / "associated_work_item_id"
    epic = anchor.read_text(encoding="utf-8").strip() if anchor.is_file() else "(anchor missing)"
    _ = sys.stdout.write(
        "\n".join(
            [
                f"## Backlog drive directive (plan `{SLUG}`, epic `{epic}`)",
                "",
                "This repository's open backlog is owned by that plan. Read",
                f"`plan/{SLUG}/research/001-charter-{SLUG}.md` before touching",
                "any work item. Do NOT invoke `/livespec-overseer:foreman` here and",
                "do NOT start a tmux worker session for a work item.",
                "",
                "If this session is the drive session (it was started to work the",
                "backlog, or the user names the plan), then on the FIRST turn:",
                f"  1. `/livespec-orchestrator-beads-fabro:plan {SLUG}` and take the",
                "     epic's typed `next_action`.",
                "  2. Read master CI (cached `gh api`); a red master is the only work",
                "     until it is green.",
                "  3. Run `needs-attention`; put any human-gated valve to the",
                "     maintainer as ONE question.",
                "  4. Act on what is ripe: dispatch through `drive --action impl:<id>`",
                "     or the dispatcher loop; never by hand unless the item carries a",
                "     `factory-exempt:*` label.",
                "  5. Before the turn ends, arm the `/loop` skill (self-paced wakeup)",
                "     or a Monitor. A turn that ends with neither armed is a STALL,",
                "     whatever else it accomplished.",
                "",
                "New work items are admitted only as a child of a snapshot epic, a",
                "`discovered-from:<snapshot-id>` dependency, or a consolidation;",
                "anything else is a PARKING LOT comment on the epic.",
                "",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
