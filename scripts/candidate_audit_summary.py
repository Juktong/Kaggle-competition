#!/usr/bin/env python3
"""Summarize candidate audit evidence for next-batch submission decisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_READINESS = Path("experiments/next_batch_readiness.csv")
DEFAULT_ARTIFACT_ROOT = Path("artifacts")
DEFAULT_OUTPUT_CSV = Path("experiments/candidate_audit_summary.csv")
DEFAULT_REPORT = Path("reports/candidate_audit_summary_report.md")


READINESS_ORDER = {
    "READY_AFTER_AUDIT_REVIEW": 0,
    "HOLD_PENDING_CONTEXT": 1,
    "WAIT_OFFICIAL_SCORE": 2,
    "HOLD_INFORMATION_SLOT": 3,
    "HOLD_LOW_UPSIDE": 4,
    "HOLD_DUPLICATE": 5,
    "HOLD_REVIEW": 6,
    "BLOCK": 7,
}


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


def norm_path(value: Any) -> str:
    text = str(value or "").strip()
    return Path(text).as_posix() if text else ""


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def merge_record(records: dict[str, dict[str, Any]], key: str, update: dict[str, Any]) -> None:
    if not key:
        return
    record = records.setdefault(key, {"path": key})
    for name, value in update.items():
        if value is None:
            continue
        if name in {"warnings", "errors"}:
            existing = record.get(name, [])
            if not isinstance(existing, list):
                existing = []
            if isinstance(value, list):
                record[name] = sorted(set(existing + value))
            continue
        if name not in record or record[name] in ("", None, np.nan):
            record[name] = value
        elif name.endswith("_json"):
            record[name] = value


def collect_audits(artifact_root: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    if not artifact_root.is_dir():
        return records

    for path in sorted(artifact_root.rglob("*.json")):
        obj = load_json(path)
        if not obj:
            continue

        if "submission" in obj:
            key = norm_path(obj.get("submission"))
            merge_record(
                records,
                key,
                {
                    "audit_summary_json": path.as_posix(),
                    "audit_json": norm_path(obj.get("audit_json")),
                    "audit_status": obj.get("audit_status"),
                    "risk_status": obj.get("risk_status"),
                    "rows_audited": obj.get("rows"),
                    "sha256_submission_csv": obj.get("sha256_submission_csv"),
                    "warnings": obj.get("warnings", []),
                    "errors": obj.get("errors", []),
                },
            )

        if "submission_path" in obj:
            key = norm_path(obj.get("submission_path"))
            shape = obj.get("shape_metrics", {}) if isinstance(obj.get("shape_metrics"), dict) else {}
            refs = obj.get("reference_distances", {}) if isinstance(obj.get("reference_distances"), dict) else {}
            current_best = refs.get("current_best_7p235", {}) if isinstance(refs.get("current_best_7p235"), dict) else {}
            fleongg = refs.get("fleongg_branch_pending", {}) if isinstance(refs.get("fleongg_branch_pending"), dict) else {}
            merge_record(
                records,
                key,
                {
                    "audit_json": path.as_posix(),
                    "audit_status": obj.get("status"),
                    "risk_status": obj.get("risk_status"),
                    "rows_audited": obj.get("rows"),
                    "sha256_submission_csv": obj.get("sha256_submission_csv"),
                    "id_order_matches_sample": obj.get("id_order_matches_sample"),
                    "audit_anchor_first_abs_p90": shape.get("anchor_first_abs_p90"),
                    "audit_jump_rate_abs_slope_gt3": shape.get("jump_rate_abs_slope_gt3"),
                    "audit_typewell_range_violation_frac": shape.get("typewell_range_violation_frac"),
                    "audit_rmse_to_current_best_7p235": current_best.get("rmse"),
                    "audit_rmse_to_fleongg_pending": fleongg.get("rmse"),
                    "warnings": obj.get("warnings", []),
                    "errors": obj.get("errors", []),
                },
            )

    return records


def audit_gate(row: pd.Series) -> str:
    status = str(row.get("audit_status", "") or "")
    risk = str(row.get("risk_status", "") or "")
    errors = row.get("audit_error_count", np.nan)
    if not status or status == "nan":
        return "MISSING_AUDIT"
    if status != "PASS":
        return "AUDIT_FAIL"
    if np.isfinite(errors) and errors > 0:
        return "AUDIT_FAIL"
    if risk == "WARN":
        return "AUDIT_PASS_WARN_REVIEW"
    return "AUDIT_PASS"


def audit_gate_rank(gate: str) -> int:
    return {
        "AUDIT_PASS": 0,
        "AUDIT_PASS_WARN_REVIEW": 1,
        "MISSING_AUDIT": 8,
        "AUDIT_FAIL": 9,
    }.get(gate, 10)


def novelty_bucket(distance: Any) -> str:
    try:
        dist = float(distance)
    except Exception:
        return "unknown"
    if not np.isfinite(dist):
        return "unknown"
    if dist < 0.25:
        return "duplicate"
    if dist < 1.0:
        return "low"
    if dist < 3.0:
        return "moderate"
    if dist < 6.0:
        return "high"
    return "very_high"


def submission_gate(row: pd.Series) -> str:
    audit = str(row.get("audit_gate", ""))
    readiness = str(row.get("readiness_status", ""))
    if audit == "AUDIT_FAIL":
        return "BLOCK_AUDIT_FAIL"
    if audit == "MISSING_AUDIT":
        return "BLOCK_NEEDS_AUDIT"
    if readiness == "READY_AFTER_AUDIT_REVIEW":
        return "READY_REVIEW_WARNINGS" if audit == "AUDIT_PASS_WARN_REVIEW" else "READY"
    if readiness in {"HOLD_PENDING_CONTEXT", "WAIT_OFFICIAL_SCORE"}:
        return "AUDITED_WAIT_CONTEXT"
    if readiness in {"HOLD_DUPLICATE", "HOLD_LOW_UPSIDE"}:
        return readiness
    return readiness or "HOLD_REVIEW"


def build_summary(readiness: pd.DataFrame, audit_records: dict[str, dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for _, row in readiness.iterrows():
        path = norm_path(row.get("path"))
        audit = audit_records.get(path, {})
        out = row.to_dict()
        out.update({k: v for k, v in audit.items() if k != "path"})
        out["audit_warning_count"] = len(audit.get("warnings", [])) if audit else np.nan
        out["audit_error_count"] = len(audit.get("errors", [])) if audit else np.nan
        out["audit_gate"] = audit_gate(pd.Series(out))
        out["audit_gate_rank"] = audit_gate_rank(out["audit_gate"])
        out["readiness_rank"] = READINESS_ORDER.get(str(out.get("readiness_status", "")), 99)
        out["novelty_bucket"] = novelty_bucket(out.get("rmse_to_current_best_7p235"))
        out["submission_gate"] = submission_gate(pd.Series(out))
        rows.append(out)
    summary = pd.DataFrame(rows)
    if summary.empty:
        return summary
    sort_cols = ["audit_gate_rank", "readiness_rank", "rmse_to_current_best_7p235", "path"]
    return summary.sort_values(sort_cols, na_position="last")


def write_report(summary: pd.DataFrame, output: Path, csv_path: Path) -> None:
    cols = [
        "path",
        "family",
        "submission_gate",
        "readiness_status",
        "audit_gate",
        "estimated_public_band",
        "novelty_bucket",
        "rmse_to_current_best_7p235",
        "audit_rmse_to_fleongg_pending",
        "anchor_first_abs_p90",
        "jump_rate_abs_slope_gt3",
        "cv_mean_delta",
    ]
    cols = [c for c in cols if c in summary.columns]

    audit_counts = summary["audit_gate"].value_counts().rename_axis("audit_gate").reset_index(name="count") if not summary.empty else pd.DataFrame()
    gate_counts = summary["submission_gate"].value_counts().rename_axis("submission_gate").reset_index(name="count") if not summary.empty else pd.DataFrame()
    audited_wait = summary[summary.get("submission_gate", pd.Series(dtype=str)) == "AUDITED_WAIT_CONTEXT"] if not summary.empty else pd.DataFrame()
    missing = summary[summary.get("audit_gate", pd.Series(dtype=str)) == "MISSING_AUDIT"] if not summary.empty else pd.DataFrame()

    lines = [
        "# Candidate Audit Summary",
        "",
        "This report joins next-batch readiness with local audit JSON evidence.",
        "",
        "## Counts",
        "",
        f"- Candidates tracked: `{len(summary)}`",
        f"- Audited candidates waiting on external context: `{len(audited_wait)}`",
        f"- Candidates missing audit evidence: `{len(missing)}`",
        "",
        "## Audit Gates",
        "",
        markdown_table(audit_counts),
        "",
        "## Submission Gates",
        "",
        markdown_table(gate_counts),
        "",
        "## Ranked Candidates",
        "",
        markdown_table(summary[cols].head(30) if cols else summary.head(30)),
        "",
        "## Outputs",
        "",
        f"- `{csv_path.as_posix()}`",
        f"- `{output.as_posix()}`",
    ]

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness", type=Path, default=DEFAULT_READINESS)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    readiness = pd.read_csv(args.readiness)
    audits = collect_audits(args.artifact_root)
    summary = build_summary(readiness, audits)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_csv, index=False)
    write_report(summary, args.report, args.output_csv)

    print(f"wrote {args.output_csv}")
    print(f"wrote {args.report}")
    if not summary.empty:
        print(summary[["path", "submission_gate", "audit_gate", "readiness_status"]].head(12).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
