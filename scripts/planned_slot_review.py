#!/usr/bin/env python3
"""Review planned submission slots by combining gates, impact, and diversity evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_PLAN = Path("experiments/next_submission_batch_plan.csv")
DEFAULT_RELEASE = Path("experiments/submission_release_gate.csv")
DEFAULT_FINAL_PACKAGE = Path("experiments/final_submission_package_summary.csv")
DEFAULT_IMPACT = Path("experiments/planned_candidate_well_impact_summary.csv")
DEFAULT_DIVERSITY = Path("experiments/planned_candidate_diversity_summary.csv")
DEFAULT_OUTPUT_CSV = Path("experiments/planned_slot_review.csv")
DEFAULT_REPORT = Path("reports/planned_slot_review.md")


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


def merge_optional(left: pd.DataFrame, right: pd.DataFrame, columns: list[str], suffix: str = "") -> pd.DataFrame:
    if left.empty or right.empty or "planned_slot" not in right.columns:
        return left
    cols = [col for col in columns if col in right.columns]
    if "planned_slot" not in cols:
        cols = ["planned_slot"] + cols
    return left.merge(right[cols], on="planned_slot", how="left", suffixes=("", suffix))


def review_row(row: pd.Series) -> tuple[str, str, str]:
    release_gate = str(row.get("release_gate", "") or "")
    audit_gate = str(row.get("audit_gate", "") or "")
    package_gate = str(row.get("package_gate", "") or "")
    diversity_flag = str(row.get("diversity_flag", "") or "")
    impact_bucket = str(row.get("impact_bucket", "") or "")
    slot_role = str(row.get("slot_role", "") or "")
    family = str(row.get("family", "") or "")

    if release_gate == "BLOCKED_STRATEGY_PIVOT":
        return "BUILD_NEW_ARCHITECTURE_FIRST", "BLOCK", "Official calibration rejected the planned branch family; build new structural candidates before submitting."
    if release_gate.startswith("BLOCKED") or release_gate == "REVIEW_LEDGER_UPDATES":
        return "HOLD_EXTERNAL_CONTEXT", "WAIT", f"Release gate is {release_gate}; do not submit or package yet."
    if audit_gate not in {"AUDIT_PASS", "AUDIT_PASS_WARN_REVIEW"}:
        return "BLOCK_AUDIT", "BLOCK", f"Audit gate is {audit_gate}."
    if package_gate.startswith("FAIL"):
        return "BLOCK_PACKAGE", "BLOCK", f"Final package gate is {package_gate}."
    if diversity_flag == "REDUNDANT_REVIEW":
        if slot_role == "calibration_sweep" or family == "projection_learned_blend":
            return (
                "KEEP_ONLY_IF_CALIBRATION_SWEEP",
                "REVIEW",
                "This slot is redundant with nearby blend weights; keep only if the batch explicitly spends slots to map the blend curve.",
            )
        return "REVIEW_REDUNDANT", "REVIEW", "Candidate is redundant with another planned slot."
    if impact_bucket == "SINGLE_WELL_DOMINATED":
        return "SPARSE_INFO_SLOT_REVIEW", "REVIEW", "Candidate is single-well dominated; use only as a sparse information slot."
    if impact_bucket in {"BROAD", "CONCENTRATED"} and diversity_flag == "OK":
        return "KEEP_FOR_FINAL_REVIEW", "KEEP", "Candidate has non-redundant planned evidence; keep for final release review after external blockers clear."
    return "REVIEW_REQUIRED", "REVIEW", "Candidate needs final human/strategy review."


def evidence_row(row: pd.Series) -> tuple[str, str, str]:
    diversity_flag = str(row.get("diversity_flag", "") or "")
    impact_bucket = str(row.get("impact_bucket", "") or "")
    slot_role = str(row.get("slot_role", "") or "")
    family = str(row.get("family", "") or "")

    if diversity_flag == "REDUNDANT_REVIEW":
        if slot_role == "calibration_sweep" or family == "projection_learned_blend":
            return (
                "KEEP_ONLY_IF_CALIBRATION_SWEEP",
                "REVIEW",
                "Redundant with nearby blend weights; keep only for deliberate blend-curve calibration.",
            )
        return "REVIEW_REDUNDANT", "REVIEW", "Redundant with another planned slot."
    if impact_bucket == "SINGLE_WELL_DOMINATED":
        return "SPARSE_INFO_SLOT_REVIEW", "REVIEW", "Single-well dominated; use as sparse information slot only."
    if impact_bucket in {"BROAD", "CONCENTRATED"} and diversity_flag == "OK":
        return "KEEP_FOR_FINAL_REVIEW", "KEEP", "Non-redundant planned evidence; keep for final review after gates clear."
    return "REVIEW_REQUIRED", "REVIEW", "Needs final human/strategy review."


def build_review(
    plan: pd.DataFrame,
    release: pd.DataFrame,
    final_package: pd.DataFrame,
    impact: pd.DataFrame,
    diversity: pd.DataFrame,
) -> pd.DataFrame:
    if plan.empty:
        return pd.DataFrame()
    out = plan.copy()
    out = merge_optional(out, release, ["planned_slot", "release_gate", "release_reason"])
    out = merge_optional(out, final_package, ["planned_slot", "package_gate", "package_reason"])
    out = merge_optional(
        out,
        impact,
        [
            "planned_slot",
            "impact_bucket",
            "changed_well_count",
            "changed_row_frac",
            "top_well",
            "top_well_contribution_frac",
        ],
    )
    out = merge_optional(
        out,
        diversity,
        [
            "planned_slot",
            "diversity_flag",
            "min_pair_rmse",
            "max_diff_corr",
            "redundant_pair_count",
            "most_similar_slot",
        ],
    )

    reviews = out.apply(review_row, axis=1)
    out["slot_review"] = [r[0] for r in reviews]
    out["slot_action"] = [r[1] for r in reviews]
    out["slot_review_reason"] = [r[2] for r in reviews]
    evidence = out.apply(evidence_row, axis=1)
    out["evidence_review"] = [r[0] for r in evidence]
    out["evidence_action"] = [r[1] for r in evidence]
    out["evidence_reason"] = [r[2] for r in evidence]
    return out.sort_values("planned_slot")


def write_report(review: pd.DataFrame, output: Path, csv_path: Path) -> None:
    counts = review["slot_review"].value_counts().rename_axis("slot_review").reset_index(name="count") if not review.empty else pd.DataFrame()
    cols = [
        "planned_slot",
        "slot_role",
        "family",
        "slot_review",
        "slot_action",
        "evidence_review",
        "evidence_action",
        "release_gate",
        "impact_bucket",
        "diversity_flag",
        "min_pair_rmse",
        "top_well",
        "slot_review_reason",
    ]
    cols = [c for c in cols if c in review.columns]
    lines = [
        "# Planned Slot Review",
        "",
        "This report combines release gates, audit readiness, final-package state, per-well impact, and pairwise diversity into one slot-level review. It does not submit to Kaggle.",
        "",
        "## Review Counts",
        "",
        markdown_table(counts),
        "",
        "## Slot Review",
        "",
        markdown_table(review[cols] if cols else review),
        "",
        "## Release Interpretation",
        "",
        "- `HOLD_EXTERNAL_CONTEXT`: keep blocked until scores/kernel outcomes resolve.",
        "- `BUILD_NEW_ARCHITECTURE_FIRST`: do not spend official slots on the current planned family; create new structural candidates first.",
        "- `evidence_review` shows the latent quality/diversity decision even while the release gate is blocked.",
        "- `KEEP_ONLY_IF_CALIBRATION_SWEEP`: the slot is redundant, but may be kept if the explicit experiment is to map a blend curve.",
        "- `SPARSE_INFO_SLOT_REVIEW`: use only as an information slot, not as broad model promotion.",
        "- `KEEP_FOR_FINAL_REVIEW`: candidate has enough non-redundant evidence for final review once gates clear.",
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
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--final-package", type=Path, default=DEFAULT_FINAL_PACKAGE)
    parser.add_argument("--impact", type=Path, default=DEFAULT_IMPACT)
    parser.add_argument("--diversity", type=Path, default=DEFAULT_DIVERSITY)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    review = build_review(
        plan=safe_read_csv(args.plan),
        release=safe_read_csv(args.release),
        final_package=safe_read_csv(args.final_package),
        impact=safe_read_csv(args.impact),
        diversity=safe_read_csv(args.diversity),
    )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    review.to_csv(args.output_csv, index=False)
    write_report(review, args.report, args.output_csv)

    print(f"wrote {args.output_csv}")
    print(f"wrote {args.report}")
    if not review.empty:
        print(review[["planned_slot", "candidate_id", "slot_review", "slot_action"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
