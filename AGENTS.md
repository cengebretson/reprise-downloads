# Reprise downloads

This repository owns public distribution: release catalogs, draft publication,
release-integrity checks and release notes. Start with `git status --short` and
`make help`. Follow `docs/RELEASING.md` for the release contract.

Reprise's source repository owns reconstruction, the agent skill, native Settings
integration, runtime packaging/signing and platform lifecycle tests. Do not copy
those implementations into this Git tree or expose private source or credentials.
The user has approved publishing native-helper corresponding source (including
linked engine/device code) as a preview release asset; artwork, private media,
models and credentials remain excluded.

Keep archives, models, audio and credentials out of Git; upload approved packages
as release assets. `make test` is offline and uses generated fixtures. Preserve
license bytes. Verify moved links and run tests in both repositories when changing
the package/catalog contract. Never silently publish a draft or replace an asset.
