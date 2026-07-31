#!/usr/bin/env python3
"""Build branch rules for pending ROGII scores and reference kernels."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_SUBMISSIONS = Path("experiments/submission_ledger.csv")
DEFAULT_KERNELS = Path("experiments/kernel_run_ledger.csv")
DEFAULT_PLAN = Path("experiments/next_submission_batch_plan.csv")
DEFAULT_OUTPUT_CSV = Path("experiments/result_branch_matrix.csv")
DEFAULT_REPORT = Path("reports/result_branch_matrix.md")


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


def pending_submission(submissions: pd.DataFrame, candidate_id: str) -> dict[str, str]:
    if submissions.empty or "candidate_id" not in submissions.columns:
        return {}
    rows = submissions[submissions["candidate_id"].astype(str) == candidate_id]
    if rows.empty:
        return {}
    row = rows.iloc[-1].fillna("")
    return {key: str(row.get(key, "")) for key in submissions.columns}


def kernel_row(kernels: pd.DataFrame, slug: str) -> dict[str, str]:
    if kernels.empty or "kernel_slug" not in kernels.columns:
        return {}
    rows = kernels[kernels["kernel_slug"].astype(str) == slug]
    if rows.empty:
        return {}
    row = rows.iloc[-1].fillna("")
    return {key: str(row.get(key, "")) for key in kernels.columns}


def paths_by_family(plan: pd.DataFrame, family: str) -> str:
    if plan.empty or "family" not in plan.columns:
        return ""
    rows = plan[plan["family"].astype(str) == family]
    return "; ".join(rows.get("path", pd.Series(dtype=str)).astype(str).tolist())


def slots_by_role(plan: pd.DataFrame, role: str) -> str:
    if plan.empty or "slot_role" not in plan.columns:
        return ""
    rows = plan[plan["slot_role"].astype(str) == role]
    return ", ".join(rows.get("planned_slot", pd.Series(dtype=str)).astype(str).tolist())


def build_matrix(submissions: pd.DataFrame, kernels: pd.DataFrame, plan: pd.DataFrame) -> pd.DataFrame:
    baseline = pending_submission(submissions, "lucifer_baseline_repro_joezzzzz")
    fleongg = pending_submission(submissions, "fleongg_pretrained_branch_calibration")
    deg = kernel_row(kernels, "joezzzzz/rogii-degnonguidi-7159-preflight-codex")

    baseline_id = baseline.get("submission_id", "54174151")
    fleongg_id = fleongg.get("submission_id", "54174876")
    deg_version = deg.get("kernel_version", "6")

    sp45_paths = paths_by_family(plan, "projection_branch")
    blend_paths = paths_by_family(plan, "projection_learned_blend")
    plateau_paths = paths_by_family(plan, "plateau_signal")
    blend_slots = slots_by_role(plan, "calibration_sweep")

    rows = [
        {
            "branch_id": "B01_baseline_anchor_valid",
            "trigger": f"{baseline_id} completes with plausible active-account baseline score",
            "evidence_to_check": "public_score present, nonblank, and close to expected 7.235/7.263 reference band; no scoring failure",
            "decision": "promote_baseline_anchor",
            "slot_effect": "Allow SP45 projection final review; keep release gate blocked until Fleongg and Degnonguidi dependency rules are resolved.",
            "candidate_effect": sp45_paths,
            "next_command": "python3 scripts/poll_and_refresh_state.py --apply-submission-updates",
        },
        {
            "branch_id": "B02_baseline_anchor_failed",
            "trigger": f"{baseline_id} completes blank, catastrophic, or far outside expected baseline band",
            "evidence_to_check": "blank score, operational failure, or public_score much worse than trusted references",
            "decision": "block_dependent_submissions",
            "slot_effect": "Do not release SP45, blend, or plateau slots; repair active-account baseline reproduction first.",
            "candidate_effect": "; ".join([sp45_paths, blend_paths, plateau_paths]).strip("; "),
            "next_command": "record failure, patch baseline path, rerun source/output audit before any new official submission",
        },
        {
            "branch_id": "B03_fleongg_competitive",
            "trigger": f"{baseline_id} anchor is valid and {fleongg_id} is competitive with baseline",
            "evidence_to_check": "Fleongg public_score is better than, tied with, or close enough to baseline to justify ensemble diversity",
            "decision": "prioritize_blend_sweep",
            "slot_effect": f"Keep SP45+Fleongg calibration sweep slots {blend_slots}; release only after final audit/release-gate review.",
            "candidate_effect": blend_paths,
            "next_command": "python3 scripts/poll_and_refresh_state.py --apply-submission-updates",
        },
        {
            "branch_id": "B04_fleongg_weak",
            "trigger": f"{baseline_id} anchor is valid and {fleongg_id} is materially worse",
            "evidence_to_check": "Fleongg public_score is clearly worse than baseline or repeats known weak learned-signal behavior",
            "decision": "downweight_blends",
            "slot_effect": "Prefer pure SP45 projection; keep at most one blend as an information slot, and only if a planned question remains.",
            "candidate_effect": blend_paths,
            "next_command": "rerun next_submission_batch_plan after marking Fleongg as weak calibration",
        },
        {
            "branch_id": "B05_degnonguidi_complete_clean",
            "trigger": f"Degnonguidi v{deg_version} reaches COMPLETE and output audit passes",
            "evidence_to_check": "kernel status COMPLETE; output downloaded; deep audit PASS; output is distinct from current plan",
            "decision": "insert_degnonguidi_candidate",
            "slot_effect": "Insert best distinct Degnonguidi output ahead of lower-priority blend or plateau slot.",
            "candidate_effect": "pending Degnonguidi output artifact",
            "next_command": "python3 scripts/audit_kernel_output.py --kernel joezzzzz/rogii-degnonguidi-7159-preflight-codex --output-dir artifacts/kernel_outputs/rogii-degnonguidi-7159-preflight-codex_v6 --kaggle-bin /home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle --force-download",
        },
        {
            "branch_id": "B06_degnonguidi_error_or_defer",
            "trigger": f"Degnonguidi v{deg_version} errors, stalls beyond useful window, or is explicitly deferred",
            "evidence_to_check": "kernel status ERROR/CANCELLED, repeated runtime incompatibility, or deliberate defer decision in log",
            "decision": "release_without_degnonguidi_if_scores_allow",
            "slot_effect": "If baseline/Fleongg scores are resolved and release gate passes, allow Baidalin-derived slots to proceed without waiting for Degnonguidi.",
            "candidate_effect": "; ".join([sp45_paths, blend_paths]).strip("; "),
            "next_command": "update kernel ledger, record deferral reason, rerun poll_and_refresh_state.py",
        },
        {
            "branch_id": "B07_no_external_change",
            "trigger": "No new official score and no terminal kernel status",
            "evidence_to_check": "poll refresh reports submission_updates_detected=0 and kernel_updates_detected=0",
            "decision": "continue_preparation_no_submit",
            "slot_effect": "Keep all planned slots blocked; continue local validation, audit coverage, and planning consistency work.",
            "candidate_effect": "; ".join([sp45_paths, blend_paths, plateau_paths]).strip("; "),
            "next_command": "python3 scripts/poll_and_refresh_state.py",
        },
    ]
    return pd.DataFrame(rows)


def write_report(matrix: pd.DataFrame, plan: pd.DataFrame, output: Path, csv_path: Path) -> None:
    plan_cols = [
        "planned_slot",
        "slot_role",
        "family",
        "current_action",
        "release_condition",
        "path",
    ]
    plan_cols = [col for col in plan_cols if col in plan.columns]
    lines = [
        "# Result Branch Matrix",
        "",
        "This report maps pending public scores and reference-kernel outcomes to concrete next actions.",
        "",
        "## Current Planned Slots",
        "",
        markdown_table(plan[plan_cols] if plan_cols else plan),
        "",
        "## Branch Rules",
        "",
        markdown_table(matrix),
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
    parser.add_argument("--submissions", type=Path, default=DEFAULT_SUBMISSIONS)
    parser.add_argument("--kernels", type=Path, default=DEFAULT_KERNELS)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    submissions = safe_read_csv(args.submissions)
    kernels = safe_read_csv(args.kernels)
    plan = safe_read_csv(args.plan)
    matrix = build_matrix(submissions, kernels, plan)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    matrix.to_csv(args.output_csv, index=False)
    write_report(matrix, plan, args.report, args.output_csv)

    print(f"wrote {args.output_csv}")
    print(f"wrote {args.report}")
    print(matrix[["branch_id", "decision"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
