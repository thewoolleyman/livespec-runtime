"""Reconciles the shipped `__all__` surface with the ratified public-surface inventory.

`SPECIFICATION/constraints.md`, section "Public-surface constraints", ratifies
that the symbols enumerated in `SPECIFICATION/contracts.md`, section
"Module-level public surface", are the entire v1 stable API.
`SPECIFICATION/spec.md`, section "Public surface", records the shipped module
families that sit outside that inventory as ACKNOWLEDGED DEBT rather than as
implementation detail. Nothing mechanical held prose and code together, so the
inventory drifted from the exported set by 70 names before work-item
livespec-runtime-mqsxsu.4; the drift was invisible because it lived between a
markdown file and 34 `__all__` lists that no check read together.

These tests read them together, in both directions:

- every module that exports names is either RATIFIED (it has a `###` section in
  the inventory, and then every name it exports must appear there) or
  REGISTERED as debt in `tests/public-surface-debt.json`;
- every registered row still describes the tree, so the register can only
  shrink: ratifying a module, declaring it internal, or dropping its `__all__`
  makes its row stale and fails until the row is deleted;
- every `###` section in the inventory still resolves to a shipped module, so a
  deleted or renamed module cannot leave a phantom entry behind;
- every NAME a ratified section documents in a bullet's leading position is
  exported by that module, or by a module the section names, so a phantom NAME
  — documented, never shipped, or shipped once and since removed — cannot sit
  in the inventory unnoticed either;
- the verbatim third-party ports that sit outside the first-party structural
  universe are declared WITH the names they take out of scope, so that
  exclusion is visible in the register rather than silent in the walker.

MEASUREMENT — a name counts as documented when it appears as a WHOLE WORD
anywhere in the inventory section. Searching for the BACKTICKED BARE NAME is
the wrong measurement and manufactures roughly 44 phantom findings: the
inventory backticks full signatures, so `lane_of` is written
``lane_of(*, item, ...)`` and never matches ``lane_of``. Anyone re-measuring
this gap must use the word-boundary form.

HONEST LIMIT — a whole-word match over the section can over-credit a name that
is also an ordinary word of the surrounding prose (`main`, `run`, `git`). That
is why the module-level obligation is separate and comes first: a module with
no ratified section owes a register row no matter how its names happen to
spell, which is what keeps launcher entry points from riding in on a prose
word. Within a ratified section the residual over-credit is accepted; the
alternative, matching each name only inside its own module's subsection, would
report every re-export of an already-documented name as an omission.

REVERSE MEASUREMENT — the name-level reverse leg reads only the BULLET-LEADING
backticked identifiers of a section, never every backticked token in it.
Running the forward direction's tolerant match backwards would manufacture
findings out of prose words, signature fragments, and referenced type names
(`Literal`, `TypeAlias`, `Exception`), none of which the section is claiming
this module exports. A bullet whose leading token names a shipped MODULE — the
support-module and ported-module bullets — documents a module rather than a
name and is skipped; `###`-level module claims are already asserted by
`test_every_ratified_module_section_resolves_to_a_shipped_module`. The
residual latitude is the re-export allowance: a name may be satisfied by the
`__all__` of ANY shipped module the section backticks by dotted path, which is
how a facade section (`hygiene_scan`, `github_budget`) credits the support
modules it re-exports from, and it does not distinguish those from a module the
section merely mentions.
"""

import ast
import json
import re
from pathlib import Path

