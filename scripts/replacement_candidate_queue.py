#!/usr/bin/env python3
"""Create an actionable replacement-candidate queue for redundant planned slots."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_CONTINGENCY = Path("experiments/planned_slot_contingency.csv")
DEFAULT_POOL = Path("experiments/planned_slot_replacement_pool.csv")
DEFAULT_AUDIT = Path("experiments/candidate_audit_summary.csv")
DEFAULT_BACKLOG = Path("experiments/question_backlog.csv")
DEFAULT_PLATEAU_SWEEP = Path("experiments/plateau_quantile_sweep.csv")
DEFAULT_OUTPUT_CSV = Path("experiments/replacement_candidate_queue.csv")
DEFAULT_REPORT = Path("reports/replacement_candidate_queue.md")

BASELINE_PATH = "artifacts/lucifer_baseline_repro_joezzzzz_v1/submission.csv"
DATA_DIR = "data/sample"


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


def shell_path(path: str) -> str:
    return path.replace("\\", "/")


def artifact_status(submission_path: str, audit_path: str) -> str:
    sub_exists = Path(submission_path).is_file()
    audit_exists = Path(audit_path).is_file()
    if sub_exists and audit_exists:
        return "ARTIFACT_AND_AUDIT_EXIST"
    if sub_exists:
        return "ARTIFACT_NEEDS_AUDIT"
    return "TODO_BUILD"


def replacement_need(contingency: pd.DataFrame) -> int:
    if contingency.empty or "new_candidate_needed" not in contingency.columns:
        return 0
    actions = {"PARTIAL_RELEASE_NEEDS_REPLACEMENTS", "KEEP_ONE_BLEND_FIND_REPLACEMENTS"}
    rows = contingency[contingency.get("release_action", pd.Series(dtype=str)).astype(str).isin(actions)]
    needs = pd.to_numeric(rows.get("new_candidate_needed", pd.Series(dtype=float)), errors="coerce")
    return int(needs.max()) if needs.notna().any() else 0


def active_question_ids(backlog: pd.DataFrame, question_type: str | None = None) -> str:
    if backlog.empty or "question_id" not in backlog.columns:
        return ""
    rows = backlog[backlog.get("status", pd.Series(dtype=str)).astype(str).isin(["active", "hold_candidate_ready", "implemented_needs_field_use"])]
    if question_type and "question_type" in rows.columns:
        rows = rows[rows["question_type"].astype(str) == question_type]
    return ", ".join(rows.get("question_id", pd.Series(dtype=str)).astype(str).head(4).tolist())


def best_plateau_nondefault(plateau: pd.DataFrame) -> dict[str, Any]:
    if plateau.empty or "is_default" not in plateau.columns:
        return {}
    work = plateau.copy()
    work["is_default_bool"] = work["is_default"].astype(str).str.lower().isin(["true", "1"])
    if "delta_weighted_rmse_vs_last_value" in work.columns:
        work["delta_weighted_rmse_vs_last_value"] = pd.to_numeric(work["delta_weighted_rmse_vs_last_value"], errors="coerce")
        work = work[(~work["is_default_bool"]) & (work["delta_weighted_rmse_vs_last_value"] < 0)]
    else:
        work = work[~work["is_default_bool"]]
    if work.empty:
        return {}
    sort_cols = [col for col in ["weighted_rmse", "combo_id"] if col in work.columns]
    row = work.sort_values(sort_cols).iloc[0] if sort_cols else work.iloc[0]
    return row.to_dict()


def duplicate_summary(pool: pd.DataFrame, audit: pd.DataFrame) -> tuple[str, str]:
    if pool.empty or audit.empty:
        return "", ""
    backup_paths = set(
        pool[pool.get("replacement_role", pd.Series(dtype=str)).astype(str) == "backup_projection_review"]
        .get("path", pd.Series(dtype=str))
        .astype(str)
    )
    rows = audit[audit.get("path", pd.Series(dtype=str)).astype(str).isin(backup_paths)].copy()
    if rows.empty or "sha256_submission_csv" not in rows.columns:
        return "; ".join(sorted(backup_paths)), ""
    grouped = rows.groupby("sha256_submission_csv")["path"].apply(lambda s: sorted(s.astype(str).tolist())).reset_index()
    largest = grouped.sort_values("path", key=lambda col: col.map(len), ascending=False).iloc[0]
    representative = largest["path"][0] if largest["path"] else ""
    duplicates = "; ".join(largest["path"])
    return representative, duplicates


def add_task(rows: list[dict[str, Any]], **kwargs: Any) -> None:
    base = {
        "task_id": "",
        "priority": 0,
        "task_type": "",
        "status": "",
        "source_question_id": "",
        "trigger_scenario": "",
        "family": "",
        "target_artifact": "",
        "build_command": "",
        "audit_command": "",
        "decision_gate": "",
        "expected_value": "",
        "risk": "",
        "notes": "",
    }
    base.update(kwargs)
    rows.append(base)


def build_queue(
    contingency: pd.DataFrame,
    pool: pd.DataFrame,
    audit: pd.DataFrame,
    backlog: pd.DataFrame,
    plateau: pd.DataFrame,
) -> pd.DataFrame:
    need = replacement_need(contingency)
    signal_questions = active_question_ids(backlog, "signal_discovery") or active_question_ids(backlog)
    ensemble_questions = active_question_ids(backlog, "ensemble_gating") or active_question_ids(backlog)
    representative, duplicate_paths = duplicate_summary(pool, audit)
    rows: list[dict[str, Any]] = []

    add_task(
        rows,
        task_id="RCQ01_replacement_need_guard",
        priority=110,
        task_type="process_gate",
        status="ACTIVE" if need else "HOLD",
        source_question_id="Q20260629-40",
        trigger_scenario="S03_baseline_valid_fleongg_weak; S07_gates_clear_but_redundancy_unresolved",
        family="planning",
        decision_gate="Need at least two non-duplicate replacement candidates before using 4-5 slots if the blend sweep is weak or unjustified.",
        expected_value="Prevents the daily submission target from forcing duplicate blend submissions.",
        risk="none",
        notes=f"replacement_need={need}",
    )

    add_task(
        rows,
        task_id="RCQ02_dedupe_backup_sp45_projection",
        priority=100,
        task_type="existing_candidate_review",
        status="REVIEW_EXISTING" if representative else "NO_CANDIDATE",
        source_question_id=signal_questions,
        trigger_scenario="S03_baseline_valid_fleongg_weak; S07_gates_clear_but_redundancy_unresolved",
        family="projection_branch",
        target_artifact=representative,
        audit_command=(
            f"python3 scripts/pre_submit_audit.py {shell_path(representative)} --data-dir {DATA_DIR} "
            "--reference-registry experiments/reference_submission_registry.csv"
        )
        if representative
        else "",
        decision_gate="Promote at most one representative if audit passes and it is not a duplicate of an already planned SP45 output.",
        expected_value="Uses existing audited projection signal without adding another nearby blend weight.",
        risk="unknown_possible_but_risky; backup projection paths appear duplicate with each other",
        notes=f"duplicate_group={duplicate_paths}",
    )

    alpha040_submission = "artifacts/gr_typewell_light_alpha040_v1/submission.csv"
    alpha040_audit = "artifacts/gr_typewell_light_alpha040_v1/local_pre_submit_audit.json"
    add_task(
        rows,
        task_id="RCQ03_build_gr_typewell_alpha040",
        priority=92,
        task_type="build_new_candidate",
        status=artifact_status(alpha040_submission, alpha040_audit),
        source_question_id=signal_questions,
        trigger_scenario="S03_baseline_valid_fleongg_weak; S07_gates_clear_but_redundancy_unresolved",
        family="gr_typewell_light",
        target_artifact=alpha040_submission,
        build_command=(
            "python3 scripts/build_gr_typewell_light_candidate.py "
            f"--baseline {BASELINE_PATH} --data-dir {DATA_DIR} "
            "--output-dir artifacts/gr_typewell_light_alpha040_v1 --alpha 0.40 --max-move 12.0"
        ),
        audit_command=(
            f"python3 scripts/pre_submit_audit.py {alpha040_submission} --data-dir {DATA_DIR} "
            "--reference-registry experiments/reference_submission_registry.csv "
            f"--json-out {alpha040_audit}"
        ),
        decision_gate="Keep only if audit passes and distance from baseline is high enough to add information without high shape risk.",
        expected_value="Tests whether a stronger GR/typewell correction can escape low-upside alpha 0.10/0.20 behavior.",
        risk="may still be low-upside or overcorrect a small visible sample",
        notes="Follow with local_surrogate_score and candidate_audit_summary before any release review.",
    )

    relaxed_submission = "artifacts/gr_typewell_light_alpha030_relaxed_v1/submission.csv"
    relaxed_audit = "artifacts/gr_typewell_light_alpha030_relaxed_v1/local_pre_submit_audit.json"
    add_task(
        rows,
        task_id="RCQ04_build_gr_typewell_relaxed_alpha030",
        priority=84,
        task_type="build_new_candidate",
        status=artifact_status(relaxed_submission, relaxed_audit),
        source_question_id=signal_questions,
        trigger_scenario="S03_baseline_valid_fleongg_weak; S07_gates_clear_but_redundancy_unresolved",
        family="gr_typewell_light",
        target_artifact=relaxed_submission,
        build_command=(
            "python3 scripts/build_gr_typewell_light_candidate.py "
            f"--baseline {BASELINE_PATH} --data-dir {DATA_DIR} "
            "--output-dir artifacts/gr_typewell_light_alpha030_relaxed_v1 --alpha 0.30 --max-move 10.0 "
            "--min-eval-improvement 0.02"
        ),
        audit_command=(
            f"python3 scripts/pre_submit_audit.py {relaxed_submission} --data-dir {DATA_DIR} "
            "--reference-registry experiments/reference_submission_registry.csv "
            f"--json-out {relaxed_audit}"
        ),
        decision_gate="Use only if it changes more than alpha 0.20 while retaining clean anchor/jump/typewell audit metrics.",
        expected_value="Tests a slightly broader GR gate without committing to a full GR path-search rewrite.",
        risk="relaxed gate can introduce visible-sample overfit",
        notes="Treat as a replacement candidate, not a calibration sweep.",
    )

    plateau_best = best_plateau_nondefault(plateau)
    if plateau_best:
        window = int(plateau_best.get("window", 256))
        quantile = float(plateau_best.get("quantile", 0.50))
        min_move = float(plateau_best.get("min_move", 4.0))
        blend = float(plateau_best.get("blend", 1.0))
        suffix = f"w{window}_q{str(quantile).replace('.', 'p')}_m{str(min_move).replace('.', 'p')}_b{str(blend).replace('.', 'p')}"
        plateau_submission = f"artifacts/plateau_recent_quantile_{suffix}_v1/submission.csv"
        plateau_audit = f"artifacts/plateau_recent_quantile_{suffix}_v1/local_pre_submit_audit.json"
        build_cmd = (
            "python3 scripts/build_plateau_recent_quantile_candidate.py "
            f"--baseline {BASELINE_PATH} --data-dir {DATA_DIR} "
            f"--output-dir artifacts/plateau_recent_quantile_{suffix}_v1 "
            f"--window {window} --quantile {quantile:g} --min-move {min_move:g} --blend {blend:g}"
        )
        notes = (
            f"source_combo={int(plateau_best.get('combo_id', -1))}; "
            f"delta_vs_last_value={fmt(float(plateau_best.get('delta_weighted_rmse_vs_last_value', np.nan)))}; "
            f"fallback_rate={fmt(float(plateau_best.get('fallback_rate', np.nan)))}"
        )
    else:
        plateau_submission = ""
        plateau_audit = ""
        build_cmd = ""
        notes = "no non-default plateau sweep winner found"

    add_task(
        rows,
        task_id="RCQ05_build_plateau_nondefault_variant",
        priority=72,
        task_type="build_new_candidate",
        status=artifact_status(plateau_submission, plateau_audit) if plateau_submission else "NO_SWEEP_VARIANT",
        source_question_id="Q20260629-B12",
        trigger_scenario="S03_baseline_valid_fleongg_weak; S07_gates_clear_but_redundancy_unresolved",
        family="plateau_signal",
        target_artifact=plateau_submission,
        build_command=build_cmd,
        audit_command=(
            f"python3 scripts/pre_submit_audit.py {plateau_submission} --data-dir {DATA_DIR} "
            "--reference-registry experiments/reference_submission_registry.csv "
            f"--json-out {plateau_audit}"
        )
        if plateau_submission
        else "",
        decision_gate="Use only as sparse information unless a broader validation source appears.",
        expected_value="Adds a second plateau diagnostic from the best non-default stability-sweep combo.",
        risk="high fallback/sparse well coverage; not a broad model promotion",
        notes=notes,
    )

    add_task(
        rows,
        task_id="RCQ06_design_sp45_plateau_gate",
        priority=64,
        task_type="design_new_candidate",
        status="DESIGN_REQUIRED",
        source_question_id=ensemble_questions,
        trigger_scenario="S03_baseline_valid_fleongg_weak; S07_gates_clear_but_redundancy_unresolved",
        family="ensemble_gating",
        decision_gate="Implement only if per-well impact shows the plateau change is localized and SP45 projection remains broad.",
        expected_value="Could replace redundant blend slots with a per-well route rather than another global weight.",
        risk="needs a new builder and may overfit the three visible wells",
        notes="Candidate idea: baseline/SP45 for broad wells, plateau only where recent-prefix rule fires.",
    )

    add_task(
        rows,
        task_id="RCQ07_audit_degnonguidi_if_complete",
        priority=60,
        task_type="kernel_output_audit",
        status="WAIT_KERNEL",
        source_question_id="Q20260629-B07",
        trigger_scenario="S05_degnonguidi_complete_clean",
        family="reference_reproduction",
        audit_command=(
            "python3 scripts/audit_kernel_output.py "
            "--kernel joezzzzz/rogii-degnonguidi-7159-preflight-codex "
            "--output-dir artifacts/kernel_outputs/rogii-degnonguidi-7159-preflight-codex_v6 "
            "--kaggle-bin /home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle "
            "--force-download"
        ),
        decision_gate="If COMPLETE and audit passes, insert ahead of sparse or redundant planned slots.",
        expected_value="Could add the strongest independent 7.159-family reference if the patched kernel succeeds.",
        risk="kernel still running and may fail another object-contract issue",
        notes="Do not spend an official submission before output audit and distance review.",
    )

    queue = pd.DataFrame(rows).sort_values(["priority", "task_id"], ascending=[False, True])
    queue["replacement_need"] = need
    queue["ready_now"] = queue["status"].astype(str).isin(["TODO_BUILD", "ARTIFACT_NEEDS_AUDIT", "REVIEW_EXISTING", "DESIGN_REQUIRED"])
    return queue


def write_report(queue: pd.DataFrame, output: Path, csv_path: Path) -> None:
    counts = queue["status"].value_counts().rename_axis("status").reset_index(name="count") if not queue.empty else pd.DataFrame()
    type_counts = queue["task_type"].value_counts().rename_axis("task_type").reset_index(name="count") if not queue.empty else pd.DataFrame()
    cols = [
        "task_id",
        "priority",
        "task_type",
        "status",
        "source_question_id",
        "trigger_scenario",
        "family",
        "target_artifact",
        "decision_gate",
        "expected_value",
        "risk",
    ]
    cols = [col for col in cols if col in queue.columns]
    command_cols = ["task_id", "build_command", "audit_command"]
    command_cols = [col for col in command_cols if col in queue.columns]
    lines = [
        "# Replacement Candidate Queue",
        "",
        "This report turns planned-slot contingency needs into concrete candidate build, audit, and design tasks. It does not submit to Kaggle.",
        "",
        "## Status Counts",
        "",
        markdown_table(counts),
        "",
        "## Task Type Counts",
        "",
        markdown_table(type_counts),
        "",
        "## Queue",
        "",
        markdown_table(queue[cols] if cols else queue),
        "",
        "## Commands",
        "",
        markdown_table(queue[command_cols] if command_cols else queue),
        "",
        "## Interpretation",
        "",
        "- Build or audit replacement candidates only while official slots remain blocked by external context.",
        "- A replacement candidate is not submission-ready until it appears in candidate audit/readiness reports and passes release gates.",
        "- Existing backup SP45 projections should be deduped before promotion; do not spend multiple slots on the same hash.",
        "- GR/typewell and plateau tasks are replacement sources, not permission to submit before pending public scores resolve.",
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
    parser.add_argument("--contingency", type=Path, default=DEFAULT_CONTINGENCY)
    parser.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--backlog", type=Path, default=DEFAULT_BACKLOG)
    parser.add_argument("--plateau-sweep", type=Path, default=DEFAULT_PLATEAU_SWEEP)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    queue = build_queue(
        contingency=safe_read_csv(args.contingency),
        pool=safe_read_csv(args.pool),
        audit=safe_read_csv(args.audit),
        backlog=safe_read_csv(args.backlog),
        plateau=safe_read_csv(args.plateau_sweep),
    )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    queue.to_csv(args.output_csv, index=False)
    write_report(queue, args.report, args.output_csv)

    print(f"wrote {args.output_csv}")
    print(f"wrote {args.report}")
    print(queue[["task_id", "priority", "status", "ready_now"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
