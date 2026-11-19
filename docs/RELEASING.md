# Music Sketch Tools releases

This repository owns distribution. The Reprise source repository builds/signs
platform archives and runs install/sketch/remove tests. It uploads those archives,
platform catalogs, signing reports and smoke evidence as workflow artifacts.
No private checkout is needed to run this repository's tests or staging helpers.

## Draft a release

1. Complete the source repository's manual **Optional Music Sketch Tools** workflow
   with **signed** enabled and the desired platforms. Record its run ID and full
   source commit SHA. All selected jobs must pass.
2. Configure this repository's `music-sketch-tools-release` environment with
   `SOURCE_REPO_TOKEN`: a fine-grained token with Actions read access to the source
   repository. The built-in token writes releases here; no write token for the
   private source repository is needed.
3. Run **Stage Music Sketch Tools release** here. Supply the source repository,
   exact source commit, successful package run ID and `music-sketch-tools-vX.Y.Z` tag.
4. Review the resulting draft, publisher identities, notices and FFmpeg source
   distribution before publishing. The workflow never publishes automatically.

The source and downloads repositories have independent commits. The workflow
checks the selected source commit, source repository, manual package workflow
and successful completion; it rejects fork builds and unrelated runs. It verifies
package checksums, Mac notarization/Windows signing evidence and matching lifecycle
smoke hashes. Existing releases/assets are never overwritten.

Release assets are platform ZIPs, `catalog.json`, `verification.json` and
`source-build.json`. Readback confirms the release is still a draft and uploaded
sizes match. Keep large archives in GitHub Releases rather than Git history.

After publication, configure Reprise's `REPRISE_SKETCH_TOOLS_CATALOG` build setting
to the published version's `catalog.json` URL. Do not point production builds to
draft releases or require GitHub credentials on user machines.

## Local staging

### Unsigned developer previews

Apple/Windows signing accounts are optional for explicitly labeled prototype
prereleases. Choose a `music-sketch-tools-vX.Y.Z-preview.N` tag and enable the
workflow's **unsigned_preview** input, or pass `--unsigned-preview` locally.
The source build may use **signed: false**. Version/manifest/archive hashes and
install/sketch/remove evidence remain mandatory. The catalog marks the preview
channel, and the release notes disclose that publisher verification/notarization
are absent. Signed stable releases keep the original stricter checks.

Unsigned previews still need their corresponding source and upstream notices.
The user has approved disclosing the native helper/engine/device source as a
release asset. Keep app artwork, private recordings, models and credentials out.
Use `--source-asset` for approved helper and FFmpeg source archives when staging;
the catalog records their hashes and sizes. Uploaded sources are release assets,
not a copy of the private app source tree committed to this repo.

```bash
python3 tools/prepare_release.py --packages /path/to/artifacts --repository cengebretson/reprise-downloads --tag music-sketch-tools-v0.1.0-preview.1 --unsigned-preview --source-asset /path/to/helper-source.zip --source-asset /path/to/ffmpeg-9.0.tar.xz --out build/preview
```

The workflow still creates a draft, with the GitHub prerelease flag set for a
preview tag; publishing is a separate, explicit action. Local previews can be
staged from verified local build artifacts without claiming a successful CI run.

Download a successful package run's artifacts to a scratch directory. Keep their
per-platform folders and smoke evidence; the helpers find them recursively:

```bash
make test
python3 tools/prepare_release.py --packages /path/to/artifacts --repository cengebretson/reprise-downloads --tag music-sketch-tools-v0.1.0 --out build/release
```

Use a fresh output directory. Staging uploads nothing. `tools/merge_catalog.py`
can combine archive-verified catalogs, but does not establish signing or smoke
evidence by itself. Native installer and schema changes belong with Reprise;
update these release gates when their contract changes.

Publisher credentials remain required for signed stable releases. Only advertise
platforms that have passed their real package lifecycle checks.
