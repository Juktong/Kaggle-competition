#!/usr/bin/env python3
"""Build a conditional 4-5 slot plan from audited ROGII candidates."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_CANDIDATES = Path("experiments/candidate_audit_summary.csv")
DEFAULT_SUBMISSIONS = Path("experiments/submission_ledger.csv")
DEFAULT_KERNELS = Path("experiments/kernel_run_ledger.csv")
DEFAULT_OUTPUT_CSV = Path("experiments/next_submission_batch_plan.csv")
DEFAULT_REPORT = Path("reports/next_submission_batch_plan.md")

BASELINE_CANDIDATE = "lucifer_baseline_repro_joezzzzz"
FLEONGG_CANDIDATE = "fleongg_pretrained_branch_calibration"
SP45_CANDIDATE = "sp45_projection_slot1_dynamic_rerun"
FLEONGG_COMPETITIVE_MARGIN = 0.10
SP45_COMPETITIVE_MARGIN = 0.20


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


def pending_official_rows(submissions: pd.DataFrame) -> pd.DataFrame:
    if submissions.empty or "status" not in submissions.columns:
        return pd.DataFrame()
    return submissions[submissions["status"].astype(str).str.lower().isin(["pending", "submitted", "running"])].copy()


def running_kernel_rows(kernels: pd.DataFrame) -> pd.DataFrame:
    if kernels.empty or "status" not in kernels.columns:
        return pd.DataFrame()
    return kernels[kernels["status"].astype(str).str.upper().isin(["RUNNING", "PENDING", "QUEUED"])].copy()


def latest_score(submissions: pd.DataFrame, candidate_id_value: str) -> float:
    if submissions.empty or "candidate_id" not in submissions.columns:
        return np.nan
    rows = submissions[submissions["candidate_id"].astype(str) == candidate_id_value]
    if rows.empty:
        return np.nan
    return pd.to_numeric(rows.iloc[-1].get("public_score", np.nan), errors="coerce")


def calibration_flags(submissions: pd.DataFrame) -> dict[str, Any]:
    baseline = latest_score(submissions, BASELINE_CANDIDATE)
    fleongg = latest_score(submissions, FLEONGG_CANDIDATE)
    sp45 = latest_score(submissions, SP45_CANDIDATE)
    baseline_valid = np.isfinite(baseline) and baseline <= 8.5
    return {
        "baseline_score": baseline,
        "fleongg_score": fleongg,
        "sp45_score": sp45,
        "fleongg_weak": bool(baseline_valid and np.isfinite(fleongg) and fleongg > baseline + FLEONGG_COMPETITIVE_MARGIN),
        "sp45_weak": bool(baseline_valid and np.isfinite(sp45) and sp45 > baseline + SP45_COMPETITIVE_MARGIN),
    }


def candidate_id(path: str) -> str:
    parts = [part for part in Path(path).parts if part not in {"artifacts", "kernel_outputs"}]
    text = "__".join(parts).replace(".csv", "")
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()


def blend_weight(path: str) -> float:
    match = re.search(r"w0\.(\d+)", path)
    if not match:
        return np.nan
    return float(f"0.{match.group(1)}")


def slot_role(row: pd.Series) -> str:
    family = str(row.get("family", ""))
    path = str(row.get("path", ""))
    if family == "projection_branch":
        if "kernel_outputs/rogii-baidalin" in path:
            return "structural_candidate"
        return "backup_structural_comparison"
    if family == "projection_learned_blend":
        return "calibration_sweep"
    if family == "plateau_signal":
        return "flexible_information_slot"
    if family == "learned_signal":
        return "pending_equivalent_calibration"
    if family == "gr_typewell_light":
        return "low_upside_backup"
    return "review"


def information_question(row: pd.Series) -> str:
    family = str(row.get("family", ""))
    path = str(row.get("path", ""))
    if family == "projection_branch":
        return "Does the SP45 projection branch add signal beyond the active baseline?"
    if family == "projection_learned_blend":
        weight = blend_weight(path)
        weight_text = fmt(weight) if np.isfinite(weight) else "selected"
        return f"Where is the SP45+Fleongg low-dimensional blend curve around weight {weight_text}?"
    if family == "plateau_signal":
        return "Does the sparse plateau rule provide useful independent information?"
    if family == "learned_signal":
        return "Already represented by pending Fleongg official calibration; do not duplicate."
    if family == "gr_typewell_light":
        return "Low-upside GR/typewell correction; use only as conservative backup."
    return "Manual review required before assigning a submission question."


def release_condition(row: pd.Series, batch_status: str) -> str:
    family = str(row.get("family", ""))
    if batch_status == "NEEDS_NEW_ARCHITECTURE_CANDIDATES":
        return "Do not release this batch; official SP45/Fleongg calibration was weak, so build a new structural architecture first."
    if batch_status == "READY_FOR_RELEASE_REVIEW":
        return "External blockers are clear; run final manual review immediately before any official submission."
    if family == "projection_learned_blend":
        return "Release only after 54174151 and 54174876 score; prioritize if Fleongg is competitive or useful for ensemble diversity."
    if family == "projection_branch":
        return "Release after 54174151 scores and Degnonguidi v6 either completes/audits or is explicitly deferred."
    if family == "plateau_signal":
        return "Release as the flexible 5th slot only after anchors resolve and no stronger audited candidate is available."
    if family == "learned_signal":
        return "Do not release while equivalent Fleongg official submission 54174876 is pending."
    return "Hold until blockers clear and the candidate remains non-duplicate in the latest audit summary."


def score_candidate(row: pd.Series, flags: dict[str, Any]) -> float:
    score = 0.0
    gate = str(row.get("submission_gate", ""))
    family = str(row.get("family", ""))
    audit_gate = str(row.get("audit_gate", ""))
    band = str(row.get("estimated_public_band", ""))
    novelty = str(row.get("novelty_bucket", ""))
    readiness = str(row.get("readiness_status", ""))
    path = str(row.get("path", ""))

    score += {
        "AUDITED_WAIT_CONTEXT": 60,
        "HOLD_INFORMATION_SLOT": 35,
        "HOLD_LOW_UPSIDE": 5,
        "HOLD_DUPLICATE": -80,
    }.get(gate, -40)
    score += {
        "projection_branch": 28,
        "projection_learned_blend": 24,
        "plateau_signal": 12,
        "learned_signal": -25,
        "gr_typewell_light": -15,
        "anchor_or_duplicate": -100,
    }.get(family, 0)
    score += {"AUDIT_PASS": 8, "AUDIT_PASS_WARN_REVIEW": 4}.get(audit_gate, -60)
    score += {
        "plausible_7p2_to_7p8_band": 10,
        "unknown_possible_but_risky": -4,
        "likely_around_7p235_low_upside": -15,
    }.get(band, 0)
    score += {"moderate": 8, "high": 7, "very_high": 4, "low": -10, "duplicate": -80}.get(novelty, 0)
    score += {"HOLD_PENDING_CONTEXT": 5, "HOLD_INFORMATION_SLOT": 2, "WAIT_OFFICIAL_SCORE": -12}.get(readiness, 0)

    dist = row.get("rmse_to_current_best_7p235", np.nan)
    if np.isfinite(dist):
        if 1.0 <= dist <= 4.0:
            score += 8
        elif 4.0 < dist <= 6.5:
            score += 2
        elif dist < 1.0:
            score -= 20

    anchor_p90 = row.get("anchor_first_abs_p90", np.nan)
    if np.isfinite(anchor_p90) and anchor_p90 > 5.0:
        score -= 3

    cv_delta = row.get("cv_mean_delta", np.nan)
    if np.isfinite(cv_delta) and cv_delta < 0:
        score += 7

    if "kernel_outputs/rogii-baidalin" in path:
        score += 4
    if flags.get("sp45_weak") and family in {"projection_branch", "projection_learned_blend"}:
        score -= 45
    if flags.get("fleongg_weak") and family in {"projection_learned_blend", "learned_signal"}:
        score -= 35
    return score


def drop_sha_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "sha256_submission_csv" not in df.columns:
        return df
    work = df.copy()
    work["_has_sha"] = work["sha256_submission_csv"].notna()
    with_sha = work[work["_has_sha"]].sort_values(["priority_score", "path"], ascending=[False, True])
    without_sha = work[~work["_has_sha"]]
    deduped = with_sha.drop_duplicates("sha256_submission_csv", keep="first")
    return pd.concat([deduped, without_sha], ignore_index=True).drop(columns=["_has_sha"])


def choose_blend_sweep(blends: pd.DataFrame, max_count: int = 3) -> pd.DataFrame:
    if blends.empty:
        return blends
    work = blends.copy()
    work["blend_weight"] = work["path"].map(blend_weight)
    work = work.sort_values("blend_weight", na_position="last")
    if len(work) <= max_count:
        return work.sort_values("priority_score", ascending=False)
    targets = [work.iloc[0]]
    middle_idx = len(work) // 2
    targets.append(work.iloc[middle_idx])
    targets.append(work.iloc[-1])
    out = pd.DataFrame(targets).drop_duplicates("path")
    return out.sort_values("priority_score", ascending=False)


def build_plan(candidates: pd.DataFrame, submissions: pd.DataFrame, kernels: pd.DataFrame, max_slots: int) -> tuple[pd.DataFrame, dict[str, Any]]:
    pending = pending_official_rows(submissions)
    running = running_kernel_rows(kernels)
    flags = calibration_flags(submissions)
    if len(pending) or len(running):
        batch_status = "WAIT_EXTERNAL_CONTEXT"
    elif flags["sp45_weak"] and flags["fleongg_weak"]:
        batch_status = "NEEDS_NEW_ARCHITECTURE_CANDIDATES"
    else:
        batch_status = "READY_FOR_RELEASE_REVIEW"

    work = candidates.copy()
    work["candidate_id"] = work["path"].map(candidate_id)
    work["slot_role"] = work.apply(slot_role, axis=1)
    work["information_question"] = work.apply(information_question, axis=1)
    work["priority_score"] = work.apply(lambda row: score_candidate(row, flags), axis=1)
    work = drop_sha_duplicates(work)

    eligible = work[
        work["submission_gate"].isin(["READY", "READY_REVIEW_WARNINGS", "AUDITED_WAIT_CONTEXT", "HOLD_INFORMATION_SLOT"])
        & work["audit_gate"].isin(["AUDIT_PASS", "AUDIT_PASS_WARN_REVIEW"])
    ].copy()

    selected_parts = []
    if not flags["sp45_weak"]:
        baidalin_projection = eligible[
            (eligible["family"] == "projection_branch")
            & eligible["path"].astype(str).str.contains("kernel_outputs/rogii-baidalin", regex=False, na=False)
        ].sort_values("priority_score", ascending=False)
        if not baidalin_projection.empty:
            selected_parts.append(baidalin_projection.head(1))

    if not flags["fleongg_weak"] and not flags["sp45_weak"]:
        blends = choose_blend_sweep(eligible[eligible["family"] == "projection_learned_blend"], max_count=3)
        if not blends.empty:
            selected_parts.append(blends.head(3))

    replacement_families = ["gr_typewell_light", "plateau_signal"] if flags["sp45_weak"] else ["plateau_signal"]
    replacements = eligible[eligible["family"].isin(replacement_families)].sort_values("priority_score", ascending=False)
    if not replacements.empty:
        selected_parts.append(replacements.head(max_slots))

    selected = pd.concat(selected_parts, ignore_index=True) if selected_parts else pd.DataFrame(columns=eligible.columns)
    selected = selected.drop_duplicates("path").head(max_slots).copy()

    if len(selected) < max_slots:
        used = set(selected.get("path", pd.Series(dtype=str)))
        backups = eligible[~eligible["path"].isin(used)].sort_values("priority_score", ascending=False)
        selected = pd.concat([selected, backups.head(max_slots - len(selected))], ignore_index=True)

    selected = selected.head(max_slots).copy()
    selected["planned_slot"] = range(1, len(selected) + 1)
    selected["batch_status"] = batch_status
    selected["current_action"] = np.where(
        batch_status == "WAIT_EXTERNAL_CONTEXT",
        "do_not_submit_yet",
        np.where(batch_status == "NEEDS_NEW_ARCHITECTURE_CANDIDATES", "build_new_architecture_first", "final_review_before_submit"),
    )
    selected["release_condition"] = selected.apply(lambda row: release_condition(row, batch_status), axis=1)

    cols = [
        "planned_slot",
        "candidate_id",
        "path",
        "slot_role",
        "family",
        "batch_status",
        "current_action",
        "release_condition",
        "submission_gate",
        "audit_gate",
        "readiness_status",
        "priority_score",
        "estimated_public_band",
        "novelty_bucket",
        "rmse_to_current_best_7p235",
        "audit_rmse_to_fleongg_pending",
        "anchor_first_abs_p90",
        "jump_rate_abs_slope_gt3",
        "cv_mean_delta",
        "information_question",
    ]
    cols = [c for c in cols if c in selected.columns]
    meta = {
        "batch_status": batch_status,
        "pending_count": len(pending),
        "running_count": len(running),
        "pending_ids": ", ".join(pending.get("submission_id", pd.Series(dtype=str)).astype(str).tolist()),
        "running_kernels": ", ".join(running.get("kernel_slug", pd.Series(dtype=str)).astype(str).tolist()),
        "eligible_count": len(eligible),
        "selected_count": len(selected),
        "baseline_score": fmt(flags["baseline_score"]),
        "fleongg_score": fmt(flags["fleongg_score"]),
        "sp45_score": fmt(flags["sp45_score"]),
        "fleongg_weak": flags["fleongg_weak"],
        "sp45_weak": flags["sp45_weak"],
    }
    return selected[cols], meta


def write_report(plan: pd.DataFrame, meta: dict[str, Any], output: Path, csv_path: Path) -> None:
    cols = [
        "planned_slot",
        "slot_role",
        "family",
        "batch_status",
        "current_action",
        "priority_score",
        "estimated_public_band",
        "novelty_bucket",
        "rmse_to_current_best_7p235",
        "path",
    ]
    cols = [c for c in cols if c in plan.columns]
    branch_rules = pd.DataFrame(
        [
            {
                "result": "54174151 baseline scores near expected reference",
                "next_action": "Use it as the active-account anchor and allow SP45 projection review.",
            },
            {
                "result": "54174151 blank or catastrophic",
                "next_action": "Block dependent submissions; repair active-account baseline before spending more slots.",
            },
            {
                "result": "54174876 Fleongg improves or ties baseline",
                "next_action": "Prioritize SP45+Fleongg blend sweep slots after final review.",
            },
            {
                "result": "54174876 Fleongg worsens materially",
                "next_action": "Prefer pure SP45 projection or plateau information slot; downweight Fleongg blends.",
            },
            {
                "result": "Degnonguidi v6 completes and audits cleanly",
                "next_action": "Insert its best distinct output ahead of lower-priority blend or plateau slots.",
            },
        ]
    )

    lines = [
        "# Next Submission Batch Plan",
        "",
        "This is a conditional 4-5 slot plan built from audited candidates. It does not submit anything.",
        "",
        "## Current Status",
        "",
        f"- Batch status: `{meta['batch_status']}`",
        f"- Pending official submissions: `{meta['pending_count']}`",
        f"- Running kernels: `{meta['running_count']}`",
        f"- Eligible audited candidates: `{meta['eligible_count']}`",
        f"- Planned slots: `{meta['selected_count']}`",
        f"- Pending IDs: `{meta['pending_ids']}`",
        f"- Running kernels: `{meta['running_kernels']}`",
        f"- Baseline/Fleongg/SP45 official scores: `{meta['baseline_score']}` / `{meta['fleongg_score']}` / `{meta['sp45_score']}`",
        f"- Weak-branch flags: Fleongg `{meta['fleongg_weak']}`, SP45 `{meta['sp45_weak']}`",
        "",
        "## Planned Slots",
        "",
        markdown_table(plan[cols] if cols else plan),
        "",
        "## Release Rules",
        "",
        markdown_table(branch_rules),
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
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--submissions", type=Path, default=DEFAULT_SUBMISSIONS)
    parser.add_argument("--kernels", type=Path, default=DEFAULT_KERNELS)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-slots", type=int, default=5)
    args = parser.parse_args()

    candidates = safe_read_csv(args.candidates)
    submissions = safe_read_csv(args.submissions)
    kernels = safe_read_csv(args.kernels)
    plan, meta = build_plan(candidates, submissions, kernels, args.max_slots)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    plan.to_csv(args.output_csv, index=False)
    write_report(plan, meta, args.report, args.output_csv)

    print(f"wrote {args.output_csv}")
    print(f"wrote {args.report}")
    print(plan[["planned_slot", "candidate_id", "batch_status", "current_action"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
