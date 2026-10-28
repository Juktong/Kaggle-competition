#!/usr/bin/env python3
"""Analyze pairwise diversity among planned submission candidates."""

from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_PLAN = Path("experiments/next_submission_batch_plan.csv")
DEFAULT_BASELINE = Path("artifacts/lucifer_baseline_repro_joezzzzz_v1/submission.csv")
DEFAULT_OUTPUT_CSV = Path("experiments/planned_candidate_diversity.csv")
DEFAULT_SUMMARY_CSV = Path("experiments/planned_candidate_diversity_summary.csv")
DEFAULT_REPORT = Path("reports/planned_candidate_diversity_report.md")


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


def rmse(a: np.ndarray, b: np.ndarray) -> float:
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    return float(np.sqrt(np.mean(d * d)))


def corr(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if np.std(a) <= 1e-12 or np.std(b) <= 1e-12:
        return np.nan
    return float(np.corrcoef(a, b)[0, 1])


def same_direction_frac(a: np.ndarray, b: np.ndarray) -> float:
    active = (np.abs(a) > 1e-6) | (np.abs(b) > 1e-6)
    if not np.any(active):
        return np.nan
    return float(np.mean(np.sign(a[active]) == np.sign(b[active])))


def redundancy_bucket(pair_rmse: float, diff_corr: float, same_dir: float) -> str:
    if pair_rmse < 0.25:
        return "NEAR_DUPLICATE"
    if pair_rmse < 0.75 and np.isfinite(diff_corr) and diff_corr > 0.98:
        return "HIGHLY_REDUNDANT"
    if pair_rmse < 1.25 and np.isfinite(diff_corr) and diff_corr > 0.95:
        return "RELATED_LOW_INCREMENT"
    if np.isfinite(diff_corr) and diff_corr < 0.25:
        return "DIVERSE"
    if np.isfinite(same_dir) and same_dir < 0.60:
        return "DIRECTIONALLY_DIVERSE"
    return "MODERATE_INCREMENT"


def load_candidates(plan: pd.DataFrame, baseline: pd.DataFrame) -> dict[int, dict[str, Any]]:
    candidates: dict[int, dict[str, Any]] = {}
    for _, row in plan.iterrows():
        slot = int(row.get("planned_slot"))
        path = Path(str(row.get("path", "")))
        sub = read_submission(path)
        if len(sub) != len(baseline) or not sub["id"].equals(baseline["id"]):
            raise ValueError(f"{path} id order does not match baseline")
        vals = sub["tvt"].to_numpy(float)
        base_vals = baseline["tvt"].to_numpy(float)
        candidates[slot] = {
            "planned_slot": slot,
            "candidate_id": row.get("candidate_id", ""),
            "family": row.get("family", ""),
            "slot_role": row.get("slot_role", ""),
            "path": path.as_posix(),
            "values": vals,
            "diff": vals - base_vals,
        }
    return candidates


def build_pairwise(plan: pd.DataFrame, baseline_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    baseline = read_submission(baseline_path)
    candidates = load_candidates(plan, baseline)
    rows: list[dict[str, Any]] = []
    for left_slot, right_slot in combinations(sorted(candidates), 2):
        left = candidates[left_slot]
        right = candidates[right_slot]
        pair_rmse = rmse(left["values"], right["values"])
        diff_corr = corr(left["diff"], right["diff"])
        same_dir = same_direction_frac(left["diff"], right["diff"])
        rows.append(
            {
                "left_slot": left_slot,
                "right_slot": right_slot,
                "left_candidate_id": left["candidate_id"],
                "right_candidate_id": right["candidate_id"],
                "left_family": left["family"],
                "right_family": right["family"],
                "pair_rmse": pair_rmse,
                "pair_mae": float(np.mean(np.abs(left["values"] - right["values"]))),
                "pair_p95_abs_diff": float(np.quantile(np.abs(left["values"] - right["values"]), 0.95)),
                "diff_corr_vs_baseline": diff_corr,
                "same_direction_frac": same_dir,
                "redundancy_bucket": redundancy_bucket(pair_rmse, diff_corr, same_dir),
                "left_path": left["path"],
                "right_path": right["path"],
            }
        )
    pairwise = pd.DataFrame(rows)
    if not pairwise.empty:
        pairwise = pairwise.sort_values(["redundancy_bucket", "pair_rmse", "left_slot", "right_slot"])

    summary_rows: list[dict[str, Any]] = []
    for slot, cand in candidates.items():
        related = pairwise[(pairwise["left_slot"] == slot) | (pairwise["right_slot"] == slot)]
        redundant = related[related["redundancy_bucket"].isin(["NEAR_DUPLICATE", "HIGHLY_REDUNDANT", "RELATED_LOW_INCREMENT"])]
        summary_rows.append(
            {
                "planned_slot": slot,
                "candidate_id": cand["candidate_id"],
                "family": cand["family"],
                "slot_role": cand["slot_role"],
                "path": cand["path"],
                "min_pair_rmse": float(related["pair_rmse"].min()) if not related.empty else np.nan,
                "max_diff_corr": float(related["diff_corr_vs_baseline"].max()) if not related.empty else np.nan,
                "redundant_pair_count": int(len(redundant)),
                "most_similar_slot": int(
                    related.sort_values("pair_rmse").iloc[0]["right_slot"]
                    if not related.empty and int(related.sort_values("pair_rmse").iloc[0]["left_slot"]) == slot
                    else related.sort_values("pair_rmse").iloc[0]["left_slot"]
                )
                if not related.empty
                else "",
                "diversity_flag": "REDUNDANT_REVIEW" if len(redundant) else "OK",
            }
        )
    summary = pd.DataFrame(summary_rows).sort_values("planned_slot")
    return pairwise, summary


def write_report(pairwise: pd.DataFrame, summary: pd.DataFrame, output: Path, csv_path: Path, summary_csv: Path) -> None:
    counts = pairwise["redundancy_bucket"].value_counts().rename_axis("redundancy_bucket").reset_index(name="count") if not pairwise.empty else pd.DataFrame()
    pair_cols = [
        "left_slot",
        "right_slot",
        "left_family",
        "right_family",
        "pair_rmse",
        "diff_corr_vs_baseline",
        "same_direction_frac",
        "redundancy_bucket",
    ]
    summary_cols = [
        "planned_slot",
        "candidate_id",
        "family",
        "min_pair_rmse",
        "max_diff_corr",
        "redundant_pair_count",
        "most_similar_slot",
        "diversity_flag",
    ]
    lines = [
        "# Planned Candidate Diversity",
        "",
        "This report measures pairwise output diversity among planned submission slots. It is local validation only and does not submit to Kaggle.",
        "",
        "## Redundancy Buckets",
        "",
        markdown_table(counts),
        "",
        "## Candidate Summary",
        "",
        markdown_table(summary[[c for c in summary_cols if c in summary.columns]] if not summary.empty else summary),
        "",
        "## Pairwise Distances",
        "",
        markdown_table(pairwise[[c for c in pair_cols if c in pairwise.columns]] if not pairwise.empty else pairwise),
        "",
        "## Interpretation",
        "",
        "- `NEAR_DUPLICATE`, `HIGHLY_REDUNDANT`, and `RELATED_LOW_INCREMENT` pairs should not both be submitted unless they answer a deliberate calibration-sweep question.",
        "- High correlation among blend weights is expected, but it reduces information value if daily slots are scarce.",
        "- Diverse candidates can still be bad; this report only checks redundancy, not hidden-label accuracy.",
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
    pairwise, summary = build_pairwise(plan, args.baseline)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    pairwise.to_csv(args.output_csv, index=False)
    summary.to_csv(args.summary_csv, index=False)
    write_report(pairwise, summary, args.report, args.output_csv, args.summary_csv)

    print(f"wrote {args.output_csv}")
    print(f"wrote {args.summary_csv}")
    print(f"wrote {args.report}")
    if not summary.empty:
        print(summary[["planned_slot", "candidate_id", "min_pair_rmse", "max_diff_corr", "diversity_flag"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
