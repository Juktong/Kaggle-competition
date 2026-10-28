#!/usr/bin/env python3
"""Prepare or inspect local final-submission packages without submitting to Kaggle."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_PLAN = Path("experiments/next_submission_batch_plan.csv")
DEFAULT_RELEASE = Path("experiments/submission_release_gate.csv")
DEFAULT_MANIFEST = Path("experiments/candidate_artifact_manifest_summary.csv")
DEFAULT_OUTPUT_CSV = Path("experiments/final_submission_package_summary.csv")
DEFAULT_REPORT = Path("reports/final_submission_package_report.md")
DEFAULT_DATA_DIR = Path("data/sample")
DEFAULT_REFERENCE_REGISTRY = Path("experiments/reference_submission_registry.csv")


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return "" if not np.isfinite(value) else f"{value:.6g}"
    if pd.isna(value):
        return ""
    return str(value)


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "No rows."
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(fmt(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path)


def norm(value: Any) -> str:
    text = str(value or "").strip()
    return Path(text).as_posix() if text else ""


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def json_default(value: Any) -> Any:
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if pd.isna(value):
        return None
    raise TypeError(f"Object of type {value.__class__.__name__} is not JSON serializable")


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def package_gate(row: pd.Series) -> tuple[str, str]:
    release_gate = str(row.get("release_gate", "") or "")
    manifest_gate = str(row.get("manifest_gate", "") or "")
    source_path = Path(norm(row.get("source_path")))
    package_path = norm(row.get("package_submission_path"))
    audit_gate = str(row.get("audit_gate", "") or "")

    if not release_gate:
        return "BLOCKED_MISSING_RELEASE_GATE", "Release gate row is missing."
    if release_gate.startswith("BLOCKED") or release_gate == "REVIEW_LEDGER_UPDATES":
        return "BLOCKED_RELEASE_GATE", f"Release gate is {release_gate}."
    if manifest_gate and not manifest_gate.startswith("PASS"):
        return "BLOCKED_MANIFEST_GATE", f"Manifest gate is {manifest_gate}."
    if not source_path.is_file():
        return "BLOCKED_SOURCE_MISSING", f"Selected source output does not exist: {source_path.as_posix()}"
    if audit_gate not in {"AUDIT_PASS", "AUDIT_PASS_WARN_REVIEW"}:
        return "BLOCKED_AUDIT_GATE", f"Audit gate is {audit_gate}."
    if not package_path:
        return "BLOCKED_NO_PACKAGE_PATH", "Manifest does not provide a package submission path."
    if release_gate == "MANUAL_REVIEW_REQUIRED":
        return "REVIEW_READY_TO_PACKAGE", "Release gate requires manual warning review before package preparation."
    if release_gate == "READY":
        return "READY_TO_PACKAGE", "Ready to copy the selected output into the local final package and rerun audit."
    return "BLOCKED_RELEASE_GATE", f"Release gate is {release_gate}."


def merged_rows(plan: pd.DataFrame, release: pd.DataFrame, manifest: pd.DataFrame) -> pd.DataFrame:
    if plan.empty:
        return pd.DataFrame()
    out = plan.copy()
    release_cols = [
        "planned_slot",
        "release_gate",
        "release_reason",
    ]
    release_cols = [c for c in release_cols if c in release.columns]
    if release_cols:
        out = out.merge(release[release_cols], on="planned_slot", how="left")

    manifest_cols = [
        "planned_slot",
        "manifest_gate",
        "manifest_path",
        "source_path",
        "source_path_exists",
        "manifest_submission_path",
        "manifest_deep_audit_path",
        "audit_json",
        "audit_json_exists",
        "sha256_submission_csv",
    ]
    manifest_cols = [c for c in manifest_cols if c in manifest.columns]
    if manifest_cols:
        out = out.merge(manifest[manifest_cols], on="planned_slot", how="left")

    out["package_submission_path"] = out.get("manifest_submission_path", pd.Series(dtype=str)).map(norm)
    out["package_submission_exists"] = out["package_submission_path"].map(lambda p: Path(p).is_file() if p else False)
    out["package_submission_sha256"] = out["package_submission_path"].map(lambda p: sha256_file(Path(p)) if p else None)
    gates = out.apply(package_gate, axis=1)
    out["package_gate"] = [gate for gate, _ in gates]
    out["package_reason"] = [reason for _, reason in gates]
    return out


def select_row(summary: pd.DataFrame, planned_slot: int | None, candidate_id: str) -> pd.Series:
    if summary.empty:
        raise SystemExit("no planned slots available")
    selected = summary
    if planned_slot is not None:
        selected = selected[selected["planned_slot"].astype(int) == int(planned_slot)]
    if candidate_id:
        selected = selected[selected["candidate_id"].astype(str) == candidate_id]
    if selected.empty:
        raise SystemExit("selected planned slot/candidate was not found")
    if len(selected) > 1:
        raise SystemExit("selection is ambiguous; pass --planned-slot or --candidate-id")
    return selected.iloc[0]


def update_manifest(manifest_path: Path, submission_path: Path) -> None:
    obj = load_json(manifest_path)
    obj["status"] = "packaged_for_final_review"
    obj["packaged_utc"] = utc_now()
    checksums = obj.setdefault("checksums", {})
    checksums["submission_sha256"] = sha256_file(submission_path)
    manifest_path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def prepare_package(row: pd.Series, data_dir: Path, reference_registry: Path, allow_review_gate: bool) -> dict[str, Any]:
    gate = str(row.get("package_gate", "") or "")
    if gate == "REVIEW_READY_TO_PACKAGE" and not allow_review_gate:
        raise SystemExit("package gate requires manual review; pass --allow-review-gate after reviewing warnings")
    if gate not in {"READY_TO_PACKAGE", "REVIEW_READY_TO_PACKAGE"}:
        raise SystemExit(f"package gate is {gate}; refusing to prepare a final package")

    source_path = Path(norm(row.get("source_path")))
    package_path = Path(norm(row.get("package_submission_path")))
    audit_path = Path(norm(row.get("manifest_deep_audit_path")))
    manifest_path = Path(norm(row.get("manifest_path")))

    package_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, package_path)

    cmd = [
        sys.executable,
        "scripts/pre_submit_audit.py",
        package_path.as_posix(),
        "--data-dir",
        data_dir.as_posix(),
        "--reference-registry",
        reference_registry.as_posix(),
        "--json-out",
        audit_path.as_posix(),
    ]
    proc = run_cmd(cmd)
    if manifest_path.is_file():
        update_manifest(manifest_path, package_path)

    return {
        "candidate_id": row.get("candidate_id", ""),
        "planned_slot": row.get("planned_slot", ""),
        "source_path": source_path.as_posix(),
        "package_submission_path": package_path.as_posix(),
        "package_submission_sha256": sha256_file(package_path),
        "audit_path": audit_path.as_posix(),
        "audit_returncode": proc.returncode,
        "audit_stdout": proc.stdout.strip(),
        "audit_stderr": proc.stderr.strip(),
    }


def write_report(summary: pd.DataFrame, output: Path, csv_path: Path, prepared: dict[str, Any] | None) -> None:
    counts = summary["package_gate"].value_counts().rename_axis("package_gate").reset_index(name="count") if not summary.empty else pd.DataFrame()
    cols = [
        "planned_slot",
        "candidate_id",
        "family",
        "release_gate",
        "manifest_gate",
        "package_gate",
        "package_submission_exists",
        "source_path",
        "package_submission_path",
        "package_reason",
    ]
    cols = [c for c in cols if c in summary.columns]
    lines = [
        "# Final Submission Package Report",
        "",
        "This report inspects local final-submission package readiness. It never submits to Kaggle.",
        "",
        "## Package Gate Counts",
        "",
        markdown_table(counts),
        "",
        "## Planned Slot Package State",
        "",
        markdown_table(summary[cols] if cols else summary),
    ]
    if prepared is not None:
        lines.extend(
            [
                "",
                "## Prepared Package",
                "",
                markdown_table(pd.DataFrame([prepared])),
            ]
        )
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- `{csv_path.as_posix()}`",
            f"- `{output.as_posix()}`",
        ]
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--manifest-summary", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--reference-registry", type=Path, default=DEFAULT_REFERENCE_REGISTRY)
    parser.add_argument("--planned-slot", type=int, default=None)
    parser.add_argument("--candidate-id", default="")
    parser.add_argument("--prepare", action="store_true", help="Copy the selected source output into its local package folder and rerun audit.")
    parser.add_argument("--allow-review-gate", action="store_true", help="Allow package preparation when release gate is MANUAL_REVIEW_REQUIRED.")
    args = parser.parse_args()

    summary = merged_rows(
        plan=safe_read_csv(args.plan),
        release=safe_read_csv(args.release),
        manifest=safe_read_csv(args.manifest_summary),
    )
    prepared = None
    if args.prepare:
        row = select_row(summary, args.planned_slot, args.candidate_id)
        prepared = prepare_package(
            row=row,
            data_dir=args.data_dir,
            reference_registry=args.reference_registry,
            allow_review_gate=args.allow_review_gate,
        )
        summary = merged_rows(
            plan=safe_read_csv(args.plan),
            release=safe_read_csv(args.release),
            manifest=safe_read_csv(args.manifest_summary),
        )

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_csv, index=False)
    write_report(summary, args.report, args.output_csv, prepared)

    failures = 0
    if not summary.empty and "package_gate" in summary.columns:
        failures = int(summary["package_gate"].astype(str).str.startswith("FAIL").sum())
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.report}")
    print(f"package_failures={failures}")
    if prepared is not None:
        print(json.dumps(prepared, default=json_default, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
