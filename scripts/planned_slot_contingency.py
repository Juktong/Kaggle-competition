#!/usr/bin/env python3
"""Build contingency rules for planned submission slots after pending results resolve."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_SLOT_REVIEW = Path("experiments/planned_slot_review.csv")
DEFAULT_READINESS = Path("experiments/next_batch_readiness.csv")
DEFAULT_OUTPUT_CSV = Path("experiments/planned_slot_contingency.csv")
DEFAULT_POOL_CSV = Path("experiments/planned_slot_replacement_pool.csv")
DEFAULT_REPORT = Path("reports/planned_slot_contingency.md")


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


def join_slots(values: list[Any]) -> str:
    cleaned = [str(int(v)) if isinstance(v, (int, float, np.integer, np.floating)) and np.isfinite(v) else str(v) for v in values]
    return ", ".join(cleaned)


def slots_where(review: pd.DataFrame, mask: pd.Series) -> str:
    if review.empty or "planned_slot" not in review.columns:
        return ""
    rows = review[mask].copy()
    return join_slots(rows["planned_slot"].tolist())


def best_single_blend_slot(review: pd.DataFrame) -> str:
    if review.empty or "family" not in review.columns:
        return ""
    blends = review[review["family"].astype(str) == "projection_learned_blend"].copy()
    if blends.empty:
        return ""
    if "audit_rmse_to_fleongg_pending" in blends.columns:
        blends["_rank_metric"] = pd.to_numeric(blends["audit_rmse_to_fleongg_pending"], errors="coerce").fillna(-1)
    else:
        blends["_rank_metric"] = pd.to_numeric(blends.get("rmse_to_current_best_7p235", pd.Series(dtype=float)), errors="coerce").fillna(-1)
    row = blends.sort_values(["_rank_metric", "planned_slot"], ascending=[False, True]).iloc[0]
    return join_slots([row["planned_slot"]])


def role_for_pool_row(row: pd.Series, planned_paths: set[str]) -> tuple[str, str, int]:
    path = str(row.get("path", ""))
    family = str(row.get("family", ""))
    readiness = str(row.get("readiness_status", ""))
    band = str(row.get("estimated_public_band", ""))

    if path in planned_paths:
        return "already_planned", "Already represented in the current 5-slot plan.", -100
    if family == "projection_branch" and readiness == "HOLD_PENDING_CONTEXT":
        return "backup_projection_review", "Backup projection branch; review source/output distance before replacing a slot.", 70
    if family == "projection_learned_blend" and readiness == "HOLD_PENDING_CONTEXT":
        return "alternate_blend_weight_only", "Another nearby blend weight; useful only for a deliberate blend curve.", 45
    if family == "gr_typewell_light":
        return "conservative_low_upside_backup", "Safe-ish low-upside backup; use only if more informative slots are unavailable.", 25
    if family == "plateau_signal" or readiness == "HOLD_INFORMATION_SLOT":
        return "sparse_information_review", "Sparse information candidate; do not treat as broad promotion.", 35
    if family == "learned_signal" or readiness == "WAIT_OFFICIAL_SCORE":
        return "pending_equivalent_not_replacement", "Equivalent learned signal is already pending as an official submission.", 5
    if readiness == "HOLD_DUPLICATE":
        return "do_not_use_duplicate", "Duplicate/anchor output; do not use as replacement.", -80
    if readiness == "HOLD_LOW_UPSIDE" or band == "likely_around_7p235_low_upside":
        return "low_information_backup", "Low information value; keep as last resort only.", 10
    return "manual_review", "Needs manual review before replacing a planned slot.", 20


def build_replacement_pool(readiness: pd.DataFrame, review: pd.DataFrame) -> pd.DataFrame:
    if readiness.empty:
        return pd.DataFrame()
    planned_paths = set(review.get("path", pd.Series(dtype=str)).astype(str))
    pool = readiness.copy()
    role_rows = pool.apply(lambda row: role_for_pool_row(row, planned_paths), axis=1)
    pool["replacement_role"] = [row[0] for row in role_rows]
    pool["replacement_reason"] = [row[1] for row in role_rows]
    pool["replacement_rank"] = [row[2] for row in role_rows]
    if "rmse_to_current_best_7p235" in pool.columns:
        dist = pd.to_numeric(pool["rmse_to_current_best_7p235"], errors="coerce")
        pool["replacement_rank"] += np.where((dist >= 1.0) & (dist <= 5.0), 8, 0)
        pool["replacement_rank"] += np.where(dist < 1.0, -15, 0)
    cols = [
        "path",
        "family",
        "readiness_status",
        "estimated_public_band",
        "rmse_to_current_best_7p235",
        "replacement_role",
        "replacement_rank",
        "replacement_reason",
        "next_action",
    ]
    cols = [col for col in cols if col in pool.columns]
    return pool[cols].sort_values(["replacement_rank", "path"], ascending=[False, True])


def top_replacements(pool: pd.DataFrame, roles: set[str], limit: int = 3) -> str:
    if pool.empty or "replacement_role" not in pool.columns:
        return ""
    rows = pool[pool["replacement_role"].isin(roles)].head(limit)
    return "; ".join(rows.get("path", pd.Series(dtype=str)).astype(str).tolist())


def build_contingency(review: pd.DataFrame, pool: pd.DataFrame) -> pd.DataFrame:
    all_slots = join_slots(review.get("planned_slot", pd.Series(dtype=int)).tolist()) if not review.empty else ""
    final_slots = slots_where(review, review.get("evidence_review", pd.Series(dtype=str)).astype(str) == "KEEP_FOR_FINAL_REVIEW")
    calibration_slots = slots_where(review, review.get("evidence_review", pd.Series(dtype=str)).astype(str) == "KEEP_ONLY_IF_CALIBRATION_SWEEP")
    sparse_slots = slots_where(review, review.get("evidence_review", pd.Series(dtype=str)).astype(str) == "SPARSE_INFO_SLOT_REVIEW")
    single_blend = best_single_blend_slot(review)
    redundant_blends = slots_where(
        review,
        (review.get("evidence_review", pd.Series(dtype=str)).astype(str) == "KEEP_ONLY_IF_CALIBRATION_SWEEP")
        & (review.get("planned_slot", pd.Series(dtype=int)).astype(str) != single_blend),
    )
    replacement_candidates = top_replacements(
        pool,
        {"backup_projection_review", "sparse_information_review", "conservative_low_upside_backup", "low_information_backup"},
        limit=4,
    )

    rows = [
        {
            "scenario_id": "S01_no_external_change",
            "trigger": "No new official score and Degnonguidi remains non-terminal.",
            "release_action": "WAIT_NO_SUBMIT",
            "keep_slots": all_slots,
            "review_slots": all_slots,
            "replace_slots": "",
            "drop_slots": "",
            "official_slot_target": "0 now",
            "new_candidate_needed": 0,
            "replacement_candidates": "",
            "rationale": "Current release gate is blocked by external context; keep preparing but do not spend official slots.",
            "next_command": "python3 scripts/poll_and_refresh_state.py",
        },
        {
            "scenario_id": "S02_baseline_valid_fleongg_competitive",
            "trigger": "Baseline anchor scores in the expected band and Fleongg is competitive enough to justify ensemble calibration.",
            "release_action": "FINAL_REVIEW_BLEND_SWEEP",
            "keep_slots": ", ".join(x for x in [final_slots, calibration_slots] if x),
            "review_slots": sparse_slots,
            "replace_slots": "",
            "drop_slots": "",
            "official_slot_target": "4-5 after gates clear",
            "new_candidate_needed": 0,
            "replacement_candidates": "",
            "rationale": "The three blend slots are redundant but acceptable if the explicit question is the low-dimensional blend curve.",
            "next_command": "python3 scripts/final_submission_package.py --prepare --planned-slot N",
        },
        {
            "scenario_id": "S03_baseline_valid_fleongg_weak",
            "trigger": "Baseline anchor is valid but Fleongg is materially worse than the active baseline.",
            "release_action": "PARTIAL_RELEASE_NEEDS_REPLACEMENTS",
            "keep_slots": ", ".join(x for x in [final_slots, single_blend, sparse_slots] if x),
            "review_slots": single_blend,
            "replace_slots": redundant_blends,
            "drop_slots": redundant_blends,
            "official_slot_target": "2-3 current slots plus 1-2 replacements",
            "new_candidate_needed": 2,
            "replacement_candidates": replacement_candidates,
            "rationale": "If learned signal is weak, submitting three nearby learned blends wastes slots; keep at most one as an information point.",
            "next_command": "rerun candidate generation or promote a reviewed replacement before trying to use 4-5 slots",
        },
        {
            "scenario_id": "S04_baseline_anchor_failed",
            "trigger": "Baseline anchor is blank, catastrophic, or far outside the expected reference band.",
            "release_action": "BLOCK_ALL_DEPENDENT_SLOTS",
            "keep_slots": "",
            "review_slots": "",
            "replace_slots": all_slots,
            "drop_slots": all_slots,
            "official_slot_target": "0 until baseline repaired",
            "new_candidate_needed": 4,
            "replacement_candidates": "",
            "rationale": "All planned candidates depend on the active-account anchor being trustworthy.",
            "next_command": "repair baseline reproduction and rerun audit before any official submission",
        },
        {
            "scenario_id": "S05_degnonguidi_complete_clean",
            "trigger": "Degnonguidi v6 reaches COMPLETE and its downloaded output passes deep audit with distinct signal.",
            "release_action": "INSERT_DEGNONGUIDI_AND_RERANK",
            "keep_slots": final_slots,
            "review_slots": ", ".join(x for x in [single_blend, sparse_slots] if x),
            "replace_slots": ", ".join(x for x in [sparse_slots, redundant_blends] if x),
            "drop_slots": "",
            "official_slot_target": "4-5 after rerank",
            "new_candidate_needed": 0,
            "replacement_candidates": "audited Degnonguidi output",
            "rationale": "A clean 7.159-family output should outrank a sparse plateau slot and at least one redundant blend.",
            "next_command": "python3 scripts/audit_kernel_output.py --kernel joezzzzz/rogii-degnonguidi-7159-preflight-codex --force-download",
        },
        {
            "scenario_id": "S06_degnonguidi_error_or_deferred",
            "trigger": "Degnonguidi v6 fails, stalls beyond usefulness, or is explicitly deferred.",
            "release_action": "FOLLOW_SCORE_BRANCH_WITHOUT_DEGNONGUIDI",
            "keep_slots": all_slots,
            "review_slots": calibration_slots,
            "replace_slots": "",
            "drop_slots": "",
            "official_slot_target": "depends on Fleongg branch",
            "new_candidate_needed": 0,
            "replacement_candidates": replacement_candidates,
            "rationale": "Do not let a blocked reference kernel stop unrelated audited Baidalin/SP45 decisions once score dependencies resolve.",
            "next_command": "record kernel decision, rerun poll_and_refresh_state.py, then follow S02 or S03",
        },
        {
            "scenario_id": "S07_gates_clear_but_redundancy_unresolved",
            "trigger": "Release gates clear, but the batch question is not explicitly a blend-curve calibration sweep.",
            "release_action": "KEEP_ONE_BLEND_FIND_REPLACEMENTS",
            "keep_slots": ", ".join(x for x in [final_slots, single_blend, sparse_slots] if x),
            "review_slots": single_blend,
            "replace_slots": redundant_blends,
            "drop_slots": redundant_blends,
            "official_slot_target": "4-5 only after replacements exist",
            "new_candidate_needed": 2,
            "replacement_candidates": replacement_candidates,
            "rationale": "The daily 4-5 slot target should not force multiple near-duplicate submissions unless they answer a named sweep question.",
            "next_command": "use replacement pool or build a new structural candidate before packaging redundant slots",
        },
    ]
    return pd.DataFrame(rows)


def write_report(contingency: pd.DataFrame, pool: pd.DataFrame, report: Path, contingency_csv: Path, pool_csv: Path) -> None:
    counts = contingency["release_action"].value_counts().rename_axis("release_action").reset_index(name="count") if not contingency.empty else pd.DataFrame()
    pool_cols = [
        "path",
        "family",
        "readiness_status",
        "estimated_public_band",
        "rmse_to_current_best_7p235",
        "replacement_role",
        "replacement_rank",
        "replacement_reason",
    ]
    pool_cols = [col for col in pool_cols if col in pool.columns]
    useful_pool = pool[pool.get("replacement_rank", pd.Series(dtype=int)) > 0].head(10) if not pool.empty else pool
    lines = [
        "# Planned Slot Contingency",
        "",
        "This report defines what to do with the current planned official slots after pending scores or kernel results resolve. It does not submit to Kaggle.",
        "",
        "## Action Counts",
        "",
        markdown_table(counts),
        "",
        "## Scenario Matrix",
        "",
        markdown_table(contingency),
        "",
        "## Replacement Pool",
        "",
        markdown_table(useful_pool[pool_cols] if pool_cols else useful_pool),
        "",
        "## Interpretation",
        "",
        "- Keep all slots blocked while external context is pending.",
        "- If Fleongg is competitive, the three blend slots can be kept only as an explicit calibration sweep.",
        "- If Fleongg is weak, keep at most one blend and create or promote replacements before trying to use 4-5 official slots.",
        "- If Degnonguidi completes cleanly, insert it ahead of sparse or redundant slots after audit.",
        "",
        "## Outputs",
        "",
        f"- `{contingency_csv.as_posix()}`",
        f"- `{pool_csv.as_posix()}`",
        f"- `{report.as_posix()}`",
    ]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot-review", type=Path, default=DEFAULT_SLOT_REVIEW)
    parser.add_argument("--readiness", type=Path, default=DEFAULT_READINESS)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--pool-csv", type=Path, default=DEFAULT_POOL_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    review = safe_read_csv(args.slot_review)
    readiness = safe_read_csv(args.readiness)
    pool = build_replacement_pool(readiness, review)
    contingency = build_contingency(review, pool)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    contingency.to_csv(args.output_csv, index=False)
    args.pool_csv.parent.mkdir(parents=True, exist_ok=True)
    pool.to_csv(args.pool_csv, index=False)
    write_report(contingency, pool, args.report, args.output_csv, args.pool_csv)

    print(f"wrote {args.output_csv}")
    print(f"wrote {args.pool_csv}")
    print(f"wrote {args.report}")
    print(contingency[["scenario_id", "release_action", "new_candidate_needed"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
