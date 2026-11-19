# Reprise downloads

Public distribution tooling and release downloads for optional Reprise tools.
Reprise's application source and runtime build tooling remain separate.

## Music Sketch Tools

Music Sketch Tools provides optional audio analysis for agent-assisted, editable
song sketches. It installs separately and includes private Python, audio tools
and native project helpers. Saved sketches play without the analysis tools installed.

No tools release is available yet. Verified packages will appear under
[Releases](https://github.com/cengebretson/reprise-downloads/releases).
Unsigned developer previews are supported with an explicit preview tag and
disclosure; stable releases retain publisher-signing requirements. Both paths
require checksums and a passing install/sketch/remove test.

Reprise's **Settings → Agent integrations…** card shows download sizes and offers
optional installation when a published catalog is configured. Opening Settings or
installing the skill downloads no analysis runtime/models. Removing tools preserves
songs, source audio and cached models. Models download separately from upstream.

This repository owns catalogs, release notes, draft-release workflows and their
integrity checks. Each versioned release contains platform archives, checksum
catalogs and verification evidence. Third-party notices ship inside each package.
Archives and models are release assets, not source files tracked in this repo.

Run `make test` for offline tests; see [releasing](docs/RELEASING.md) for staging.
Source packaging, signing and lifecycle checks remain with Reprise so native
helpers, the runtime, skill and Settings integration stay synchronized.

The distribution helpers use the [GNU AGPL version 3](LICENSE).
