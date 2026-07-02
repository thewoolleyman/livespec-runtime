# tests/livespec_runtime/github_auth/

Mirrors `livespec_runtime/github_auth/` one-to-one (per the
`tests_mirror_pairing` discipline). Covers the fleet GitHub App-token
auth primitive: JWT assembly + RS256 signing, the env-only fail-closed
config boundary, the installation-token mint railway, the ~55-minute
caching provider (including the HARD acceptance test forcing token
expiry mid-sequence), and the `git credential` helper protocol.

No live GitHub calls: every HTTP interaction is exercised through the
injectable seams (fakes) or a monkeypatched `urllib.request.urlopen`;
the clock is injected wherever expiry matters. The only real
subprocess spawned is `openssl` (offline key generation + sign/verify
round-trips in `test_signing.py`).
