"""GitHub `gh` CLI provider for cross-repo state queries.

Per livespec/SPECIFICATION/contracts.md §"Cross-repo dependency awareness":
the runtime invokes `gh` CLI for all GitHub queries. `gh` MUST be
installed and authenticated (`gh auth status` returning success) in any
environment where the runtime is consumed.

Each function raises `subprocess.CalledProcessError` (or `JSONDecodeError`)
on failure; callers wrap them in `retry.retry_with_backoff` and translate
None into `RefStatus.unknown`.
"""

import json
import subprocess
from typing import Any


def query_pull_request_state(*, github_url: str, number: int) -> str:
    """Return the PR's `state` field via `gh pr view`.

    State is one of `OPEN`, `CLOSED`, `MERGED`, `DRAFT` per the GitHub
    REST API. Caller interprets `MERGED` and `CLOSED` as resolved.
    """
    result = subprocess.run(
        ["gh", "pr", "view", str(number), "--repo", github_url, "--json", "state"],
        capture_output=True,
        check=True,
        text=True,
    )
    payload: dict[str, Any] = json.loads(result.stdout)
    return str(payload["state"])


def branch_exists_on_remote(*, github_url: str, name: str) -> bool:
    """Return True iff the named branch exists on the remote.

    Uses `gh api repos/<owner>/<name>/branches/<branch>`; a 404 (caught
    via subprocess.CalledProcessError on the `gh api` exit) translates
    to False, anything else propagates.
    """
    owner_name = _split_owner_name(github_url=github_url)
    try:
        _ = subprocess.run(
            ["gh", "api", f"repos/{owner_name}/branches/{name}"],
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        if exc.stderr and "404" in exc.stderr:
            return False
        raise
    return True


def branch_merged_into_default(*, github_url: str, name: str, default_branch: str) -> bool:
    """Return True iff `name` is fully reachable from `default_branch`.

    Uses `gh api repos/<owner>/<name>/compare/<default>...<name>`.
    The `behind_by` field is 0 iff `name` is merged into `default_branch`
    (every commit in default is in name as ancestor) — but actually we
    want the inverse: `ahead_by == 0` means name has no commits beyond
    default's tip, i.e., name is merged. The `status` field gives the
    same answer ('identical' or 'behind' = merged).
    """
    owner_name = _split_owner_name(github_url=github_url)
    result = subprocess.run(
        ["gh", "api", f"repos/{owner_name}/compare/{default_branch}...{name}"],
        capture_output=True,
        check=True,
        text=True,
    )
    payload: dict[str, Any] = json.loads(result.stdout)
    return str(payload["status"]) in ("identical", "behind")


class NonCanonicalGithubUrlError(ValueError):
    """Raised when a github_url is not the canonical `https://github.com/<owner>/<name>` form."""

    def __init__(self, *, github_url: str) -> None:
        super().__init__(f"expected canonical github_url, got {github_url!r}")
        self.github_url = github_url


def _split_owner_name(*, github_url: str) -> str:
    """Convert `https://github.com/<owner>/<name>` → `<owner>/<name>`."""
    prefix = "https://github.com/"
    if not github_url.startswith(prefix):
        raise NonCanonicalGithubUrlError(github_url=github_url)
    tail = github_url[len(prefix) :]
    return tail.removesuffix(".git").removesuffix("/")


__all__ = [
    "NonCanonicalGithubUrlError",
    "branch_exists_on_remote",
    "branch_merged_into_default",
    "query_pull_request_state",
]
