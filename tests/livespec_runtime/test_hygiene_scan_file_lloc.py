"""Regression coverage for hygiene-scan module file length."""

import ast
import tokenize
from io import BytesIO
from pathlib import Path

__all__: list[str] = []

_HARD_CEILING = 250
_NON_LLOC_TOKEN_TYPES = frozenset(
    {
        tokenize.COMMENT,
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENCODING,
        tokenize.ENDMARKER,
    }
)


def test_hygiene_scan_runtime_modules_stay_under_file_lloc_hard_ceiling() -> None:
    offenders = {
        path.relative_to(_repo_root()).as_posix(): _count_lloc(source=path.read_text())
        for path in sorted((_repo_root() / "livespec_runtime").glob("hygiene_scan*.py"))
        if _count_lloc(source=path.read_text()) > _HARD_CEILING
    }

    assert offenders == {}


def _repo_root() -> Path:
    return Path(__file__).parents[2]


def _docstring_lines(*, source: str) -> set[int]:
    tree = ast.parse(source)
    out: set[int] = set()
    holders: list[ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            holders.append(node)
    for holder in holders:
        body = holder.body
        if (
            len(body) > 0
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            first = body[0]
            assert first.end_lineno is not None
            out.update(range(first.lineno, first.end_lineno + 1))
    return out


def _count_lloc(*, source: str) -> int:
    docstring_lines = _docstring_lines(source=source)
    code_lines: set[int] = set()
    tokens = tokenize.tokenize(BytesIO(source.encode("utf-8")).readline)
    for tok in tokens:
        if tok.type in _NON_LLOC_TOKEN_TYPES:
            continue
        line = tok.start[0]
        if line in docstring_lines:
            continue
        code_lines.add(line)
    return len(code_lines)
