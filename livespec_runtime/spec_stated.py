"""The shared judgement of whether a behaviour is stated by the ratified spec.

A SHARED-RUNTIME contract: `livespec` core names no slot for this judgement, and
both consuming producers — `livespec-orchestrator-beads-fabro` and
`livespec-orchestrator-git-jsonl` — run the SAME one. Defining it once is the
whole point: the prompt, the inputs, the verdict schema, the parser and the
persisted tier fields all live here, so two orchestrators cannot drift into two
different judgements of the same question.

The module reaches a model ONLY through the `run_model` callable its caller
supplies. It opens no subprocess, no socket and no network connection of its
own and holds no credential, so the library stays model-agnostic and every
provider binding — and every secret — stays in the consumer.

Two points the ratified contract leaves open, decided here and NOT invented
into validation:

- `generalization_target` is validated as a string or `None`, not as a heading
  present in the spec tree. Only `stated_by` is pinned to the tree by
  `contracts.md`, so refusing a target the ratified text does not refuse would
  make this parser stricter than the contract it implements.
- a `kind`/`stated_by` disagreement (an `unstated` verdict naming a heading, a
  `stated` one naming none) is carried through rather than refused, for the
  same reason: `contracts.md` describes `stated_by` as empty for `unstated`
  without making that a requirement the parser may enforce.

Both are reported to the maintainer as underspecification findings rather than
closed by this module's own reading.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from typing import Literal, TypeAlias

from returns.result import Failure, Result

__all__: list[str] = [
    "CLASSIFY_PROMPT",
    "JUDGE_PROMPT",
    "ItemClass",
    "ModelRunner",
    "SpecChangeTier",
    "SpecStatedParseError",
    "SpecStatedVerdict",
    "StatedKind",
    "classify",
    "judge",
    "parse_verdict",
]

StatedKind: TypeAlias = Literal["stated", "partial", "unstated"]
ItemClass: TypeAlias = Literal["feature", "bug", "chore", "non_functional"]
ModelRunner: TypeAlias = Callable[[str], str]

JUDGE_PROMPT: str = """You are judging ONE behaviour statement against a RATIFIED specification.

The specification tree follows, one block per file:

{spec_tree}

The behaviour statement under judgement:

{statement}

Decide whether the ratified text above STATES that behaviour, and name the
clause that states it. Reply with ONE JSON object and nothing else:

{{"kind": "stated" | "partial" | "unstated",
  "stated_by": ["## Verbatim H2 heading", "..."],
  "generalization_target": "## Verbatim H2 heading" or null,
  "rationale": "one or two sentences"}}

Rules:

- "stated" means the ratified text states the behaviour in full; "partial"
  means it states part of it; "unstated" means it does not state it.
- "stated_by" names EVERY governing H2 heading, VERBATIM and including its
  leading "## " marker, copied from the tree above. It is empty for "unstated".
- Name no heading that is absent from the tree above: an invented heading is
  refused rather than parsed.
- "generalization_target" names the one EXISTING H2 heading whose
  generalization would state the behaviour, or is null when none would.
"""

CLASSIFY_PROMPT: str = """Classify ONE work item into exactly one class.

Title: {title}

Description: {description}

Stored type, as EVIDENCE only: {item_type}

The stored type is whatever a human or an orchestrator happened to record, so
it is evidence ABOUT the item and never the answer. Weigh it against the title
and the description, and disagree with it when they say otherwise.

Reply with exactly one of these four words and nothing else:

feature — new observable behaviour.
bug — behaviour that contradicts what is already stated.
chore — work that changes no observable behaviour.
non_functional — a constraint on HOW the system behaves rather than on what it
does.
"""


@dataclass(frozen=True, slots=True, kw_only=True)
class SpecStatedVerdict:
    """One judgement: whether the spec states a behaviour, and by which clause.

    `stated_by` carries the verbatim text of each governing H2 heading, its
    leading `## ` marker included, and is empty for an `unstated` verdict.
    `generalization_target` names the one existing heading whose generalization
    would state the behaviour, or is `None`.
    """

    kind: StatedKind
    stated_by: tuple[str, ...]
    generalization_target: str | None
    rationale: str


@dataclass(frozen=True, slots=True, kw_only=True)
class SpecChangeTier:
    """The spec-change tier both orchestrators persist on a work-item.

    `tier` and `linked_proposal_topic` are the two persisted fields a consumer
    stores; `verdict` keeps the judgement they were derived from, and
    `judged_at` is an ISO-8601 UTC timestamp.
    """

    tier: Literal["spec-change", "none"]
    linked_proposal_topic: str | None
    verdict: SpecStatedVerdict | None
    judged_at: str


class SpecStatedParseError(Exception):
    """A model response this module could not read as a judgement.

    Returned as the `Failure` payload of `judge`, `classify` and
    `parse_verdict` — never raised. Inherits `Exception` directly: consumers
    catch this domain type, never a builtin ancestor.

    `field` names the offending JSON field, and is `None` when the response is
    not JSON at all.
    """

    def __init__(self, *, field: str | None, detail: str) -> None:
        super().__init__(detail)
        self.field = field
        self.detail = detail


def _rendered_spec_tree(*, spec_tree: Mapping[str, str]) -> str:
    """The spec tree rendered into the prompt: one block per path, in path order."""
    return "\n\n".join(f"--- {path} ---\n{spec_tree[path]}" for path in sorted(spec_tree))


def parse_verdict(
    *, text: str, headings: Collection[str]
) -> Result[SpecStatedVerdict, SpecStatedParseError]:
    """Parse one raw model response into a verdict over the headings the tree carries.

    This slice opens the surface and recognizes NO response yet; the typed
    verdict and the per-field failures land with the parse itself.
    """
    return Failure(
        SpecStatedParseError(
            field=None,
            detail=(
                f"no verdict is recognized yet: {len(text)} characters of response "
                f"against {len(headings)} headings"
            ),
        )
    )


def judge(
    *, spec_tree: Mapping[str, str], statement: str, run_model: ModelRunner
) -> Result[SpecStatedVerdict, SpecStatedParseError]:
    """Judge whether `spec_tree` states `statement`, and by which clause.

    `spec_tree` maps each spec-tree-relative file path to its text. The model
    is reached exactly once, through `run_model`, with `JUDGE_PROMPT` rendered
    over the tree and the statement.

    The heading set the verdict is validated against is empty in this slice;
    deriving it from `spec_tree` lands with the verdict parse.
    """
    prompt = JUDGE_PROMPT.format(
        spec_tree=_rendered_spec_tree(spec_tree=spec_tree), statement=statement
    )
    return parse_verdict(text=run_model(prompt), headings=())


def classify(
    *, title: str, description: str, item_type: str, run_model: ModelRunner
) -> Result[ItemClass, SpecStatedParseError]:
    """Classify one work item, treating `item_type` as evidence and not as the answer.

    `item_type` is the stored type: it is rendered into the prompt as evidence
    about the item, and the class returned is the model's own reading of the
    title and the description. The model is reached exactly once, through
    `run_model`.

    The failure carries `field` `None` because a classification response is one
    bare word rather than a JSON object, so there is no field to name.

    This slice recognizes no answer yet; the four-member vocabulary lands with
    the classification itself.
    """
    prompt = CLASSIFY_PROMPT.format(title=title, description=description, item_type=item_type)
    answer = run_model(prompt).strip()
    return Failure(
        SpecStatedParseError(field=None, detail=f"no item class is recognized yet: {answer!r}")
    )
