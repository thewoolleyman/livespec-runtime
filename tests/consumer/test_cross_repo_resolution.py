"""Consumer-tier scenario tests for `livespec_runtime` cross-repo resolution.

This is the top-of-pyramid, consumer-style test tier for
livespec-runtime. Each test drives the library exactly as an external
consumer would — importing ONLY the public surface enumerated in
`SPECIFICATION/contracts.md` §"Module-level public surface", building
a `CrossRepoManifest` from consumer-shaped `.livespec.jsonc` dicts via
`parse_cross_repo_manifest`, building `DependsOnEntry` variants via
`parse_depends_on_entry`, and resolving them through the public
`resolve_ref` entry point.

Crucially this tier never reaches past the public boundary: it
monkeypatches `subprocess.run` (the OS edge a real consumer's `gh`
invocations cross) with recorded fixture payloads — NOT the internal
`gh_provider` functions — and asserts only on consumer-VISIBLE return
values (`RefStatus` members) and consumer-CATCHABLE error TYPES
(`CrossRepoSchemaError`, `NonCanonicalGithubUrlError`). No internal
shape (argv lists, retry-counter internals, private helpers) is
asserted here; those live in the unit tier under
`tests/livespec_runtime/`.

Tier registration: every `## Scenario:` heading in
`SPECIFICATION/scenarios.md` maps (many-to-one) to a test below via
`tests/heading-coverage.json`, under the `tests.consumer` allowlisted
node-id prefix declared in `pyproject.toml`
`[tool.livespec_dev_tooling].scenario_tiers` (epic li-scetier Wave 4,
work-item li-scetrn).

`time.sleep` is monkeypatched in the retry-exhaustion test so the
backoff policy is exercised without burning real wall-clock delay; no
live network or real `gh` process is ever spawned.
"""

import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

# Every import below is part of `livespec_runtime`'s public surface per
# contracts.md §"Module-level public surface": the parse boundary, the
# typed manifest + RefStatus, the `resolve_ref` entry point, the two
# consumer-catchable error types, and the one public provider function a
# consumer that pre-validates URLs may invoke directly.
from livespec_runtime.cross_repo.errors import CrossRepoSchemaError
from livespec_runtime.cross_repo.providers.github import (
    NonCanonicalGithubUrlError,
    branch_exists_on_remote,
)
from livespec_runtime.cross_repo.resolve import resolve_ref
from livespec_runtime.cross_repo.types import (
    CrossRepoManifest,
    RefStatus,
    parse_cross_repo_manifest,
    parse_depends_on_entry,
)

__all__: list[str] = []

# Recorded gh responses shared with the unit tier; re-using them keeps
# the consumer tier honest about the real gh payload shapes without a
# live network call.
_GH_FIXTURES = (
    Path(__file__).resolve().parent.parent
    / "livespec_runtime"
    / "cross_repo"
    / "providers"
    / "fixtures"
)


def _gh_stdout(*, fixture: str) -> str:
    return (_GH_FIXTURES / fixture).read_text(encoding="utf-8")


def _completed(*, argv: list[str], stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=argv, returncode=0, stdout=stdout, stderr="")


def _http_404_error() -> subprocess.CalledProcessError:
    exc = subprocess.CalledProcessError(returncode=1, cmd=["gh"])
    exc.stderr = "gh: Not Found (HTTP 404)"
    return exc


def _manifest_from_jsonc(*, block: dict[str, Any]) -> CrossRepoManifest:
    """Build a manifest exactly as a consumer would from `.livespec.jsonc`."""
    return parse_cross_repo_manifest(parsed=block)


# A consumer's local-store lookup that reports everything in-flight. Only
# `LocalDependency` resolution ever invokes `local_status_lookup`, so the
# non-local tests pass this purely to satisfy the required parameter; an
# inline lambda keeps it coverage-clean (the body is never executed there).
def _open_lookup(_work_item_id: str) -> RefStatus:  # pragma: no cover
    return RefStatus.OPEN


