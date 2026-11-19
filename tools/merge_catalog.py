#!/usr/bin/env python3
"""Prepare a reviewable release catalog from built archives; uploads/publishes nothing."""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse


def collect(packages, base_url):
    if urlparse(base_url).scheme != "https":
        raise ValueError("The release base URL must use HTTPS")
    merged = None
    for path in sorted(packages.rglob("catalog-*.json")):
        catalog = json.loads(path.read_text())
        if merged is None:
            merged = dict(schema=1, version=catalog["version"], models=catalog["models"], platforms={})
        if catalog["version"] != merged["version"] or catalog["models"] != merged["models"]:
            raise ValueError("Catalog versions or model pins disagree")
        for platform, asset in catalog["platforms"].items():
            if platform in merged["platforms"]:
                raise ValueError(f"Duplicate platform: {platform}")
            name = f"reprise-sketch-tools-{catalog['version']}-{platform}.zip"
            archive = path.parent / name
            with archive.open("rb") as stream:
                checksum = hashlib.sha256()
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    checksum.update(chunk)
                digest = checksum.hexdigest()
            if digest != asset["sha256"] or archive.stat().st_size != asset["bytes"]:
                raise ValueError(f"Archive hash/size mismatch: {archive}")
            merged["platforms"][platform] = dict(asset, url=base_url.rstrip("/") + "/" + name)
    if merged is None:
        raise ValueError("No package catalogs found")
    return merged


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", required=True, type=Path)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    merged = collect(args.packages, args.base_url)
    if args.out.exists():
        raise ValueError("Refusing to overwrite an existing catalog")
    args.out.write_text(json.dumps(merged, indent=2) + "\n")
    print(json.dumps(dict(catalog=str(args.out), platforms=list(merged["platforms"]), published=False)))


if __name__ == "__main__":
    main()
