#!/usr/bin/env python3
"""Initialize a local artifact folder for one submission candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path("artifacts")
DEFAULT_DATA_DIR = Path("data/sample")
DEFAULT_REFERENCE_REGISTRY = Path("experiments/reference_submission_registry.csv")


def slugify(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower()).strip("_")
    text = re.sub(r"_+", "_", text)
    if not text:
        raise ValueError("candidate id cannot be empty after normalization")
    return text


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def build_manifest(
    candidate_id: str,
    requested_candidate_id: str,
    family: str,
    artifact_dir: Path,
    source_path: str,
    notes: str,
    data_dir: Path,
    reference_registry: Path,
) -> dict[str, Any]:
    manifest_path = artifact_dir / "candidate_manifest.json"
    submission_path = artifact_dir / "submission.csv"
    deep_audit_path = artifact_dir / "deep_pre_submit_audit.json"
    local_audit_path = artifact_dir / "candidate_audit.json"
    run_notes_path = artifact_dir / "run_notes.md"

    return {
        "candidate_id": candidate_id,
        "requested_candidate_id": requested_candidate_id,
        "family": family,
        "status": "initialized",
        "created_utc": utc_now(),
        "artifact_dir": rel(artifact_dir),
        "source_path": source_path,
        "notes": notes,
        "files": {
            "manifest": rel(manifest_path),
            "submission": rel(submission_path),
            "deep_pre_submit_audit": rel(deep_audit_path),
            "candidate_audit": rel(local_audit_path),
            "run_notes": rel(run_notes_path),
        },
        "checksums": {
            "submission_sha256": sha256_file(submission_path),
            "source_sha256": sha256_file(Path(source_path)) if source_path else None,
        },
        "required_before_official_submission": [
            "submission.csv exists in this artifact folder or this manifest points to the exact selected output",
            "scripts/pre_submit_audit.py passes with --reference-registry experiments/reference_submission_registry.csv",
            "deep_pre_submit_audit.json exists and has status PASS",
            "candidate appears in experiments/candidate_audit_summary.csv with a non-failing audit gate",
            "scripts/poll_and_refresh_state.py has been rerun after the latest Kaggle status check",
            "reports/submission_release_gate_report.md has no BLOCKED_* or REVIEW_LEDGER_UPDATES result for the selected slot",
            "reports/planning_state_validation_report.md reports zero error failures",
            "experiments/submission_ledger.csv is updated after any official submission",
        ],
        "standard_commands": {
            "deep_pre_submit_audit": (
                "python3 scripts/pre_submit_audit.py "
                f"{rel(submission_path)} --data-dir {rel(data_dir)} "
                f"--reference-registry {rel(reference_registry)} --json-out {rel(deep_audit_path)}"
            ),
            "refresh_planning_state": "python3 scripts/poll_and_refresh_state.py",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-id", required=True, help="Human-readable candidate id; normalized to a safe folder slug.")
    parser.add_argument("--family", default="unknown", help="Model or strategy family, e.g. projection_branch.")
    parser.add_argument("--source-path", default="", help="Optional source notebook/output/model path used to create this candidate.")
    parser.add_argument("--notes", default="", help="Short local notes to store in the manifest.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Ignored artifact root.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--reference-registry", type=Path, default=DEFAULT_REFERENCE_REGISTRY)
    parser.add_argument("--force", action="store_true", help="Overwrite an existing candidate_manifest.json.")
    parser.add_argument("--dry-run", action="store_true", help="Print the manifest without writing files.")
    args = parser.parse_args()

    candidate_id = slugify(args.candidate_id)
    artifact_dir = args.root / candidate_id
    manifest_path = artifact_dir / "candidate_manifest.json"
    manifest = build_manifest(
        candidate_id=candidate_id,
        requested_candidate_id=args.candidate_id,
        family=args.family,
        artifact_dir=artifact_dir,
        source_path=args.source_path,
        notes=args.notes,
        data_dir=args.data_dir,
        reference_registry=args.reference_registry,
    )

    if args.dry_run:
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0

    if manifest_path.exists() and not args.force:
        raise SystemExit(f"{manifest_path} already exists; pass --force to overwrite it")

    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_id": candidate_id, "manifest": rel(manifest_path), "status": "written"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
