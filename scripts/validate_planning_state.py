#!/usr/bin/env python3
"""Validate consistency between ROGII planning reports before submission."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_POLL = Path("experiments/poll_refresh_summary.csv")
DEFAULT_READINESS = Path("experiments/next_batch_readiness.csv")
DEFAULT_AUDIT = Path("experiments/candidate_audit_summary.csv")
DEFAULT_PLAN = Path("experiments/next_submission_batch_plan.csv")
DEFAULT_WELL_IMPACT = Path("experiments/planned_candidate_well_impact_summary.csv")
DEFAULT_DIVERSITY = Path("experiments/planned_candidate_diversity_summary.csv")
DEFAULT_SLOT_REVIEW = Path("experiments/planned_slot_review.csv")
DEFAULT_SLOT_CONTINGENCY = Path("experiments/planned_slot_contingency.csv")
DEFAULT_REPLACEMENT_POOL = Path("experiments/planned_slot_replacement_pool.csv")
DEFAULT_REPLACEMENT_QUEUE = Path("experiments/replacement_candidate_queue.csv")
DEFAULT_RELEASE = Path("experiments/submission_release_gate.csv")
DEFAULT_MANIFEST = Path("experiments/candidate_artifact_manifest_summary.csv")
DEFAULT_FINAL_PACKAGE = Path("experiments/final_submission_package_summary.csv")
DEFAULT_RESULT_APPLICATION = Path("experiments/result_application_plan.csv")
DEFAULT_OUTPUT_CSV = Path("experiments/planning_state_validation.csv")
DEFAULT_REPORT = Path("reports/planning_state_validation_report.md")


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


def poll_value(poll: pd.DataFrame, key: str, default: str = "") -> str:
    if poll.empty or not {"metric", "value"}.issubset(poll.columns):
        return default
    rows = poll[poll["metric"].astype(str) == key]
    if rows.empty:
        return default
    return str(rows.iloc[0]["value"])


def int_poll_value(poll: pd.DataFrame, key: str) -> int:
    try:
        return int(float(poll_value(poll, key, "0")))
    except ValueError:
        return 0


def add(checks: list[dict[str, Any]], name: str, severity: str, status: str, detail: str) -> None:
    checks.append({"check": name, "severity": severity, "status": status, "detail": detail})


def status_from_condition(condition: bool) -> str:
    return "PASS" if condition else "FAIL"


def validate(
    poll: pd.DataFrame,
    readiness: pd.DataFrame,
    audit: pd.DataFrame,
    plan: pd.DataFrame,
    well_impact: pd.DataFrame,
    diversity: pd.DataFrame,
    slot_review: pd.DataFrame,
    slot_contingency: pd.DataFrame,
    replacement_pool: pd.DataFrame,
    replacement_queue: pd.DataFrame,
    release: pd.DataFrame,
    manifest: pd.DataFrame,
    final_package: pd.DataFrame,
    result_application: pd.DataFrame,
) -> pd.DataFrame:
    checks: list[dict[str, Any]] = []

    pending = int_poll_value(poll, "pending_official_submissions")
    running = int_poll_value(poll, "running_kernels")
    kernel_updates = int_poll_value(poll, "kernel_updates_detected")
    submission_updates = int_poll_value(poll, "submission_updates_detected")
    batch_status = poll_value(poll, "batch_status", "")

    add(checks, "input_poll_summary_exists", "ERROR", status_from_condition(not poll.empty), "poll refresh summary is readable")
    add(checks, "input_readiness_exists", "ERROR", status_from_condition(not readiness.empty), "next-batch readiness CSV is readable")
    add(checks, "input_audit_summary_exists", "ERROR", status_from_condition(not audit.empty), "candidate audit summary CSV is readable")
    add(checks, "input_plan_exists", "ERROR", status_from_condition(not plan.empty), "next submission batch plan CSV is readable")
    add(
        checks,
        "input_well_impact_summary_exists",
        "ERROR",
        status_from_condition(not well_impact.empty),
        "planned candidate well-impact summary CSV is readable",
    )
    add(
        checks,
        "input_candidate_diversity_summary_exists",
        "ERROR",
        status_from_condition(not diversity.empty),
        "planned candidate diversity summary CSV is readable",
    )
    add(
        checks,
        "input_planned_slot_review_exists",
        "ERROR",
        status_from_condition(not slot_review.empty),
        "planned slot review CSV is readable",
    )
    add(
        checks,
        "input_planned_slot_contingency_exists",
        "ERROR",
        status_from_condition(not slot_contingency.empty),
        "planned slot contingency CSV is readable",
    )
    add(
        checks,
        "input_planned_slot_replacement_pool_exists",
        "ERROR",
        status_from_condition(not replacement_pool.empty),
        "planned slot replacement pool CSV is readable",
    )
    add(
        checks,
        "input_replacement_candidate_queue_exists",
        "ERROR",
        status_from_condition(not replacement_queue.empty),
        "replacement candidate queue CSV is readable",
    )
    add(checks, "input_release_gate_exists", "ERROR", status_from_condition(not release.empty), "submission release gate CSV is readable")
    add(
        checks,
        "input_artifact_manifest_summary_exists",
        "ERROR",
        status_from_condition(not manifest.empty),
        "candidate artifact manifest summary CSV is readable",
    )
    add(
        checks,
        "input_final_submission_package_summary_exists",
        "ERROR",
        status_from_condition(not final_package.empty),
        "final submission package summary CSV is readable",
    )
    add(
        checks,
        "input_result_application_plan_exists",
        "ERROR",
        status_from_condition(not result_application.empty),
        "result application plan CSV is readable",
    )

    plan_paths = set(plan.get("path", pd.Series(dtype=str)).astype(str))
    release_paths = set(release.get("path", pd.Series(dtype=str)).astype(str))
    audit_paths = set(audit.get("path", pd.Series(dtype=str)).astype(str))
    readiness_paths = set(readiness.get("path", pd.Series(dtype=str)).astype(str))
    well_impact_paths = set(well_impact.get("path", pd.Series(dtype=str)).astype(str))
    diversity_paths = set(diversity.get("path", pd.Series(dtype=str)).astype(str))
    slot_review_paths = set(slot_review.get("path", pd.Series(dtype=str)).astype(str))
    manifest_paths = set(manifest.get("path", pd.Series(dtype=str)).astype(str))
    package_paths = set(final_package.get("path", pd.Series(dtype=str)).astype(str))

    add(
        checks,
        "planned_slots_within_daily_limit",
        "ERROR",
        status_from_condition(len(plan) <= 5),
        f"planned slots={len(plan)}; daily official limit=5",
    )
    add(
        checks,
        "planned_slots_have_release_rows",
        "ERROR",
        status_from_condition(plan_paths == release_paths),
        f"plan-only={sorted(plan_paths - release_paths)[:5]}; release-only={sorted(release_paths - plan_paths)[:5]}",
    )
    add(
        checks,
        "planned_slots_have_audit_rows",
        "ERROR",
        status_from_condition(plan_paths.issubset(audit_paths)),
        f"missing audit rows={sorted(plan_paths - audit_paths)[:5]}",
    )
    add(
        checks,
        "planned_slots_have_readiness_rows",
        "ERROR",
        status_from_condition(plan_paths.issubset(readiness_paths)),
        f"missing readiness rows={sorted(plan_paths - readiness_paths)[:5]}",
    )
    add(
        checks,
        "planned_slots_have_well_impact_rows",
        "ERROR",
        status_from_condition(plan_paths.issubset(well_impact_paths)),
        f"missing well-impact rows={sorted(plan_paths - well_impact_paths)[:5]}",
    )
    add(
        checks,
        "planned_slots_have_diversity_rows",
        "ERROR",
        status_from_condition(plan_paths.issubset(diversity_paths)),
        f"missing diversity rows={sorted(plan_paths - diversity_paths)[:5]}",
    )
    add(
        checks,
        "planned_slots_have_slot_review_rows",
        "ERROR",
        status_from_condition(plan_paths.issubset(slot_review_paths)),
        f"missing slot-review rows={sorted(plan_paths - slot_review_paths)[:5]}",
    )
    add(
        checks,
        "planned_slots_have_artifact_manifest_rows",
        "ERROR",
        status_from_condition(plan_paths.issubset(manifest_paths)),
        f"missing manifest rows={sorted(plan_paths - manifest_paths)[:5]}",
    )
    add(
        checks,
        "planned_slots_have_final_package_rows",
        "ERROR",
        status_from_condition(plan_paths.issubset(package_paths)),
        f"missing package rows={sorted(plan_paths - package_paths)[:5]}",
    )
    add(
        checks,
        "planned_paths_unique",
        "ERROR",
        status_from_condition(len(plan_paths) == len(plan)),
        "no duplicate planned submission paths",
    )

    if "sha256_submission_csv" in audit.columns and not plan.empty:
        planned_audit = audit[audit["path"].astype(str).isin(plan_paths)].copy()
        dup_sha = planned_audit["sha256_submission_csv"].dropna().duplicated().sum()
        add(
            checks,
            "planned_submission_hashes_unique",
            "ERROR",
            status_from_condition(int(dup_sha) == 0),
            f"duplicate planned sha count={int(dup_sha)}",
        )

    missing_audit = int((audit.get("audit_gate", pd.Series(dtype=str)).astype(str) == "MISSING_AUDIT").sum()) if not audit.empty else 0
    add(
        checks,
        "no_missing_audit_in_candidate_pool",
        "ERROR",
        status_from_condition(missing_audit == 0),
        f"MISSING_AUDIT rows={missing_audit}",
    )

    release_gates = set(release.get("release_gate", pd.Series(dtype=str)).astype(str))
    blocked_or_review = any(gate.startswith("BLOCKED") or gate == "REVIEW_LEDGER_UPDATES" for gate in release_gates)
    if pending or running or batch_status == "WAIT_EXTERNAL_CONTEXT":
        add(
            checks,
            "external_context_blocks_release",
            "ERROR",
            status_from_condition(blocked_or_review),
            f"pending={pending}; running={running}; batch_status={batch_status}; gates={sorted(release_gates)}",
        )
        actions = set(plan.get("current_action", pd.Series(dtype=str)).astype(str))
        add(
            checks,
            "blocked_plan_does_not_submit",
            "ERROR",
            status_from_condition(actions <= {"do_not_submit_yet"}),
            f"current actions={sorted(actions)}",
        )

    if kernel_updates or submission_updates:
        add(
            checks,
            "detected_updates_block_release_until_applied",
            "ERROR",
            status_from_condition("REVIEW_LEDGER_UPDATES" in release_gates),
            f"kernel_updates={kernel_updates}; submission_updates={submission_updates}; gates={sorted(release_gates)}",
        )
    else:
        add(
            checks,
            "no_unapplied_poll_updates",
            "INFO",
            "PASS",
            "poll refresh detected no unapplied kernel/submission updates",
        )

    if "audit_gate" in plan.columns:
        bad_audit = plan[~plan["audit_gate"].astype(str).isin(["AUDIT_PASS", "AUDIT_PASS_WARN_REVIEW"])]
        add(
            checks,
            "planned_slots_have_passing_audit_gate",
            "ERROR",
            status_from_condition(bad_audit.empty),
            f"nonpassing planned audit rows={len(bad_audit)}",
        )

    if "impact_bucket" in well_impact.columns:
        planned_impact = well_impact[well_impact["path"].astype(str).isin(plan_paths)].copy()
        add(
            checks,
            "planned_slots_have_impact_buckets",
            "ERROR",
            status_from_condition(len(planned_impact) == len(plan_paths) and planned_impact["impact_bucket"].astype(str).ne("").all()),
            f"well-impact rows={len(planned_impact)}; buckets={sorted(set(planned_impact.get('impact_bucket', pd.Series(dtype=str)).astype(str)))}",
        )

    if "diversity_flag" in diversity.columns:
        planned_diversity = diversity[diversity["path"].astype(str).isin(plan_paths)].copy()
        add(
            checks,
            "planned_slots_have_diversity_flags",
            "ERROR",
            status_from_condition(len(planned_diversity) == len(plan_paths) and planned_diversity["diversity_flag"].astype(str).ne("").all()),
            f"diversity rows={len(planned_diversity)}; flags={sorted(set(planned_diversity.get('diversity_flag', pd.Series(dtype=str)).astype(str)))}",
        )

    if {"slot_review", "evidence_review"}.issubset(slot_review.columns):
        planned_reviews = slot_review[slot_review["path"].astype(str).isin(plan_paths)].copy()
        add(
            checks,
            "planned_slots_have_slot_reviews",
            "ERROR",
            status_from_condition(
                len(planned_reviews) == len(plan_paths)
                and planned_reviews["slot_review"].astype(str).ne("").all()
                and planned_reviews["evidence_review"].astype(str).ne("").all()
            ),
            f"slot-review rows={len(planned_reviews)}; reviews={sorted(set(planned_reviews.get('slot_review', pd.Series(dtype=str)).astype(str)))}",
        )

    if {"scenario_id", "release_action", "new_candidate_needed"}.issubset(slot_contingency.columns):
        required_scenarios = {
            "S01_no_external_change",
            "S02_baseline_valid_fleongg_competitive",
            "S03_baseline_valid_fleongg_weak",
            "S04_baseline_anchor_failed",
            "S05_degnonguidi_complete_clean",
            "S06_degnonguidi_error_or_deferred",
            "S07_gates_clear_but_redundancy_unresolved",
        }
        scenarios = set(slot_contingency["scenario_id"].astype(str))
        add(
            checks,
            "required_slot_contingency_scenarios_exist",
            "ERROR",
            status_from_condition(required_scenarios.issubset(scenarios)),
            f"missing scenarios={sorted(required_scenarios - scenarios)}",
        )
        needs = pd.to_numeric(slot_contingency["new_candidate_needed"], errors="coerce")
        add(
            checks,
            "slot_contingency_new_candidate_needs_are_numeric",
            "ERROR",
            status_from_condition(needs.notna().all() and (needs >= 0).all()),
            f"new_candidate_needed values={slot_contingency['new_candidate_needed'].astype(str).tolist()}",
        )
        if pending or running or batch_status == "WAIT_EXTERNAL_CONTEXT":
            actions = set(slot_contingency["release_action"].astype(str))
            add(
                checks,
                "pending_context_has_wait_no_submit_contingency",
                "ERROR",
                status_from_condition("WAIT_NO_SUBMIT" in actions),
                f"contingency actions={sorted(actions)}",
            )

    if "replacement_role" in replacement_pool.columns:
        roles = set(replacement_pool["replacement_role"].astype(str))
        add(
            checks,
            "replacement_pool_roles_available",
            "INFO",
            status_from_condition(bool(roles)),
            f"replacement roles={sorted(roles)}",
        )

    if {"task_id", "task_type", "status", "replacement_need"}.issubset(replacement_queue.columns):
        tasks = set(replacement_queue["task_id"].astype(str))
        add(
            checks,
            "replacement_queue_has_core_tasks",
            "ERROR",
            status_from_condition({"RCQ01_replacement_need_guard", "RCQ03_build_gr_typewell_alpha040"}.issubset(tasks)),
            f"replacement queue tasks={sorted(tasks)}",
        )
        need_values = pd.to_numeric(replacement_queue["replacement_need"], errors="coerce")
        need = int(need_values.max()) if need_values.notna().any() else 0
        if need > 0:
            build_or_review = replacement_queue[
                replacement_queue["task_type"].astype(str).isin(["build_new_candidate", "existing_candidate_review", "design_new_candidate"])
            ]
            add(
                checks,
                "replacement_need_has_actionable_queue",
                "ERROR",
                status_from_condition(len(build_or_review) >= need),
                f"replacement_need={need}; actionable_tasks={len(build_or_review)}",
            )
        built_or_ready = replacement_queue[
            replacement_queue["status"].astype(str).isin(["ARTIFACT_AND_AUDIT_EXIST", "ARTIFACT_NEEDS_AUDIT", "TODO_BUILD", "REVIEW_EXISTING"])
        ]
        add(
            checks,
            "replacement_queue_has_build_or_review_paths",
            "INFO",
            status_from_condition(not built_or_ready.empty),
            f"build/review task rows={len(built_or_ready)}",
        )

    if "manifest_gate" in manifest.columns:
        planned_manifest = manifest[manifest["path"].astype(str).isin(plan_paths)].copy()
        bad_manifest = planned_manifest[~planned_manifest["manifest_gate"].astype(str).str.startswith("PASS")]
        add(
            checks,
            "planned_slots_have_valid_artifact_manifests",
            "ERROR",
            status_from_condition(bad_manifest.empty and len(planned_manifest) == len(plan_paths)),
            f"nonpassing planned manifest rows={len(bad_manifest)}; manifest rows={len(planned_manifest)}",
        )

    if "package_gate" in final_package.columns:
        planned_package = final_package[final_package["path"].astype(str).isin(plan_paths)].copy()
        bad_package = planned_package[planned_package["package_gate"].astype(str).str.startswith("FAIL")]
        add(
            checks,
            "planned_slots_have_no_final_package_failures",
            "ERROR",
            status_from_condition(bad_package.empty and len(planned_package) == len(plan_paths)),
            f"failing planned package rows={len(bad_package)}; package rows={len(planned_package)}",
        )
        if pending or running or batch_status == "WAIT_EXTERNAL_CONTEXT":
            package_gates = set(planned_package.get("package_gate", pd.Series(dtype=str)).astype(str))
            add(
                checks,
                "blocked_release_blocks_final_packaging",
                "ERROR",
                status_from_condition(package_gates <= {"BLOCKED_RELEASE_GATE"}),
                f"package gates while external context pending={sorted(package_gates)}",
            )

    if "status" in result_application.columns:
        result_statuses = set(result_application["status"].astype(str))
        if kernel_updates or submission_updates:
            add(
                checks,
                "detected_updates_have_application_review_step",
                "ERROR",
                status_from_condition("REVIEW_REQUIRED" in result_statuses),
                f"result application statuses={sorted(result_statuses)}",
            )
        if pending or running or batch_status == "WAIT_EXTERNAL_CONTEXT":
            blocking_rows = result_application[result_application.get("blocks_release", pd.Series(dtype=bool)).astype(str) == "True"]
            add(
                checks,
                "pending_context_has_result_application_blockers",
                "ERROR",
                status_from_condition(not blocking_rows.empty),
                f"blocking result-application rows={len(blocking_rows)}",
            )

    if "release_gate" in release.columns:
        ready_rows = release[release["release_gate"].astype(str) == "READY"]
        if not ready_rows.empty:
            add(
                checks,
                "ready_rows_require_final_review_action",
                "ERROR",
                status_from_condition(set(ready_rows["current_action"].astype(str)) == {"final_review_before_submit"}),
                "READY slots must be in final_review_before_submit state",
            )
        else:
            add(checks, "no_slots_ready_for_submit", "INFO", "PASS", "no planned slot is currently releasable")

    return pd.DataFrame(checks)


def write_report(checks: pd.DataFrame, output: Path, csv_path: Path) -> None:
    errors = checks[(checks["severity"] == "ERROR") & (checks["status"] != "PASS")]
    warnings = checks[(checks["severity"] == "WARN") & (checks["status"] != "PASS")]
    overall = "PASS" if errors.empty else "FAIL"

    counts = checks.groupby(["severity", "status"]).size().reset_index(name="count") if not checks.empty else pd.DataFrame()
    lines = [
        "# Planning State Validation",
        "",
        "This report validates consistency between polling, readiness, audit summary, batch plan, and release gate state.",
        "",
        "## Overall",
        "",
        f"- Status: `{overall}`",
        f"- Error failures: `{len(errors)}`",
        f"- Warning failures: `{len(warnings)}`",
        "",
        "## Counts",
        "",
        markdown_table(counts),
        "",
        "## Checks",
        "",
        markdown_table(checks),
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
    parser.add_argument("--poll", type=Path, default=DEFAULT_POLL)
    parser.add_argument("--readiness", type=Path, default=DEFAULT_READINESS)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--well-impact", type=Path, default=DEFAULT_WELL_IMPACT)
    parser.add_argument("--diversity", type=Path, default=DEFAULT_DIVERSITY)
    parser.add_argument("--slot-review", type=Path, default=DEFAULT_SLOT_REVIEW)
    parser.add_argument("--slot-contingency", type=Path, default=DEFAULT_SLOT_CONTINGENCY)
    parser.add_argument("--replacement-pool", type=Path, default=DEFAULT_REPLACEMENT_POOL)
    parser.add_argument("--replacement-queue", type=Path, default=DEFAULT_REPLACEMENT_QUEUE)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--manifest-summary", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--final-package", type=Path, default=DEFAULT_FINAL_PACKAGE)
    parser.add_argument("--result-application", type=Path, default=DEFAULT_RESULT_APPLICATION)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    checks = validate(
        poll=safe_read_csv(args.poll),
        readiness=safe_read_csv(args.readiness),
        audit=safe_read_csv(args.audit),
        plan=safe_read_csv(args.plan),
        well_impact=safe_read_csv(args.well_impact),
        diversity=safe_read_csv(args.diversity),
        slot_review=safe_read_csv(args.slot_review),
        slot_contingency=safe_read_csv(args.slot_contingency),
        replacement_pool=safe_read_csv(args.replacement_pool),
        replacement_queue=safe_read_csv(args.replacement_queue),
        release=safe_read_csv(args.release),
        manifest=safe_read_csv(args.manifest_summary),
        final_package=safe_read_csv(args.final_package),
        result_application=safe_read_csv(args.result_application),
    )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    checks.to_csv(args.output_csv, index=False)
    write_report(checks, args.report, args.output_csv)

    failing_errors = checks[(checks["severity"] == "ERROR") & (checks["status"] != "PASS")]
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.report}")
    print(f"status={'PASS' if failing_errors.empty else 'FAIL'} error_failures={len(failing_errors)}")
    return 0 if failing_errors.empty else 1


if __name__ == "__main__":
    raise SystemExit(main())