# ---------------------------------------------------------------------------
# gh-fixture-driven subprocess monkeypatch helpers. A consumer's
# environment shells out to `gh`; we patch the single OS edge
# (`subprocess.run`) and route each call to a fixture by matching on
# the gh subcommand the resolver issues.
# ---------------------------------------------------------------------------


def _patch_gh(
    monkeypatch: pytest.MonkeyPatch,
    *,
    pr_state_fixture: str | None = None,
    branch_present: bool | None = None,
    compare_fixture: str | None = None,
) -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        # `gh pr view <n> --repo <url> --json state`
        if argv[:3] == ["gh", "pr", "view"]:
            assert pr_state_fixture is not None
            return _completed(argv=argv, stdout=_gh_stdout(fixture=pr_state_fixture))
        # `gh api repos/<owner>/<name>/compare/<base>...<head>`
        if argv[:2] == ["gh", "api"] and "compare/" in argv[2]:
            assert compare_fixture is not None
            return _completed(argv=argv, stdout=_gh_stdout(fixture=compare_fixture))
        # `gh api repos/<owner>/<name>/branches/<branch>`
        if argv[:2] == ["gh", "api"] and "/branches/" in argv[2]:
            if branch_present:
                return _completed(argv=argv, stdout=_gh_stdout(fixture="branch_view_present.json"))
            raise _http_404_error()
        raise AssertionError(f"unexpected gh invocation: {argv}")  # pragma: no cover

    monkeypatch.setattr(subprocess, "run", fake_run)


# ===========================================================================
# Pull-request dependency scenarios
# ===========================================================================


