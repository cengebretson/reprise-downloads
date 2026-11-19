#!/usr/bin/env python3
"""Stage verified release assets for a GitHub draft release; never publishes."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

from merge_catalog import collect


def stage(packages, repository, tag, out, unsigned_preview=False, source_assets=()):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Use a GitHub owner/repository destination")
    match = re.fullmatch(r"music-sketch-tools-v([0-9]+\.[0-9]+\.[0-9]+)(-preview\.[1-9][0-9]*)?", tag)
    if not match:
        raise ValueError("Use a music-sketch-tools-vMAJOR.MINOR.PATCH[-preview.N] tag")
    if unsigned_preview and not match[2]:
        raise ValueError("Unsigned packages require an explicit -preview.N release tag")
    base = f"https://github.com/{repository}/releases/download/{tag}"
    catalog = collect(packages, base)
    if match[1] != catalog["version"]:
        raise ValueError("Release tag does not match the package version")
    evidence = {}
    for path in packages.rglob("smoke.json"):
        smoke = json.loads(path.read_text())
        if smoke.get("status") == "PASS" and smoke.get("independentPlaybackAfterRemoval") == "PASS":
            evidence[smoke["plan"]["platform"]] = smoke
    selected = []
    reports = {}
    for platform, asset in catalog["platforms"].items():
        listings = list(packages.rglob(f"catalog-{platform}.json"))
        if len(listings) != 1:
            raise ValueError(f"Expected one source catalog for {platform}")
        folder = listings[0].parent
        report = json.loads((folder / f"signing-{platform}.json").read_text())
        if report.get("archiveSha256") != asset["sha256"] or report.get("platform") != platform:
            raise ValueError(f"Signing evidence does not match {platform}")
        expected = (
            "developer-id"
            if platform.startswith("macos-")
            else "authenticode"
            if platform.startswith("windows-")
            else "catalog-checksums"
        )
        kind = report.get("kind")
        if kind != expected and not (unsigned_preview and kind == "unsigned"):
            raise ValueError(f"Unsigned package cannot be released: {platform}")
        if (
            not unsigned_preview
            and expected == "developer-id"
            and report.get("notarization", {}).get("status") != "Accepted"
        ):
            raise ValueError(f"Apple notarization is missing: {platform}")
        smoke = evidence.get(platform, {})
        if (
            smoke.get("plan", {}).get("downloadBytes") != asset["bytes"]
            or smoke.get("archiveSha256") != asset["sha256"]
        ):
            raise ValueError(f"Matching install/sketch/remove evidence is missing: {platform}")
        archive = folder / asset["url"].rsplit("/", 1)[1]
        with zipfile.ZipFile(archive) as zip_file:
            manifest_bytes = zip_file.read("package.json")
            if hashlib.sha256(manifest_bytes).hexdigest() != asset["manifestSha256"]:
                raise ValueError(f"Manifest does not match catalog: {platform}")
            manifest = json.loads(manifest_bytes)
        if manifest.get("signing", {}).get("kind") != kind or manifest.get("platform") != platform:
            raise ValueError(f"Manifest signing/platform disagrees: {platform}")
        reports[platform] = report
        asset["signing"] = kind
        selected.append(archive)
    catalog["releaseChannel"] = "unsigned-preview" if unsigned_preview else "stable"
    sources = {}
    names = {archive.name for archive in selected}
    for source in source_assets:
        if not source.is_file() or source.name in names:
            raise ValueError("Missing or conflicting source asset: " + str(source))
        names.add(source.name)
        checksum = hashlib.sha256()
        with source.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                checksum.update(chunk)
        sources[source.name] = dict(
            url=base + "/" + source.name, sha256=checksum.hexdigest(), bytes=source.stat().st_size
        )
        selected.append(source)
    catalog["sourceAssets"] = sources
    out.mkdir(parents=True, exist_ok=False)
    for archive in selected:
        shutil.copy2(archive, out / archive.name)
    (out / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n")
    (out / "verification.json").write_text(json.dumps(dict(signing=reports, smoke=evidence), indent=2) + "\n")
    notes = (
        f"Optional Music Sketch Tools {catalog['version']}.\n\n"
        f"Platforms: {', '.join(catalog['platforms'])}.\n\n"
        "Install only after an explicit download plan. Saved projects play without these tools. "
        "Models download separately and are cached.\n\n"
        "Draft for review: verify publisher identity, third-party notices and FFmpeg source distribution before publishing.\n"
    )
    if unsigned_preview:
        notes = (
            "## Unsigned developer preview\n\n"
            "This prototype is not notarized or publisher-verified. macOS/Windows may show security warnings. "
            "Use it only if you trust this source; do not disable system security globally.\n\n"
        ) + notes
    (out / "RELEASE.md").write_text(notes)
    print(json.dumps(dict(staged=str(out), catalog=base + "/catalog.json", published=False)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", required=True, type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--source-asset",
        action="append",
        type=Path,
        default=[],
        help="Approved corresponding-source archive to attach with the release",
    )
    parser.add_argument(
        "--unsigned-preview",
        action="store_true",
        help="Allow an explicitly labeled unsigned developer prerelease; integrity and smoke checks still apply",
    )
    args = parser.parse_args()
    sources = args.source_asset or sorted(args.packages.rglob("*-helper-source.zip")) + sorted(
        args.packages.rglob("ffmpeg-*.tar.xz")
    )
    stage(
        args.packages,
        args.repository,
        args.tag,
        args.out,
        unsigned_preview=args.unsigned_preview,
        source_assets=sources,
    )
