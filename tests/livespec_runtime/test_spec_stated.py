"""Unit-tier coverage for `livespec_runtime.spec_stated`.

The module is the ONE judgement every orchestrator runs to decide whether a
behaviour is already stated by a ratified livespec specification, so its two
module-wide properties are asserted here rather than at the scenario tier:

- the ratified public surface is importable from THIS one module, which is what
  the module-level public-surface inventory in `SPECIFICATION/contracts.md`
  promises a consumer that renders the shared prompt or persists the shared
  tier fields;
- a model is reached ONLY through the `run_model` callable the caller supplies,
  measured in both directions — the module imports no transport of its own, and
  each public entry point hands its rendered prompt to the injected callable
  exactly once.

The scenario-tier behaviour (the verdict's fields, the classification, and the
parse failures) lives in `tests/consumer/test_spec_stated_judgement.py`, which
`tests/heading-coverage.json` binds to the three ratified scenario headings.

The module is loaded through `importlib` rather than a top-level `import` so
the surface assertion's first measurement is the module FILE existing, which
is what makes the Red of the slice that introduced it a genuine assertion
failure instead of a collection error.
"""

import importlib
import re
from pathlib import Path

from tests.livespec_runtime.test_public_surface_inventory import (
    inventory_findings,
    public_surface_register,
    ratified_inventory_section,
)

__all__: list[str] = []

_MODULE_NAME = "livespec_runtime.spec_stated"
_MODULE_PATH = Path(__file__).resolve().parents[2] / "livespec_runtime" / "spec_stated.py"

# Every name the module-level public-surface inventory in
# `SPECIFICATION/contracts.md` documents for this module, which is also what
# its `__all__` must export: the
# inventory reconciliation reads both directions and the `ratified_unshipped`
# waiver that stood while the section preceded the module is gone.
_RATIFIED_SURFACE = (
    "CLASSIFY_PROMPT",
    "ItemClass",
    "JUDGE_PROMPT",
    "ModelRunner",
    "SpecChangeTier",
    "SpecStatedParseError",
    "SpecStatedVerdict",
    "StatedKind",
    "classify",
    "judge",
    "parse_verdict",
)

# A model transport the module must not import, because the contract confines
# every model reach to the injected `run_model` callable: no subprocess, no
# socket, no HTTP client, and no `os` process-spawn surface either.
_MODEL_TRANSPORTS = frozenset(
    {
        "aiohttp",
        "http",
        "httpx",
        "os",
        "requests",
        "socket",
        "ssl",
        "subprocess",
        "urllib",
    }
)

_SPEC_TREE = {"SPECIFICATION/contracts.md": "## Widgets\n\nA widget MUST be blue.\n"}

# The module name an `import X` / `from X import Y` statement names, at any
# indentation. Read textually rather than through `ast` so the measurement
# carries no arm that a module importing only the `from` form would leave
# unexercised.
_IMPORT_STATEMENT = re.compile(r"^[ \t]*(?:import|from)\s+([A-Za-z_][A-Za-z0-9_.]*)", re.MULTILINE)


class _Runner:
    """A `ModelRunner` stub that records every prompt it is handed.

    `ModelRunner` is `Callable[[str], str]`, so the prompt arrives
    POSITIONALLY; a `__call__` carries that externally-fixed convention
    without a module-level `def` claiming a positional parameter of its own.
    """

    def __init__(self, *, responses: list[str]) -> None:
        self.responses = responses
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.responses[len(self.prompts) - 1]


def _imported_roots(*, source: str) -> frozenset[str]:
    """The top-level module name of every import statement the source carries."""
    return frozenset(name.partition(".")[0] for name in _IMPORT_STATEMENT.findall(source))


def test_the_ratified_public_surface_is_importable_from_the_one_module() -> None:
    """Witness the `contracts.md` public-surface inventory for `spec_stated`.

    The prompt text, the verdict schema and the persisted `spec_change_tier` /
    `linked_proposal_topic` field definitions all come from this one module,
    and the inventory reconciliation agrees in both directions — which is also
    what retires the `ratified_unshipped_modules` row that waived the section
    while it preceded its module.
    """
    assert _MODULE_PATH.is_file(), f"{_MODULE_NAME} must ship as one module at {_MODULE_PATH}"

    module = importlib.import_module(_MODULE_NAME)
    verdict = module.SpecStatedVerdict(
        kind="stated",
        stated_by=("## Widgets",),
        generalization_target=None,
        rationale="the heading states it",
    )
    tier = module.SpecChangeTier(
        tier="spec-change",
        linked_proposal_topic="widget-colour",
        verdict=verdict,
        judged_at="2026-10-21T00:00:00Z",
    )

    assert tuple(sorted(module.__all__)) == tuple(sorted(_RATIFIED_SURFACE))
    assert [name for name in _RATIFIED_SURFACE if not hasattr(module, name)] == []
    assert isinstance(module.JUDGE_PROMPT, str)
    assert isinstance(module.CLASSIFY_PROMPT, str)
    assert verdict.stated_by == ("## Widgets",)
    assert (tier.tier, tier.linked_proposal_topic, tier.judged_at) == (
        "spec-change",
        "widget-colour",
        "2026-10-21T00:00:00Z",
    )
    assert tier.verdict is verdict
    assert (
        inventory_findings(section=ratified_inventory_section(), register=public_surface_register())
        == []
    )


def test_a_model_is_reached_only_through_the_injected_run_model_callable() -> None:
    """Witness the contract's no-model-no-subprocess-no-network clause.

    Measured both ways: the module imports no transport it could reach a model
    with, and each entry point hands its rendered prompt to the injected
    callable exactly once per call — the "at most once per `judge` or
    `classify` call" clause.
    """
    module = importlib.import_module(_MODULE_NAME)
    imported = _imported_roots(source=_MODULE_PATH.read_text(encoding="utf-8"))
    judged = _Runner(responses=["not a verdict"])
    classified = _Runner(responses=["feature"])

    module.judge(spec_tree=_SPEC_TREE, statement="a widget is blue", run_model=judged)
    module.classify(
        title="widgets are blue",
        description="assert the colour",
        item_type="task",
        run_model=classified,
    )

    assert sorted(imported & _MODEL_TRANSPORTS) == []
    assert len(judged.prompts) == 1
    assert len(classified.prompts) == 1