def test_pull_request_dependency_resolution_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers scenarios:
    - "resolve a closed pull-request dependency" (MERGED -> CLOSED)
    - "resolve an open pull-request dependency" (OPEN -> OPEN)

    A consumer declares a manifest from its `.livespec.jsonc`
    `cross_repo_targets` block, parses a `pull_request` depends_on
    entry, and resolves it; the gh `state` is round-tripped to a
    consumer-visible `RefStatus`.
    """
    manifest = _manifest_from_jsonc(
        block={
            "livespec": {"github_url": "https://github.com/thewoolleyman/livespec"},
            "livespec-runtime": {"github_url": "https://github.com/thewoolleyman/livespec-runtime"},
        }
    )

    merged_entry = parse_depends_on_entry(
        parsed={"kind": "pull_request", "repo": "livespec", "number": 166}
    )
    _patch_gh(monkeypatch, pr_state_fixture="pr_view_merged.json")
    assert (
        resolve_ref(entry=merged_entry, manifest=manifest, local_status_lookup=_open_lookup)
        == RefStatus.CLOSED
    )

    open_entry = parse_depends_on_entry(
        parsed={"kind": "pull_request", "repo": "livespec-runtime", "number": 2}
    )
    _patch_gh(monkeypatch, pr_state_fixture="pr_view_open.json")
    assert (
        resolve_ref(entry=open_entry, manifest=manifest, local_status_lookup=_open_lookup)
        == RefStatus.OPEN
    )


def test_pull_request_dependency_retry_exhaustion_is_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Covers scenario "pull-request dependency under retry exhaustion".

    When every `gh pr view` attempt raises, the consumer sees
    `RefStatus.UNKNOWN` after the retry policy is exhausted — never an
    exception bubbling out of `resolve_ref`. `time.sleep` is patched so
    the backoff runs instantly.
    """
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)

    def always_raise(_argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        exc = subprocess.CalledProcessError(returncode=1, cmd=["gh"])
        exc.stderr = "gh: server error (HTTP 500)"
        raise exc

    monkeypatch.setattr(subprocess, "run", always_raise)
    manifest = _manifest_from_jsonc(
        block={"livespec": {"github_url": "https://github.com/thewoolleyman/livespec"}}
    )
    entry = parse_depends_on_entry(parsed={"kind": "pull_request", "repo": "livespec", "number": 2})
    assert (
        resolve_ref(entry=entry, manifest=manifest, local_status_lookup=_open_lookup)
        == RefStatus.UNKNOWN
    )


def test_pull_request_dependency_unknown_repo_slug_is_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Covers scenario "pull-request dependency with unknown repo slug".

    A `repo` slug absent from the manifest resolves to
    `RefStatus.UNKNOWN` with NO gh invocation — `subprocess.run` is
    patched to fail loudly so any attempted shell-out would surface.
    """

    def forbid_run(_argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise AssertionError(  # pragma: no cover
            "no gh invocation expected for an unknown repo slug"
        )

    monkeypatch.setattr(subprocess, "run", forbid_run)
    manifest = _manifest_from_jsonc(
        block={"livespec": {"github_url": "https://github.com/thewoolleyman/livespec"}}
    )
    entry = parse_depends_on_entry(
        parsed={"kind": "pull_request", "repo": "livespec-runtime", "number": 2}
    )
    assert (
        resolve_ref(entry=entry, manifest=manifest, local_status_lookup=_open_lookup)
        == RefStatus.UNKNOWN
    )


# ===========================================================================
# Branch dependency scenarios
# ===========================================================================


def test_branch_dependency_resolution_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers scenarios:
    - "branch dependency that no longer exists on remote" (404 -> CLOSED)
    - "branch dependency present but not yet merged" (present + ahead -> OPEN)
    - "branch dependency present and merged into default" (present + identical -> CLOSED)

    A consumer resolves `branch` depends_on entries against the gh
    remote view; absent/merged/unmerged each map to a consumer-visible
    `RefStatus`.
    """
    manifest = _manifest_from_jsonc(
        block={
            "livespec-runtime": {
                "github_url": "https://github.com/thewoolleyman/livespec-runtime",
                "default_branch": "master",
            }
        }
    )

    gone_entry = parse_depends_on_entry(
        parsed={"kind": "branch", "repo": "livespec-runtime", "name": "feat/old-merged-branch"}
    )
    _patch_gh(monkeypatch, branch_present=False)
    assert (
        resolve_ref(entry=gone_entry, manifest=manifest, local_status_lookup=_open_lookup)
        == RefStatus.CLOSED
    )

    unmerged_entry = parse_depends_on_entry(
        parsed={
            "kind": "branch",
            "repo": "livespec-runtime",
            "name": "feat/cross-repo-types-li-aclzfe",
        }
    )
    _patch_gh(monkeypatch, branch_present=True, compare_fixture="branch_compare_ahead.json")
    assert (
        resolve_ref(entry=unmerged_entry, manifest=manifest, local_status_lookup=_open_lookup)
        == RefStatus.OPEN
    )

    merged_entry = parse_depends_on_entry(
        parsed={"kind": "branch", "repo": "livespec-runtime", "name": "some-merged-branch"}
    )
    _patch_gh(monkeypatch, branch_present=True, compare_fixture="branch_compare_identical.json")
    assert (
        resolve_ref(entry=merged_entry, manifest=manifest, local_status_lookup=_open_lookup)
        == RefStatus.CLOSED
    )


def test_non_canonical_github_url_raises_for_branch_provider() -> None:
    """Covers scenario "non-canonical github_url raises NonCanonicalGithubUrlError".

    A consumer that invokes the public provider function
    `branch_exists_on_remote` (per contracts.md
    §`livespec_runtime.cross_repo.providers.github`) with a
    non-canonical (ssh) github_url gets `NonCanonicalGithubUrlError`
    carrying the offending url verbatim, raised at the owner/name split
    BEFORE any `gh` shell-out. (This typed error surfaces only when the
    provider is called directly; behind the `resolve_ref` retry layer
    it degrades to `RefStatus.UNKNOWN`, which is the
    "tolerate-partial-visibility" contract, so the scenario is observed
    here at the provider boundary the Gherkin names.)
    """
    offending = "git@github.com:thewoolleyman/livespec.git"
    with pytest.raises(NonCanonicalGithubUrlError) as excinfo:
        _ = branch_exists_on_remote(github_url=offending, name="feat/foo")
    assert excinfo.value.github_url == offending


# ===========================================================================
# Local + sibling work-item dependency scenarios
# ===========================================================================


def test_local_dependency_delegates_to_caller_lookup() -> None:
    """Covers scenario "local dependency delegates to caller-supplied lookup".

    A `local` dependency resolves entirely via the consumer-supplied
    `local_status_lookup`; no gh invocation occurs (the local path
    never touches `subprocess`).
    """
    manifest = CrossRepoManifest(targets={})
    entry = parse_depends_on_entry(parsed={"kind": "local", "work_item_id": "li-aclzfe"})

    def lookup(work_item_id: str) -> RefStatus:
        return RefStatus.OPEN if work_item_id == "li-aclzfe" else RefStatus.UNKNOWN

    assert resolve_ref(entry=entry, manifest=manifest, local_status_lookup=lookup) == RefStatus.OPEN


def test_sibling_work_item_without_lookup_is_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    """Covers scenario "sibling work-item dependency without sibling_status_lookup".

    A `sibling_work_item` dependency with no `sibling_status_lookup`
    supplied resolves to `RefStatus.UNKNOWN` with NO gh invocation.
    """

    def forbid_run(_argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise AssertionError(  # pragma: no cover
            "no gh invocation expected for a sibling work-item with no lookup"
        )

    monkeypatch.setattr(subprocess, "run", forbid_run)
    manifest = _manifest_from_jsonc(
        block={"livespec": {"github_url": "https://github.com/thewoolleyman/livespec"}}
    )
    entry = parse_depends_on_entry(
        parsed={"kind": "sibling_work_item", "repo": "livespec", "work_item_id": "li-e7h6ki"}
    )
    assert (
        resolve_ref(entry=entry, manifest=manifest, local_status_lookup=_open_lookup)
        == RefStatus.UNKNOWN
    )


# ===========================================================================
# Parse-boundary accept / reject scenarios
# ===========================================================================


def test_parse_depends_on_entry_rejects_unknown_kind() -> None:
    """Covers scenario "parse_depends_on_entry rejects unknown kind".

    A consumer feeding an unknown `kind` gets `CrossRepoSchemaError`
    whose `detail` names the offending kind and enumerates the four
    valid kinds.
    """
    with pytest.raises(CrossRepoSchemaError) as excinfo:
        _ = parse_depends_on_entry(parsed={"kind": "slack_thread", "channel": "#engineering"})
    detail = excinfo.value.detail
    assert "slack_thread" in detail
    for valid_kind in ("local", "sibling_work_item", "pull_request", "branch"):
        assert valid_kind in detail


def test_parse_depends_on_entry_rejects_missing_required_field() -> None:
    """Covers scenario "parse_depends_on_entry rejects missing required field".

    A `pull_request` entry missing `number` raises
    `CrossRepoSchemaError` whose `detail` names the missing field.
    """
    with pytest.raises(CrossRepoSchemaError) as excinfo:
        _ = parse_depends_on_entry(parsed={"kind": "pull_request", "repo": "livespec"})
    assert "number" in excinfo.value.detail


def test_parse_cross_repo_manifest_accepts_minimal_target() -> None:
    """Covers scenario "parse_cross_repo_manifest accepts minimal target".

    A minimal target dict (github_url only) parses into a manifest with
    one target whose optional fields fall back to their documented
    defaults (`local_clone is None`, `default_branch == "master"`).
    """
    manifest = parse_cross_repo_manifest(
        parsed={"livespec": {"github_url": "https://github.com/thewoolleyman/livespec"}}
    )
    assert set(manifest.targets) == {"livespec"}
    target = manifest.targets["livespec"]
    assert target.local_clone is None
    assert target.default_branch == "master"


def test_parse_cross_repo_manifest_rejects_target_missing_github_url() -> None:
    """Covers scenario "parse_cross_repo_manifest rejects target missing github_url".

    A target dict lacking `github_url` raises `CrossRepoSchemaError`
    whose `detail` names both the missing field and the offending slug.
    """
    with pytest.raises(CrossRepoSchemaError) as excinfo:
        _ = parse_cross_repo_manifest(parsed={"livespec": {"default_branch": "main"}})
    detail = excinfo.value.detail
    assert "github_url" in detail
    assert "livespec" in detail
