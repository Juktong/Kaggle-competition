#!/usr/bin/env python3
"""Summarize local candidate artifact manifests for planned submission slots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_PLAN = Path("experiments/next_submission_batch_plan.csv")
DEFAULT_AUDIT = Path("experiments/candidate_audit_summary.csv")
DEFAULT_ARTIFACT_ROOT = Path("artifacts")
DEFAULT_OUTPUT_CSV = Path("experiments/candidate_artifact_manifest_summary.csv")
DEFAULT_REPORT = Path("reports/candidate_artifact_manifest_report.md")


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


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_manifests(root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_candidate: dict[str, dict[str, Any]] = {}
    by_source: dict[str, dict[str, Any]] = {}
    if not root.is_dir():
        return by_candidate, by_source

    for path in sorted(root.rglob("candidate_manifest.json")):
        obj = load_json(path)
        if not obj:
            continue
        obj["_manifest_path"] = path.as_posix()
        candidate_id = str(obj.get("candidate_id", "") or "")
        source_path = norm(obj.get("source_path"))
        if candidate_id:
            by_candidate[candidate_id] = obj
        if source_path:
            by_source[source_path] = obj
    return by_candidate, by_source


def audit_lookup(audit: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if audit.empty or "path" not in audit.columns:
        return {}
    records: dict[str, dict[str, Any]] = {}
    for _, row in audit.iterrows():
        records[norm(row.get("path"))] = row.to_dict()
    return records


def gate_for(
    manifest_exists: bool,
    source_path_matches_plan: bool,
    selected_output_exists: bool,
    audit_evidence_exists: bool,
    audit_gate: str,
) -> str:
    if not manifest_exists:
        return "FAIL_MISSING_MANIFEST"
    if not source_path_matches_plan:
        return "FAIL_SOURCE_MISMATCH"
    if not selected_output_exists:
        return "FAIL_SELECTED_OUTPUT_MISSING"
    if not audit_evidence_exists:
        return "FAIL_MISSING_AUDIT_EVIDENCE"
    if audit_gate not in {"AUDIT_PASS", "AUDIT_PASS_WARN_REVIEW"}:
        return "FAIL_AUDIT_GATE"
    return "PASS_SOURCE_POINTER"


def build_summary(plan: pd.DataFrame, audit: pd.DataFrame, artifact_root: Path) -> pd.DataFrame:
    by_candidate, by_source = load_manifests(artifact_root)
    audits = audit_lookup(audit)
    rows: list[dict[str, Any]] = []

    for _, row in plan.iterrows():
        candidate_id = str(row.get("candidate_id", "") or "")
        planned_path = norm(row.get("path"))
        manifest = by_candidate.get(candidate_id) or by_source.get(planned_path) or {}
        manifest_exists = bool(manifest)
        found_by = "candidate_id" if candidate_id in by_candidate else ("source_path" if planned_path in by_source else "")
        files = manifest.get("files", {}) if isinstance(manifest.get("files"), dict) else {}

        source_path = norm(manifest.get("source_path"))
        manifest_submission_path = norm(files.get("submission"))
        manifest_deep_audit_path = norm(files.get("deep_pre_submit_audit"))
        manifest_candidate_audit_path = norm(files.get("candidate_audit"))

        source_path_matches_plan = manifest_exists and source_path == planned_path
        source_path_exists = bool(source_path) and Path(source_path).is_file()
        manifest_submission_exists = bool(manifest_submission_path) and Path(manifest_submission_path).is_file()
        selected_output_exists = source_path_exists or manifest_submission_exists

        audit_row = audits.get(planned_path, {})
        audit_json = norm(audit_row.get("audit_json"))
        audit_json_exists = bool(audit_json) and Path(audit_json).is_file()
        audit_gate = str(audit_row.get("audit_gate", "") or "")
        audit_evidence_exists = audit_json_exists and audit_gate in {"AUDIT_PASS", "AUDIT_PASS_WARN_REVIEW"}

        gate = gate_for(
            manifest_exists=manifest_exists,
            source_path_matches_plan=source_path_matches_plan,
            selected_output_exists=selected_output_exists,
            audit_evidence_exists=audit_evidence_exists,
            audit_gate=audit_gate,
        )

        rows.append(
            {
                "planned_slot": row.get("planned_slot", ""),
                "candidate_id": candidate_id,
                "path": planned_path,
                "family": row.get("family", ""),
                "manifest_gate": gate,
                "manifest_path": manifest.get("_manifest_path", ""),
                "manifest_found_by": found_by,
                "source_path": source_path,
                "source_path_matches_plan": source_path_matches_plan,
                "source_path_exists": source_path_exists,
                "manifest_submission_path": manifest_submission_path,
                "manifest_submission_exists": manifest_submission_exists,
                "selected_output_exists": selected_output_exists,
                "manifest_deep_audit_path": manifest_deep_audit_path,
                "manifest_deep_audit_exists": bool(manifest_deep_audit_path) and Path(manifest_deep_audit_path).is_file(),
                "manifest_candidate_audit_path": manifest_candidate_audit_path,
                "manifest_candidate_audit_exists": bool(manifest_candidate_audit_path)
                and Path(manifest_candidate_audit_path).is_file(),
                "audit_json": audit_json,
                "audit_json_exists": audit_json_exists,
                "audit_gate": audit_gate,
                "audit_status": audit_row.get("audit_status", ""),
                "sha256_submission_csv": audit_row.get("sha256_submission_csv", ""),
                "notes": manifest.get("notes", ""),
            }
        )

    return pd.DataFrame(rows)


def write_report(summary: pd.DataFrame, output: Path, csv_path: Path, artifact_root: Path) -> None:
    counts = summary["manifest_gate"].value_counts().reset_index() if not summary.empty else pd.DataFrame()
    if not counts.empty:
        counts.columns = ["manifest_gate", "count"]

    display_cols = [
        "planned_slot",
        "candidate_id",
        "manifest_gate",
        "manifest_found_by",
        "source_path_exists",
        "audit_json_exists",
        "audit_gate",
        "notes",
    ]
    display = summary[[c for c in display_cols if c in summary.columns]].copy() if not summary.empty else pd.DataFrame()

    lines = [
        "# Candidate Artifact Manifest Report",
        "",
        "This report checks local ignored `candidate_manifest.json` files for the planned official-submission slots.",
        "",
        "## Summary",
        "",
        markdown_table(counts),
        "",
        "## Planned Slot Manifests",
        "",
        markdown_table(display),
        "",
        "## Gate Meaning",
        "",
        "- `PASS_SOURCE_POINTER`: the manifest exists, points to the exact planned output path, the selected output exists locally, and candidate audit evidence exists.",
        "- `FAIL_*`: an official submission should not proceed until the missing or mismatched evidence is fixed.",
        "",
        "## Outputs",
        "",
        f"- artifact root: `{artifact_root.as_posix()}`",
        f"- `{csv_path.as_posix()}`",
        f"- `{output.as_posix()}`",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    plan = safe_read_csv(args.plan)
    audit = safe_read_csv(args.audit)
    summary = build_summary(plan=plan, audit=audit, artifact_root=args.artifact_root)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_csv, index=False)
    write_report(summary, args.report, args.output_csv, args.artifact_root)

    failures = 0
    if not summary.empty and "manifest_gate" in summary.columns:
        failures = int((~summary["manifest_gate"].astype(str).str.startswith("PASS")).sum())
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.report}")
    print(f"manifest_failures={failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
