"""This repository's committed factory table names a factory, never a machine.

Witnesses `SPECIFICATION/constraints.md` section "Factory routing" (v028).
`dispatcher.factories` used to carry a `server` per entry, which binds each
factory to a MACHINE: moving one is then a commit, a release and a plugin
refresh in every governed repository, for a fact the fleet's provisioning
inventory already holds. The registry-backed form moves both addresses — the
Fabro server url and the sandbox Docker daemon — into host state rendered at
`/etc/livespec/fabro-factories.json`, so a committed entry names only the
factory and the move is a provisioning change touching no tracked file here.

These are a LINT over whatever this repository commits: they read the real
block and assert a property of it rather than pinning a value a fixture could
have supplied. The registry-backing assertion is the durable one — it is what
keeps a hostname from reappearing in a tracked file, and it holds however many
entries the table grows. The naming assertions are narrower by design: the
entry name is what the control node's rendered registry cross-references, so a
rename that leaves it behind is a configuration fault this suite should report
rather than a dispatch should discover.

The lint carries its own FAIL-CAPABILITY arm. A reader that silently returned
an empty table would make every assertion here pass vacuously, which is worse
than no lint at all, so the registry-backing property is factored into a
predicate and driven to conviction against a fabricated hostname-bearing table
parsed through the same two helpers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final, cast

__all__: list[str] = []

_REPO_ROOT: Final = Path(__file__).resolve().parents[2]
_CONFIG_NAME: Final = ".livespec.jsonc"
# `"registry": true` is the ratified spelling, and the predicate below tests
# for that VALUE rather than for the key's presence: any other value leaves
# the entry non-registry-backed, where a committed `server` decides as it did
# before — still the supported form for an adopter outside this fleet.
_REGISTRY_KEY: Final = "registry"
# The address keys a registry-backed entry may not also carry. Each names an
# address the registry is the source of, so an entry declaring one has two
# answers and no rule for choosing between them.
_COMMITTED_ADDRESS_KEYS: Final = ("server", "docker_host")


def _strip_line_comments(*, text: str) -> str:
    """Drop `//` line comments from JSONC text, respecting string literals.

    A naive cut at the first `//` would truncate every `https://` value this
    repository commits under `cross_repo_targets`, so the scan tracks whether
    it is inside a string literal and cuts only outside one. Block comments
    are deliberately NOT handled: this file commits none, and a `/* ... */`
    added later surfaces as a loud `json.JSONDecodeError` rather than as a
    silently wrong parse.
    """
    kept: list[str] = []
    for line in text.splitlines():
        in_string = False
        escaped = False
        cut = len(line)
        for index, char in enumerate(line):
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = not in_string
            elif char == "/" and not in_string and line[index + 1 : index + 2] == "/":
                cut = index
                break
        kept.append(line[:cut])
    return "\n".join(kept)


def _dispatcher_block(*, text: str) -> dict[str, Any]:
    """Parse JSONC `text` down to its `dispatcher` block.

    The `cast` is the single typed parse boundary, as every other
    `.livespec.jsonc` reader in this fleet spells it: `json.loads` returns
    `Any`, and the committed shape is asserted by the tests below rather than
    by a schema this lint would have to carry and keep in step.
    """
    parsed = cast(dict[str, Any], json.loads(_strip_line_comments(text=text)))
    return cast(dict[str, Any], parsed["livespec-orchestrator-beads-fabro"]["dispatcher"])


def _committed_dispatcher_block() -> dict[str, Any]:
    return _dispatcher_block(text=(_REPO_ROOT / _CONFIG_NAME).read_text(encoding="utf-8"))


def _factories(*, dispatcher: dict[str, Any]) -> dict[str, Any]:
    return cast(dict[str, Any], dispatcher["factories"])


def _registry_backing_faults(*, factories: dict[str, Any]) -> list[tuple[str, str]]:
    """Return one `(entry name, fault)` pair per entry that names a machine."""
    faults: list[tuple[str, str]] = []
    for name, entry in sorted(factories.items()):
        if cast(dict[str, Any], entry).get(_REGISTRY_KEY) is not True:
            faults.append((name, f'{_REGISTRY_KEY} is not the literal "true"'))
        faults.extend((name, f"declares {key}") for key in _COMMITTED_ADDRESS_KEYS if key in entry)
    return faults


def test_the_committed_table_declares_exactly_one_entry_named_legacy() -> None:
    """One live instance, named for the factory and not for its host.

    `legacy` is the name the control node's rendered registry declares for the
    instance this repository has always dispatched to, so routing is unchanged
    by the switch. A committed entry whose name that file does not declare
    resolves to no address at all, which is refused before the item is claimed
    rather than quietly sent to whichever Fabro the dispatching host runs.
    """
    assert sorted(_factories(dispatcher=_committed_dispatcher_block())) == ["legacy"]


def test_every_committed_entry_is_registry_backed_and_names_no_machine() -> None:
    """The durable invariant: no tracked file here holds a factory's address.

    Asserted over EVERY entry rather than over the one named above, so an
    entry added later cannot reintroduce a committed hostname without this
    failing.
    """
    faults = _registry_backing_faults(
        factories=_factories(dispatcher=_committed_dispatcher_block())
    )

    assert faults == []


def test_the_committed_default_factory_names_a_registry_backed_entry() -> None:
    """`legacy` is the default, and it is an entry the table actually declares.

    The second half is what makes the first worth asserting: a default naming
    no declared entry refuses every dispatch from this repository, and nothing
    about the key's own value says whether it does.
    """
    dispatcher = _committed_dispatcher_block()

    assert dispatcher["default_factory"] == "legacy"
    assert dispatcher["default_factory"] in _factories(dispatcher=dispatcher)


def test_the_lint_convicts_a_fabricated_hostname_bearing_table() -> None:
    """FAIL-CAPABILITY arm: a green result above is evidence, not silence.

    Drives the same stripper and the same predicate against the hostname-
    bearing shape this repository committed before the switch. It also pins
    the stripper's load-bearing behavior — the `https://` inside a string
    literal survives, the full-line `//` comment does not — because a stripper
    that truncated at the first slash would reduce the committed read above to
    a parse error nobody reads as a routing fault.
    """
    fabricated = _dispatcher_block(
        text="""{
  // A full-line comment, exactly as the committed file spells one.
  "livespec-orchestrator-beads-fabro": {
    "dispatcher": {
      "factories": {
        "hp": { "server": "https://hp-xubuntu.example.invalid:32276" }
      },
      "default_factory": "hp"
    }
  }
}
""",
    )
    factories = _factories(dispatcher=fabricated)

    assert factories["hp"]["server"] == "https://hp-xubuntu.example.invalid:32276"
    assert _registry_backing_faults(factories=factories) == [
        ("hp", 'registry is not the literal "true"'),
        ("hp", "declares server"),
    ]


def test_the_stripper_tracks_an_escaped_quote_rather_than_closing_the_string() -> None:
    """A `\\"` inside a string literal does not end it, so a later `//` is data.

    The escape arm is the one part of the stripper the committed file does not
    currently exercise — it commits no escaped quote — and leaving it
    unexercised would mean the first value that carries one gets truncated
    mid-string, surfacing as a parse error that names nothing about routing.
    The second assertion keeps the arm honest in the other direction: a real
    comment OUTSIDE any string is still cut.
    """
    stripped = _strip_line_comments(text=r'{"note": "a \" and then // stays"} // cut here')

    assert stripped == r'{"note": "a \" and then // stays"} '
    assert "cut here" not in stripped
