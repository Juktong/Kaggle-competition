#!/usr/bin/env python3
"""Create a compact decision report from local surrogate scores."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_OUTPUT = Path("reports/candidate_decision_report.md")


def fmt(value) -> str:
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


def decision(row: pd.Series) -> str:
    risk = str(row.get("risk_grade", ""))
    dist = row.get("rmse_to_current_best_7p235", np.nan)
    if risk.startswith("reject") or risk == "high_shape_risk":
        return "BLOCK"
    if np.isfinite(dist) and dist < 0.25:
        return "HOLD_DUPLICATE"
    if np.isfinite(dist) and dist < 1.0:
        return "HOLD_LOW_UPSIDE"
    if risk == "plausible_submit_candidate":
        return "SUBMIT_CANDIDATE"
    return "HOLD_NEEDS_REVIEW"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scores", type=Path, default=Path("experiments/local_surrogate_scores.csv"))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--focus",
        default="gr_typewell|plateau_recent|lucifer_baseline|fleongg_pretrained|sp45_projection|sp45_fleongg",
    )
    args = parser.parse_args()

    scores = pd.read_csv(args.scores)
    focus = scores[scores["path"].str.contains(args.focus, case=False, regex=True, na=False)].copy()
    if focus.empty:
        focus = scores.copy()
    focus["decision"] = focus.apply(decision, axis=1)

    sort_cols = [c for c in ["decision", "rmse_to_current_best_7p235", "risk_grade"] if c in focus.columns]
    if sort_cols:
        focus = focus.sort_values(sort_cols, na_position="last")

    cols = [
        "path",
        "decision",
        "risk_grade",
        "estimated_public_band",
        "rmse_to_current_best_7p235",
        "anchor_first_abs_p90",
        "jump_rate_abs_slope_gt3",
        "typewell_range_violation_frac",
    ]
    cols = [c for c in cols if c in focus.columns]

    lines = [
        "# Candidate Decision Report",
        "",
        "This report converts local surrogate rows into a lightweight pre-submission decision table.",
        "",
        "Decision meanings:",
        "",
        "- `BLOCK`: do not submit without a specific override reason.",
        "- `HOLD_DUPLICATE`: too close to the active baseline to spend a slot.",
        "- `HOLD_LOW_UPSIDE`: likely safe but low information value.",
        "- `SUBMIT_CANDIDATE`: eligible for official submission if source and format audits pass.",
        "- `HOLD_NEEDS_REVIEW`: inspect manually before any official submission.",
        "",
        "## Focus Candidates",
        "",
        markdown_table(focus[cols]),
        "",
        "## Recommendation",
        "",
    ]

    submit_count = int((focus["decision"] == "SUBMIT_CANDIDATE").sum())
    if submit_count:
        lines.append(f"{submit_count} focused candidate(s) are eligible for official submission after audit review.")
    else:
        lines.append("No focused candidate is currently strong enough to spend an official slot without new evidence.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
