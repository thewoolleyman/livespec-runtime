"""Reconciles the shrink-only heading-coverage debt register with the live registry.

`tests/heading-coverage-debt.json` is this repository's adoption of charter D3
of the fleet plan `fleet-heading-coverage-convergence` (livespec-dev-tooling
epic `livespec-dev-tooling-0bse`): every `test: "TODO"` row of
`tests/heading-coverage.json` MUST appear in the register, keyed by
`(spec_root, spec_file, heading)` and carrying the owning `work_item` plus the
row's `first_seen` date. A `TODO` is a TRANSITION, and the register is what
gives the fleet's ratchet something to shrink — the only permitted movement is
downward, so the only way to add a cop-out is to resolve one first.

The register is GENERATED mechanically by
`python -m livespec_dev_tooling.heading_coverage_debt`, never authored by hand:
a hand-kept baseline is a list of exemptions, where an author who wants a new
`TODO` accepted simply adds a line. The fleet's own verdict lives in
`livespec_dev_tooling.checks.heading_coverage_debt_register`, which this
repository cannot yet import — its `livespec-dev-tooling` pin is v1.64.1 and
that module arrived later. Until the pin bump lands, nothing in this
repository's own check suite holds the two files together, which is exactly the
window a resolved row could shrink the registry while leaving its register
entry behind.

So this test reads them together, in both directions and against the ratified
schema, with no dependency on the unpinned module:

- every live `TODO` row has a register entry, so a new cop-out cannot arrive
  unregistered;
- every register entry still names a live `TODO` row, so banking a shrink
  nobody made fails rather than quietly leaving room for the next `TODO`;
- no key is entered twice, so "exactly one entry per `TODO` row" is measured
  rather than assumed from a key-set comparison that a duplicate survives;
- every entry carries the key three plus `work_item` and `first_seen`, because
  debt with no owner and no clock is debt the liveness gate and the
  release-tier age bound cannot judge.

It is control-armed, in the manner of this repository's other register
reconciliation (`test_public_surface_inventory.py`): the passing assertion
against the real pair is followed by fabricated drift in each direction, so a
green result is evidence the register describes the registry rather than
evidence the comparison inspected nothing.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__: list[str] = []

_TESTS_ROOT = Path(__file__).resolve().parents[1]
_COVERAGE = _TESTS_ROOT / "heading-coverage.json"
_REGISTER = _TESTS_ROOT / "heading-coverage-debt.json"

_KEY_FIELDS = (
    "spec_root",
    "spec_file",
    "heading",
)
_REQUIRED_FIELDS = (
    *_KEY_FIELDS,
    "work_item",
    "first_seen",
)


def _rows_at(*, path: Path) -> list[dict[str, object]]:
    """The JSON array of objects at `path` — the shape both files declare."""
    return json.loads(path.read_text(encoding="utf-8"))


def _key_of(*, row: dict[str, object]) -> tuple[str, ...]:
    """`row`'s `(spec_root, spec_file, heading)` key, rendered for reporting.

    A row missing one of the three, or carrying a non-string there, keys on the
    empty string for that field rather than being dropped: an unkeyed register
    entry has no live `TODO` row to match, so it is reported as stale instead
    of silently excusing itself from the comparison.
    """
    return tuple(value if isinstance(value := row.get(field), str) else "" for field in _KEY_FIELDS)


def _todo_keys(*, registry_rows: list[dict[str, object]]) -> list[tuple[str, ...]]:
    """The keys of every live `TODO` row — the debt the register must carry."""
    return [_key_of(row=row) for row in registry_rows if row.get("test") == "TODO"]


def _incomplete_fields(*, row: dict[str, object]) -> list[str]:
    """The required fields `row` does not carry as a non-empty string."""
    return [
        field
        for field in _REQUIRED_FIELDS
        if not (isinstance(value := row.get(field), str) and value.strip())
    ]


def _register_findings(
    *, registry_rows: list[dict[str, object]], register_rows: list[dict[str, object]]
) -> list[str]:
    """Every way the register fails to describe `registry_rows`' `TODO` debt, sorted."""
    todo = _todo_keys(registry_rows=registry_rows)
    entered = [_key_of(row=row) for row in register_rows]
    findings = [f"unregistered_todo: {key}" for key in sorted(set(todo) - set(entered))]
    findings += [f"stale_register_entry: {key}" for key in sorted(set(entered) - set(todo))]
    findings += [
        f"duplicate_register_entry: {key}"
        for key in sorted({key for key in entered if entered.count(key) > 1})
    ]
    for row in register_rows:
        missing = _incomplete_fields(row=row)
        if missing:
            findings.append(f"register_row_incomplete: {_key_of(row=row)} missing {missing}")
    return findings


def test_heading_coverage_debt_register_carries_exactly_the_live_todo_rows() -> None:
    """The register holds one complete entry per live `TODO` row, and nothing else.

    Charter D3's adoption assertion, read off the two committed files. The
    control arms below fabricate one drift per direction so the passing
    assertion above cannot be satisfied by a comparison that measured nothing.
    """
    assert _REGISTER.is_file(), f"the debt register is absent: {_REGISTER}"
    registry_rows = _rows_at(path=_COVERAGE)
    register_rows = _rows_at(path=_REGISTER)
    assert (
        _register_findings(registry_rows=registry_rows, register_rows=register_rows) == []
    ), "the heading-coverage debt register no longer describes the live registry"
    assert len(register_rows) == len(_todo_keys(registry_rows=registry_rows))

    # Control arm: a resolved row whose register entry stays behind, and a new
    # `TODO` whose entry was never added, are the two directions the ratchet
    # exists for. Dropping the first entry fabricates both at once.
    assert _register_findings(registry_rows=registry_rows, register_rows=register_rows[1:]) != []

    # Control arm: an entry for a heading no live `TODO` row names is stale.
    phantom: dict[str, object] = {
        "spec_root": "SPECIFICATION",
        "spec_file": "spec.md",
        "heading": "## Heading No Row Names",
        "work_item": "livespec-runtime-l5q",
        "first_seen": "2026-05-28",
    }
    assert (
        _register_findings(registry_rows=registry_rows, register_rows=[*register_rows, phantom])
        != []
    )

    # Control arm: debt with no owner is debt the age bound cannot judge, so an
    # entry missing `work_item` must be convicted even though its key matches.
    ownerless = {field: value for field, value in register_rows[0].items() if field != "work_item"}
    assert (
        _register_findings(
            registry_rows=registry_rows, register_rows=[*register_rows[1:], ownerless]
        )
        != []
    )
