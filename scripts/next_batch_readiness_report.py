#!/usr/bin/env python3
"""Build a next-batch readiness report from current ROGII experiment state."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_OUTPUT_CSV = Path("experiments/next_batch_readiness.csv")
DEFAULT_REPORT = Path("reports/next_batch_readiness_report.md")


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


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path)


def pending_official_rows(submissions: pd.DataFrame) -> pd.DataFrame:
    if submissions.empty or "status" not in submissions.columns:
        return pd.DataFrame()
    return submissions[submissions["status"].astype(str).str.lower().isin(["pending", "submitted", "running"])].copy()


def running_kernel_rows(kernels: pd.DataFrame) -> pd.DataFrame:
    if kernels.empty or "status" not in kernels.columns:
        return pd.DataFrame()
    return kernels[kernels["status"].astype(str).str.upper().isin(["RUNNING", "PENDING", "QUEUED"])].copy()


def candidate_family(path: str) -> str:
    text = path.lower()
    if "sp45_fleongg" in text:
        return "projection_learned_blend"
    if "sp45_projection" in text:
        return "projection_branch"
    if "fleongg_pretrained" in text:
        return "learned_signal"
    if "plateau_recent" in text:
        return "plateau_signal"
    if "gr_typewell" in text:
        return "gr_typewell_light"
    if "lucifer_baseline" in text or "submission_public_self_verified" in text:
        return "anchor_or_duplicate"
    if "fleongg_branch" in text:
        return "learned_signal"
    return "unknown"


def base_decision(row: pd.Series) -> str:
    risk = str(row.get("risk_grade", ""))
    dist = row.get("rmse_to_current_best_7p235", np.nan)
    if risk.startswith("reject") or risk == "high_shape_risk":
        return "BLOCK"
    if np.isfinite(dist) and dist < 0.25:
        return "HOLD_DUPLICATE"
    if np.isfinite(dist) and dist < 1.0:
        return "HOLD_LOW_UPSIDE"
    if risk == "plausible_submit_candidate":
        return "LOCAL_CANDIDATE"
    return "HOLD_REVIEW"


def pseudo_method_lookup(pseudo: pd.DataFrame, method: str) -> dict[str, float]:
    if pseudo.empty or "method" not in pseudo.columns:
        return {}
    rows = pseudo[pseudo["method"] == method]
    if rows.empty:
        return {}
    row = rows.iloc[0]
    return {
        "cv_weighted_rmse": float(row.get("weighted_rmse", np.nan)),
        "cv_mean_delta": float(row.get("mean_delta_rmse_vs_baseline", np.nan)),
        "cv_win_rate": float(row.get("win_rate_vs_baseline", np.nan)),
        "cv_fallback_rate": float(row.get("fallback_rate", np.nan)),
    }


def plateau_stability(plateau_sweep: pd.DataFrame) -> dict[str, float]:
    if plateau_sweep.empty or "delta_weighted_rmse_vs_last_value" not in plateau_sweep.columns:
        return {}
    default = plateau_sweep[plateau_sweep.get("is_default", False).astype(bool)] if "is_default" in plateau_sweep.columns else pd.DataFrame()
    ranked = plateau_sweep.sort_values(["weighted_rmse", "combo_id"]).reset_index(drop=True)
    out = {
        "plateau_sweep_combos": int(len(plateau_sweep)),
        "plateau_sweep_beat_count": int((plateau_sweep["delta_weighted_rmse_vs_last_value"] < 0).sum()),
        "plateau_sweep_beat_rate": float((plateau_sweep["delta_weighted_rmse_vs_last_value"] < 0).mean()),
    }
    if not default.empty:
        default_combo = int(default.iloc[0]["combo_id"])
        matches = ranked.index[ranked["combo_id"] == default_combo].tolist()
        out["plateau_default_rank"] = int(matches[0] + 1) if matches else np.nan
    return out


def readiness_status(
    row: pd.Series,
    pending_by_candidate: set[str],
    pending_count: int,
    running_reference_count: int,
) -> tuple[str, str]:
    path = str(row.get("path", ""))
    family = str(row.get("family", "unknown"))
    decision = str(row.get("base_decision", ""))

    if decision == "BLOCK":
        return "BLOCK", "Rejected by risk grade or shape risk."
    if decision == "HOLD_DUPLICATE":
        return "HOLD_DUPLICATE", "Too close to the active baseline; useful as anchor only."
    if decision == "HOLD_LOW_UPSIDE":
        return "HOLD_LOW_UPSIDE", "Likely safe but low information value."

    if family == "learned_signal" and "fleongg_pretrained" in path.lower():
        if "fleongg_pretrained_branch_calibration" in pending_by_candidate:
            return "WAIT_OFFICIAL_SCORE", "Equivalent learned-signal branch is already submitted as pending."
        return "HOLD_PENDING_ANCHOR", "Learned-signal value should be interpreted after active baseline score resolves."

    if family == "plateau_signal":
        return "HOLD_INFORMATION_SLOT", "Sparse local win; hold until pending anchors or stronger validation justify a slot."

    if pending_count or running_reference_count:
        return "HOLD_PENDING_CONTEXT", "Wait for pending official scores or running reference kernels before spending another slot."

    if decision == "LOCAL_CANDIDATE":
        return "READY_AFTER_AUDIT_REVIEW", "Eligible only after source/output audit and batch diversity review."
    return "HOLD_REVIEW", "Needs manual review before official submission."


def readiness_priority(status: str) -> int:
    order = {
        "WAIT_OFFICIAL_SCORE": 0,
        "HOLD_PENDING_CONTEXT": 1,
        "HOLD_INFORMATION_SLOT": 2,
        "READY_AFTER_AUDIT_REVIEW": 3,
        "HOLD_LOW_UPSIDE": 4,
        "HOLD_DUPLICATE": 5,
        "HOLD_REVIEW": 6,
        "BLOCK": 7,
    }
    return order.get(status, 99)


def build_candidate_rows(
    scores: pd.DataFrame,
    submissions: pd.DataFrame,
    kernels: pd.DataFrame,
    pseudo: pd.DataFrame,
    plateau_sweep: pd.DataFrame,
) -> pd.DataFrame:
    if scores.empty:
        return pd.DataFrame()
    focus = scores[
        scores["path"].astype(str).str.contains(
            "gr_typewell|plateau_recent|lucifer_baseline|fleongg_pretrained|sp45_projection|sp45_fleongg",
            case=False,
            regex=True,
            na=False,
        )
    ].copy()
    if focus.empty:
        focus = scores.copy()

    pending = pending_official_rows(submissions)
    running = running_kernel_rows(kernels)
    pending_by_candidate = set(pending.get("candidate_id", pd.Series(dtype=str)).astype(str))
    running_reference_count = int((running.get("purpose", pd.Series(dtype=str)).astype(str) == "reference_notebook_preflight").sum())

    focus["family"] = focus["path"].astype(str).map(candidate_family)
    focus["base_decision"] = focus.apply(base_decision, axis=1)
    status_notes = focus.apply(
        lambda row: readiness_status(row, pending_by_candidate, len(pending), running_reference_count),
        axis=1,
    )
    focus["readiness_status"] = [item[0] for item in status_notes]
    focus["next_action"] = [item[1] for item in status_notes]
    focus["priority"] = focus["readiness_status"].map(readiness_priority)

    plateau_cv = pseudo_method_lookup(pseudo, "plateau_recent_quantile")
    plateau_info = plateau_stability(plateau_sweep)
    for key, value in {**plateau_cv, **plateau_info}.items():
        focus[key] = np.nan
        focus.loc[focus["family"] == "plateau_signal", key] = value

    sort_cols = ["priority", "rmse_to_current_best_7p235", "path"]
    return focus.sort_values(sort_cols, na_position="last")


def write_report(
    candidates: pd.DataFrame,
    submissions: pd.DataFrame,
    kernels: pd.DataFrame,
    output: Path,
    csv_path: Path,
) -> None:
    pending = pending_official_rows(submissions)
    running = running_kernel_rows(kernels)
    ready = candidates[candidates["readiness_status"].astype(str).str.startswith("READY")] if not candidates.empty else pd.DataFrame()

    cols = [
        "path",
        "family",
        "readiness_status",
        "base_decision",
        "estimated_public_band",
        "rmse_to_current_best_7p235",
        "anchor_first_abs_p90",
        "jump_rate_abs_slope_gt3",
        "next_action",
    ]
    cols = [c for c in cols if c in candidates.columns]

    pending_cols = [c for c in ["submission_id", "candidate_id", "status", "decision", "public_score", "next_action"] if c in pending.columns]
    running_cols = [c for c in ["kernel_slug", "kernel_version", "purpose", "status", "next_action"] if c in running.columns]

    lines = [
        "# Next Batch Readiness Report",
        "",
        "This report ranks local candidates and blockers for the next official submission batch.",
        "",
        "## Current Blockers",
        "",
        f"- Pending official submissions: `{len(pending)}`",
        f"- Running Kaggle kernels: `{len(running)}`",
        f"- Ready-after-audit candidates with no context blocker: `{len(ready)}`",
        "",
        "## Pending Official Submissions",
        "",
        markdown_table(pending[pending_cols] if pending_cols else pending),
        "",
        "## Running Kernels",
        "",
        markdown_table(running[running_cols] if running_cols else running),
        "",
        "## Candidate Readiness",
        "",
        markdown_table(candidates[cols].head(30) if cols else candidates.head(30)),
        "",
        "## Recommendation",
        "",
    ]

    if len(pending) or len(running):
        lines.append("Do not spend another official slot on dependent variants until pending scores or reference kernels resolve.")
        lines.append("Continue polling, then audit completed kernel outputs before promoting any reference branch.")
    elif len(ready):
        lines.append("One or more candidates are ready for final source/output audit review before a planned official slot.")
    else:
        lines.append("No candidate is ready for an official slot without additional validation or audit work.")

    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- `{csv_path}`",
        ]
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-surrogate", type=Path, default=Path("experiments/local_surrogate_scores.csv"))
    parser.add_argument("--submission-ledger", type=Path, default=Path("experiments/submission_ledger.csv"))
    parser.add_argument("--kernel-ledger", type=Path, default=Path("experiments/kernel_run_ledger.csv"))
    parser.add_argument("--pseudo-summary", type=Path, default=Path("experiments/pseudo_test_cv_summary.csv"))
    parser.add_argument("--plateau-sweep", type=Path, default=Path("experiments/plateau_quantile_sweep.csv"))
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    scores = safe_read_csv(args.local_surrogate)
    submissions = safe_read_csv(args.submission_ledger)
    kernels = safe_read_csv(args.kernel_ledger)
    pseudo = safe_read_csv(args.pseudo_summary)
    plateau_sweep = safe_read_csv(args.plateau_sweep)

    candidates = build_candidate_rows(scores, submissions, kernels, pseudo, plateau_sweep)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(args.output_csv, index=False)
    write_report(candidates, submissions, kernels, args.report, args.output_csv)

    print(f"wrote {args.output_csv}")
    print(f"wrote {args.report}")
    if not candidates.empty:
        print(candidates[["path", "readiness_status", "next_action"]].head(12).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
