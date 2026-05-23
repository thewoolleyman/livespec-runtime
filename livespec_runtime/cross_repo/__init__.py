"""livespec_runtime.cross_repo — cross-repo work-item dependency resolution.

Skeleton landing the public surface as a single entry-point per
livespec/SPECIFICATION/contracts.md §"Cross-repo dependency awareness"
(landed by work-item li-e7h6ki under parent epic li-6d2wpj). The actual
implementation (typed DependsOnEntry union, providers.github, retry
policy, resolve_ref) lands via li-aclzfe and bumps livespec-runtime to
v0.2.0.

At v0.1.0 the surface is intentionally empty; the import boundary
exists so consumer pyproject.toml entries can pin
livespec-runtime>=0.1.0 today and the bump to v0.2.0 carries only the
impl, not the contract.
"""

__all__: list[str] = []