__all__: list[str] = []

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME_ROOT = _REPO_ROOT / "livespec_runtime"
_CONTRACTS = _REPO_ROOT / "SPECIFICATION" / "contracts.md"
_REGISTER = _REPO_ROOT / "tests" / "public-surface-debt.json"
_INVENTORY_HEADING = "## Module-level public surface"
_GENERATED_MARKER = "# @generated"
_SECTION_SPLIT = re.compile(r"^### `([A-Za-z0-9_.]+)`\n", re.MULTILINE)
_BULLET_HEAD = re.compile(r"^- ((?:`[^`]+`(?:,\s+)?)+)", re.MULTILINE)
_LEADING_IDENTIFIER = re.compile(r"`([A-Za-z_][A-Za-z0-9_.]*)")
_DOTTED_TOKEN = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+)`")


def _inventory_section() -> str:
    """The body of the ratified inventory, up to the next top-level heading."""
    contracts = _CONTRACTS.read_text(encoding="utf-8")
    start = contracts.index(_INVENTORY_HEADING)
    end = contracts.index("\n## ", start + len(_INVENTORY_HEADING))
    return contracts[start:end]


def _documented_names(*, section: str) -> frozenset[str]:
    return frozenset(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", section))


def _documented_modules(*, section: str) -> frozenset[str]:
    return frozenset(re.findall(r"^### `([A-Za-z0-9_.]+)`", section, re.MULTILINE))


def _exported_names(*, source: str) -> tuple[str, ...]:
    """The module-top `__all__` entries, or an empty tuple when there are none."""
    return tuple(
        element.value
        for node in ast.parse(source).body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "__all__"
        and isinstance(node.value, ast.List)
        for element in node.value.elts
        if isinstance(element, ast.Constant) and isinstance(element.value, str)
    )


def _module_name(*, path: Path) -> str:
    return path.relative_to(_REPO_ROOT).with_suffix("").as_posix().replace("/", ".")


def _exporting_modules() -> dict[str, tuple[str, ...]]:
    """Every first-party runtime module that declares a non-empty `__all__`.

    Verbatim third-party ports are excluded here and asserted separately: they
    carry the `# @generated` marker that drops them from the first-party
    structural universe every other check walks, so their upstream `__all__` is
    not a declaration of this library's surface.
    """
    exporting: dict[str, tuple[str, ...]] = {}
    for path in sorted(_RUNTIME_ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        if _GENERATED_MARKER in source:
            continue
        names = _exported_names(source=source)
        if names:
            exporting[_module_name(path=path)] = names
    return exporting


def _register() -> dict[str, list[dict[str, object]]]:
    return json.loads(_REGISTER.read_text(encoding="utf-8"))


def _registered_modules() -> frozenset[str]:
    return frozenset(str(row["module"]) for row in _register()["unratified_modules"])


def _unaccounted_exports(
    *,
    exporting: dict[str, tuple[str, ...]],
    ratified_modules: frozenset[str],
    documented: frozenset[str],
    registered: frozenset[str],
) -> list[str]:
    """Exports that are neither in the ratified inventory nor registered as debt.

    A RATIFIED module owes every name it exports to its own inventory; each
    shortfall is reported dotted. An unratified module owes a register row;
    that shortfall is reported bare, because the module — not any one name — is
    what has to be ratified, declared internal, or recorded.
    """
    unaccounted: list[str] = []
    for module, names in exporting.items():
        if module in ratified_modules:
            unaccounted += [f"{module}.{name}" for name in names if name not in documented]
        elif module not in registered:
            unaccounted.append(module)
    return unaccounted


def _stale_register_rows(
    *,
    registered: frozenset[str],
    exporting: dict[str, tuple[str, ...]],
    ratified_modules: frozenset[str],
) -> list[str]:
    """Register rows that no longer describe the tree, which is what makes it shrink-only."""
    stale: list[str] = []
    for module in sorted(registered):
        if module not in exporting:
            stale.append(f"{module}: no longer exports anything (delete the row)")
        elif module in ratified_modules:
            stale.append(f"{module}: now ratified in contracts.md (delete the row)")
    return stale


def _sections(*, section: str) -> dict[str, str]:
    """Each ratified `###` module section of the inventory, mapped to its own body."""
    parts = _SECTION_SPLIT.split(section)
    return dict(zip(parts[1::2], parts[2::2], strict=True))


def _shipped_modules() -> frozenset[str]:
    """Every module the runtime package ships, dotted from the repo root."""
    return frozenset(_module_name(path=path) for path in _RUNTIME_ROOT.rglob("*.py"))


def _bullet_leading_names(*, body: str) -> tuple[str, ...]:
    """The identifiers a section CLAIMS, read from each bullet's leading backticked run.

    Only the run at the head of the bullet counts, so ``- `a`, `b` — uses
    `Literal``` claims `a` and `b` and not `Literal`. Signatures are truncated
    at the first non-identifier character, which is what turns the inventory's
    ``lane_of(*, item, ...)`` into the bare `lane_of` a module can export.
    """
    return tuple(
        name for head in _BULLET_HEAD.findall(body) for name in _LEADING_IDENTIFIER.findall(head)
    )


def _resolve_module(*, token: str, section_module: str, shipped: frozenset[str]) -> str | None:
    """The shipped module a backticked token names, or None when it names no module.

    The inventory writes module references three ways — fully dotted, relative
    to the runtime package, and bare relative to the section's own package (the
    `_fractional_indexing` port) — so all three are tried.
    """
    package = section_module.rpartition(".")[0]
    for candidate in (token, f"livespec_runtime.{token}", f"{package}.{token}"):
        if candidate in shipped:
            return candidate
    return None


def _sibling_exports(
    *,
    body: str,
    section_module: str,
    exporting: dict[str, tuple[str, ...]],
    shipped: frozenset[str],
) -> frozenset[str]:
    """What the modules a section backticks by dotted path export, for the re-export leg."""
    resolved = (
        _resolve_module(token=token, section_module=section_module, shipped=shipped)
        for token in _DOTTED_TOKEN.findall(body)
    )
    return frozenset(
        name for module in resolved if module is not None for name in exporting.get(module, ())
    )


def _phantom_documented_names(
    *,
    sections: dict[str, str],
    exporting: dict[str, tuple[str, ...]],
    shipped: frozenset[str],
) -> list[str]:
    """Names a ratified section documents that no module it names actually exports.

    This is the reverse of `_unaccounted_exports`: that one walks `__all__` and
    asks the inventory, this one walks the inventory and asks `__all__`.
    """
    phantom: list[str] = []
    for module, body in sections.items():
        exported = frozenset(exporting.get(module, ())) | _sibling_exports(
            body=body, section_module=module, exporting=exporting, shipped=shipped
        )
        for name in _bullet_leading_names(body=body):
            if _resolve_module(token=name, section_module=module, shipped=shipped) is not None:
                continue
            if name not in exported:
                phantom.append(f"{module}.{name}")
    return sorted(set(phantom))


def _phantom_in_inventory(*, section: str) -> list[str]:
    """The reverse leg measured against the shipped tree."""
    return _phantom_documented_names(
        sections=_sections(section=section),
        exporting=_exporting_modules(),
        shipped=_shipped_modules(),
    )


def test_every_exported_name_is_ratified_or_its_module_is_registered_as_debt() -> None:
    section = _inventory_section()
    unaccounted = _unaccounted_exports(
        exporting=_exporting_modules(),
        ratified_modules=_documented_modules(section=section),
        documented=_documented_names(section=section),
        registered=_registered_modules(),
    )

    assert unaccounted == [], (
        "these exports are neither in the ratified inventory nor registered as debt: "
        f"{unaccounted}. A bare module name means the module has no `###` section in "
        "contracts.md: ratify it, declare it internal, or add a row to "
        "tests/public-surface-debt.json. A dotted name means a RATIFIED module exports "
        "something its own section omits: document it, or drop it from `__all__`."
    )


def test_the_debt_register_carries_no_stale_rows() -> None:
    """A row must still describe the tree, so the register can only shrink."""
    stale = _stale_register_rows(
        registered=_registered_modules(),
        exporting=_exporting_modules(),
        ratified_modules=_documented_modules(section=_inventory_section()),
    )

    assert stale == [], f"stale debt-register rows: {stale}"


def test_the_reconciliation_names_both_shapes_of_drift() -> None:
    """The failure paths, against a synthetic tree — a conformant repo never walks them.

    Without this, the two clauses that make the check load-bearing are asserted
    only by the absence of a failure, which is exactly how a check rots into a
    vacuous pass.
    """
    unaccounted = _unaccounted_exports(
        exporting={
            "ratified": ("Documented", "Undocumented"),
            "unregistered": ("Whatever",),
            "registered": ("Whatever",),
        },
        ratified_modules=frozenset({"ratified"}),
        documented=frozenset({"Documented"}),
        registered=frozenset({"registered"}),
    )

    assert unaccounted == ["ratified.Undocumented", "unregistered"]


def test_a_register_row_goes_stale_when_it_stops_describing_the_tree() -> None:
    """Ratifying a module or dropping its `__all__` obliges deleting its row."""
    stale = _stale_register_rows(
        registered=frozenset({"gone", "now_ratified", "still_debt"}),
        exporting={"now_ratified": ("A",), "still_debt": ("B",)},
        ratified_modules=frozenset({"now_ratified"}),
    )

    assert stale == [
        "gone: no longer exports anything (delete the row)",
        "now_ratified: now ratified in contracts.md (delete the row)",
    ]


def test_every_ratified_module_section_resolves_to_a_shipped_module() -> None:
    """The inventory must not carry a section for a module that no longer ships."""
    phantom = [
        module
        for module in sorted(_documented_modules(section=_inventory_section()))
        if not (_REPO_ROOT / f"{module.replace('.', '/')}.py").is_file()
    ]

    assert phantom == [], (
        f"contracts.md documents modules that do not ship: {phantom}. "
        "Removing or renaming a module is a major-version change; the inventory "
        "section must move with it."
    )


def test_every_documented_name_is_exported_by_a_module_its_section_names() -> None:
    """The reverse of the forward leg: the inventory may not document a phantom name."""
    phantom = _phantom_in_inventory(section=_inventory_section())

    assert phantom == [], (
        f"contracts.md documents names that no module exports: {phantom}. Each is "
        "reported as `<ratified section>.<name>`. A name that was never shipped, or "
        "that has since been dropped from an `__all__`, must leave the inventory with "
        "it; removing a shipped name is a major-version change per spec.md "
        '§"Public surface".'
    )


def test_a_phantom_bullet_injected_into_a_ratified_section_is_reported() -> None:
    """Fail-capability, against the REAL inventory text — the check is not vacuous.

    The positive control above passes only because the tree carries no phantom
    today, which is indistinguishable from a check that can never go red. This
    injects one bullet into a real ratified section and demands the finding.
    Measuring the DIFFERENCE against the un-injected text keeps this a proof of
    fail-capability alone: a real phantom appearing in the tree is the positive
    control's failure to report, not this one's.
    """
    section = _inventory_section()
    heading = "### `livespec_runtime.cross_repo.retry`\n"
    injected = section.replace(
        heading, f"{heading}\n- `never_shipped_by_anything` — a name the tree never had.\n", 1
    )

    caused = set(_phantom_in_inventory(section=injected)) - set(
        _phantom_in_inventory(section=section)
    )

    assert caused == {"livespec_runtime.cross_repo.retry.never_shipped_by_anything"}


def test_the_reverse_leg_credits_re_exports_and_skips_module_bullets() -> None:
    """The two latitudes the measurement grants, against a synthetic inventory.

    A facade section documents names its support modules export, and a bullet
    that leads with a module name documents a module rather than a name; both
    are silent on the real tree, so only a synthetic section walks them.
    """
    phantom = _phantom_documented_names(
        sections={
            "pkg.facade": (
                "- `Reexported`, `Missing` — one lives in `pkg.support`, one nowhere.\n"
                "- `pkg.support` — the support module, named not exported.\n"
                "- prose bullets and `Literal` mentions are not claims.\n"
            ),
            "pkg.support": "- `Reexported` — defined here.",
        },
        exporting={"pkg.support": ("Reexported",)},
        shipped=frozenset({"pkg.facade", "pkg.support"}),
    )

    assert phantom == ["pkg.facade.Missing"]


def test_generated_ports_declare_the_names_they_take_out_of_scope() -> None:
    """The one exclusion the walker applies is enumerated, never silent."""
    on_disk = {
        path.relative_to(_REPO_ROOT).as_posix(): list(
            _exported_names(source=path.read_text(encoding="utf-8"))
        )
        for path in sorted(_RUNTIME_ROOT.rglob("*.py"))
        if _GENERATED_MARKER in path.read_text(encoding="utf-8")
    }
    declared = {str(row["path"]): row["names"] for row in _register()["generated_ports"]}

    assert on_disk == declared, (
        "the `# @generated` verbatim ports on disk disagree with "
        "tests/public-surface-debt.json. Re-vendoring that changes a port's `__all__` "
        "must restate which names it takes out of the public-surface reconciliation."
    )
