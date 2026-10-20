"""The ratified-section-ahead-of-its-module waiver, driven over the REAL inventory.

Binds the `SPECIFICATION/scenarios.md` scenario that a ratified section may
precede its module only while a live owner is registered, ratified as v026 by
proposal `ratified-unshipped-module-register`. The consumer here is the
repository's own public-surface reconciliation: its Given is an inventory plus a
register payload, and its four Then/And lines are four findings-list outcomes,
so this tier drives `inventory_findings` — the one composed entry point
`tests/livespec_runtime/test_public_surface_inventory.py` publishes — and never
reaches into the individual legs that module's own tests assert one at a time.

The inventory is the REAL `contracts.md` section with ONE synthetic `###`
section appended, rather than a wholly synthetic one, so every clause is
measured against the inventory the repository actually ships: a waiver that
silenced a real finding, or a real finding that the appended section masked,
would show up here as a non-empty baseline. The appended module is deliberately
one the tree does not contain, which is the only way to pose a section whose
module does not ship without deleting a shipped one.
"""

from tests.livespec_runtime.test_public_surface_inventory import (
    inventory_findings,
    public_surface_register,
    ratified_inventory_section,
)

__all__: list[str] = []

_UNSHIPPED = "livespec_runtime.ratified_before_it_ships"
_UNEXPORTED = ("NothingExportsThisYet", "nothing_exports_this_either")
_OWNER = "livespec-runtime-krpzzb"
_SHIPPED = "livespec_runtime.cross_repo.retry"
_OTHER_SECTION = f"### `{_SHIPPED}`\n"
_PHANTOM_IN_OTHER_SECTION = "never_shipped_by_anything"


def _inventory_with_an_unshipped_section() -> str:
    """The shipped inventory plus one ratified section whose module does not exist.

    The section documents TWO names so the no-row leg is measured against
    EVERY name it documents rather than against a single one, which a
    first-finding-wins implementation would also satisfy.
    """
    bullets = "".join(
        f"- `{name}(*, item)` — ratified ahead of the module that will export it.\n"
        for name in _UNEXPORTED
    )
    return f"{ratified_inventory_section()}\n### `{_UNSHIPPED}`\n\n{bullets}"


def _register_waiving(*, modules: list[str]) -> dict[str, list[dict[str, object]]]:
    """The shipped register with its `ratified_unshipped_modules` list replaced."""
    register = public_surface_register()
    register["ratified_unshipped_modules"] = [
        {"module": module, "work_item": _OWNER} for module in modules
    ]
    return register


def test_a_ratified_section_may_precede_its_module_only_while_a_live_owner_is_registered() -> None:
    unwaived_inventory = _inventory_with_an_unshipped_section()

    baseline = inventory_findings(
        section=ratified_inventory_section(), register=public_surface_register()
    )
    waived = inventory_findings(
        section=unwaived_inventory, register=_register_waiving(modules=[_UNSHIPPED])
    )
    unregistered = inventory_findings(
        section=unwaived_inventory, register=_register_waiving(modules=[])
    )
    stale = inventory_findings(
        section=ratified_inventory_section(), register=_register_waiving(modules=[_SHIPPED])
    )
    elsewhere = inventory_findings(
        section=unwaived_inventory.replace(
            _OTHER_SECTION,
            f"{_OTHER_SECTION}\n- `{_PHANTOM_IN_OTHER_SECTION}` — a name the tree never had.\n",
            1,
        ),
        register=_register_waiving(modules=[_UNSHIPPED]),
    )

    assert (
        baseline == []
    ), f"the shipped tree must reconcile before anything is injected: {baseline}"
    assert waived == [], (
        "a ratified section whose module does not ship must be waived while a "
        f"ratified_unshipped_modules row names it and an owner, but got: {waived}"
    )
    assert unregistered == sorted(
        [f"phantom name: {_UNSHIPPED}.{name}" for name in _UNEXPORTED]
        + [f"phantom section: {_UNSHIPPED}"]
    )
    assert stale == [f"stale unshipped row: {_SHIPPED}: now ships (delete the row)"]
    assert elsewhere == [f"phantom name: {_SHIPPED}.{_PHANTOM_IN_OTHER_SECTION}"]
