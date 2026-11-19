#!/usr/bin/env python3
"""Require an explicitly selected successful package build from the source repository."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess


def validate(run, repository, commit):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Use an owner/repository source")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        raise ValueError("Select the full source commit SHA")
    if (
        run.get("repository", {}).get("full_name") != repository
        or run.get("head_repository", {}).get("full_name") != repository
    ):
        raise ValueError("Build must come from the selected source repository, not a fork")
    if run.get("path") != ".github/workflows/sketch-tools.yml" or run.get("event") != "workflow_dispatch":
        raise ValueError("Select a manual Optional Music Sketch Tools package run")
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise ValueError("Package build must complete successfully")
    if run.get("head_sha", "").lower() != commit.lower():
        raise ValueError("Package build does not match the selected source commit")
    return dict(repository=repository, commit=commit.lower(), run=run["id"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    repository, commit, run_id = (os.environ[name] for name in ("SOURCE_REPOSITORY", "SOURCE_COMMIT", "BUILD_RUN"))
    if not run_id.isdecimal() or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid source repository or numeric build run ID")
    run = json.loads(subprocess.check_output(["gh", "api", f"repos/{repository}/actions/runs/{run_id}"]))
    record = validate(run, repository, commit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2) + "\n")
    print("Verified selected source build and commit")
