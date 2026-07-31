#!/usr/bin/env python3
"""Analyze per-well impact of planned submission candidates versus a baseline."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_PLAN = Path("experiments/next_submission_batch_plan.csv")
DEFAULT_BASELINE = Path("artifacts/lucifer_baseline_repro_joezzzzz_v1/submission.csv")
DEFAULT_OUTPUT_CSV = Path("experiments/planned_candidate_well_impact.csv")
DEFAULT_SUMMARY_CSV = Path("experiments/planned_candidate_well_impact_summary.csv")
DEFAULT_REPORT = Path("reports/planned_candidate_well_impact_report.md")


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


def parse_ids(ids: pd.Series) -> pd.DataFrame:
    parts = ids.astype(str).str.rsplit("_", n=1, expand=True)
    if parts.shape[1] != 2:
        raise ValueError("submission ids must look like <well>_<row_idx>")
    return pd.DataFrame(
        {
            "id": ids.astype(str).to_numpy(),
            "well": parts[0].to_numpy(),
            "row_idx": pd.to_numeric(parts[1], errors="raise").astype(int).to_numpy(),
        }
    )


def read_submission(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if list(df.columns) != ["id", "tvt"]:
        raise ValueError(f"{path} must have columns ['id', 'tvt']; got {list(df.columns)}")
    df = df[["id", "tvt"]].copy()
    df["id"] = df["id"].astype(str)
    df["tvt"] = pd.to_numeric(df["tvt"], errors="raise").astype(float)
    if df["id"].duplicated().any():
        raise ValueError(f"{path} has duplicate ids")
    if not np.isfinite(df["tvt"].to_numpy(float)).all():
        raise ValueError(f"{path} contains non-finite tvt")
    return df


def impact_bucket(changed_well_count: int, top_contribution_frac: float, rmse_to_baseline: float) -> str:
    if not np.isfinite(rmse_to_baseline) or rmse_to_baseline <= 1e-9:
        return "NO_CHANGE"
    if changed_well_count <= 1:
        return "SINGLE_WELL_DOMINATED"
    if changed_well_count <= 2:
        return "SPARSE_INFORMATION"
    if np.isfinite(top_contribution_frac) and top_contribution_frac >= 0.75:
        return "HIGHLY_CONCENTRATED"
    if np.isfinite(top_contribution_frac) and top_contribution_frac >= 0.50:
        return "CONCENTRATED"
    return "BROAD"


def analyze_candidate(plan_row: pd.Series, baseline: pd.DataFrame, parsed: pd.DataFrame) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = Path(str(plan_row.get("path", "")))
    candidate = read_submission(path)
    if len(candidate) != len(baseline) or not candidate["id"].equals(baseline["id"]):
        raise ValueError(f"{path} id order does not match baseline")

    work = parsed.copy()
    work["baseline_tvt"] = baseline["tvt"].to_numpy(float)
    work["candidate_tvt"] = candidate["tvt"].to_numpy(float)
    work["diff"] = work["candidate_tvt"] - work["baseline_tvt"]
    work["abs_diff"] = np.abs(work["diff"])
    work["sq_diff"] = work["diff"] * work["diff"]
    changed = work["abs_diff"] > 1e-6
    total_sq = float(work["sq_diff"].sum())

    rows: list[dict[str, Any]] = []
    grouped = work.groupby("well", sort=False)
    for well, group in grouped:
        sq_sum = float(group["sq_diff"].sum())
        abs_vals = group["abs_diff"].to_numpy(float)
        diff_vals = group["diff"].to_numpy(float)
        changed_rows = int((abs_vals > 1e-6).sum())
        rows.append(
            {
                "planned_slot": plan_row.get("planned_slot", ""),
                "candidate_id": plan_row.get("candidate_id", ""),
                "family": plan_row.get("family", ""),
                "path": path.as_posix(),
                "well": well,
                "rows": int(len(group)),
                "changed_rows": changed_rows,
                "changed_frac": changed_rows / max(1, len(group)),
                "rmse_diff": float(np.sqrt(np.mean(diff_vals * diff_vals))),
                "mae_diff": float(np.mean(abs_vals)),
                "median_abs_diff": float(np.median(abs_vals)),
                "p95_abs_diff": float(np.quantile(abs_vals, 0.95)),
                "max_abs_diff": float(np.max(abs_vals)),
                "mean_signed_diff": float(np.mean(diff_vals)),
                "contribution_frac": sq_sum / total_sq if total_sq > 0 else 0.0,
                "row_idx_min": int(group["row_idx"].min()),
                "row_idx_max": int(group["row_idx"].max()),
            }
        )

    per_well = pd.DataFrame(rows).sort_values(["contribution_frac", "rmse_diff", "well"], ascending=[False, False, True])
    changed_wells = per_well[per_well["changed_rows"] > 0]
    top = per_well.iloc[0] if not per_well.empty else pd.Series(dtype=object)
    rmse_all = float(np.sqrt(total_sq / max(1, len(work))))
    summary = {
        "planned_slot": plan_row.get("planned_slot", ""),
        "candidate_id": plan_row.get("candidate_id", ""),
        "family": plan_row.get("family", ""),
        "path": path.as_posix(),
        "rows": int(len(work)),
        "changed_rows": int(changed.sum()),
        "changed_row_frac": int(changed.sum()) / max(1, len(work)),
        "changed_well_count": int(len(changed_wells)),
        "rmse_to_baseline": rmse_all,
        "mae_to_baseline": float(work["abs_diff"].mean()),
        "p95_abs_diff_to_baseline": float(work["abs_diff"].quantile(0.95)),
        "max_abs_diff_to_baseline": float(work["abs_diff"].max()),
        "top_well": top.get("well", ""),
        "top_well_contribution_frac": float(top.get("contribution_frac", np.nan)),
        "top_well_rmse_diff": float(top.get("rmse_diff", np.nan)),
        "top_well_changed_frac": float(top.get("changed_frac", np.nan)),
        "impact_bucket": impact_bucket(int(len(changed_wells)), float(top.get("contribution_frac", np.nan)), rmse_all),
    }
    return per_well.to_dict("records"), summary


def build_reports(plan: pd.DataFrame, baseline_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline = read_submission(baseline_path)
    parsed = parse_ids(baseline["id"])
    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for _, plan_row in plan.iterrows():
        rows, summary = analyze_candidate(plan_row, baseline, parsed)
        all_rows.extend(rows)
        summaries.append(summary)
    per_well = pd.DataFrame(all_rows)
    summary_df = pd.DataFrame(summaries)
    if not per_well.empty:
        per_well = per_well.sort_values(["planned_slot", "contribution_frac", "rmse_diff"], ascending=[True, False, False])
    if not summary_df.empty:
        summary_df = summary_df.sort_values(["planned_slot"])
    return per_well, summary_df


def write_report(per_well: pd.DataFrame, summary: pd.DataFrame, output: Path, csv_path: Path, summary_csv: Path) -> None:
    summary_cols = [
        "planned_slot",
        "candidate_id",
        "family",
        "impact_bucket",
        "changed_well_count",
        "changed_row_frac",
        "rmse_to_baseline",
        "top_well",
        "top_well_contribution_frac",
        "top_well_rmse_diff",
    ]
    summary_view = summary[[c for c in summary_cols if c in summary.columns]].copy() if not summary.empty else pd.DataFrame()
    top_cols = [
        "planned_slot",
        "candidate_id",
        "well",
        "contribution_frac",
        "rmse_diff",
        "changed_frac",
        "p95_abs_diff",
        "max_abs_diff",
        "mean_signed_diff",
    ]
    top = per_well.groupby("planned_slot", group_keys=False).head(5) if not per_well.empty else pd.DataFrame()
    top_view = top[[c for c in top_cols if c in top.columns]].copy() if not top.empty else pd.DataFrame()

    counts = summary["impact_bucket"].value_counts().rename_axis("impact_bucket").reset_index(name="count") if not summary.empty else pd.DataFrame()
    lines = [
        "# Planned Candidate Well Impact",
        "",
        "This report analyzes planned submission candidates per well against the active-account baseline output. It is local validation only and does not submit to Kaggle.",
        "",
        "## Impact Buckets",
        "",
        markdown_table(counts),
        "",
        "## Candidate Summary",
        "",
        markdown_table(summary_view),
        "",
        "## Top Impacted Wells",
        "",
        markdown_table(top_view),
        "",
        "## Interpretation",
        "",
        "- `SINGLE_WELL_DOMINATED` or `SPARSE_INFORMATION` candidates can still be useful information slots, but they should not be treated as broad model improvements without stronger evidence.",
        "- `CONCENTRATED` candidates need per-well review before release because leaderboard movement may depend on a small number of wells.",
        "- `BROAD` candidates change many wells and should be checked for hidden-format and physical-shape risk before any official submission.",
        "",
        "## Outputs",
        "",
        f"- `{csv_path.as_posix()}`",
        f"- `{summary_csv.as_posix()}`",
        f"- `{output.as_posix()}`",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--summary-csv", type=Path, default=DEFAULT_SUMMARY_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    plan = safe_read_csv(args.plan)
    per_well, summary = build_reports(plan, args.baseline)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    per_well.to_csv(args.output_csv, index=False)
    summary.to_csv(args.summary_csv, index=False)
    write_report(per_well, summary, args.report, args.output_csv, args.summary_csv)

    print(f"wrote {args.output_csv}")
    print(f"wrote {args.summary_csv}")
    print(f"wrote {args.report}")
    if not summary.empty:
        print(summary[["planned_slot", "candidate_id", "impact_bucket", "top_well", "top_well_contribution_frac"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
