#!/usr/bin/env python3
"""Check whether planned ROGII submission slots are allowed to release."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_PLAN = Path("experiments/next_submission_batch_plan.csv")
DEFAULT_POLL = Path("experiments/poll_refresh_summary.csv")
DEFAULT_OUTPUT_CSV = Path("experiments/submission_release_gate.csv")
DEFAULT_REPORT = Path("reports/submission_release_gate_report.md")


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


def overall_gate(plan: pd.DataFrame, poll: pd.DataFrame) -> tuple[str, str]:
    pending = int_poll_value(poll, "pending_official_submissions")
    running = int_poll_value(poll, "running_kernels")
    kernel_updates = int_poll_value(poll, "kernel_updates_detected")
    submission_updates = int_poll_value(poll, "submission_updates_detected")
    batch_status = poll_value(poll, "batch_status", "")

    if kernel_updates or submission_updates:
        return "REVIEW_LEDGER_UPDATES", "External updates were detected in dry-run; apply reviewed ledger changes and rerun."
    if pending or running or batch_status == "WAIT_EXTERNAL_CONTEXT":
        return "BLOCKED_EXTERNAL_CONTEXT", "Pending official scores or running kernels still affect candidate interpretation."
    if batch_status == "NEEDS_NEW_ARCHITECTURE_CANDIDATES":
        return "BLOCKED_STRATEGY_PIVOT", "Official calibration rejected the planned branch family; build new structural candidates before submitting."
    if plan.empty:
        return "BLOCKED_NO_PLAN", "No planned submission slots are available."
    if set(plan.get("current_action", pd.Series(dtype=str)).astype(str)) != {"final_review_before_submit"}:
        return "BLOCKED_PLAN_NOT_RELEASED", "Batch plan has not moved all selected slots to final review."
    return "READY_FOR_FINAL_REVIEW", "External blockers are clear; run final manual review before any official submission."


def slot_gate(row: pd.Series, overall_status: str) -> tuple[str, str]:
    action = str(row.get("current_action", ""))
    audit_gate = str(row.get("audit_gate", ""))
    submission_gate = str(row.get("submission_gate", ""))
    batch_status = str(row.get("batch_status", ""))

    if overall_status.startswith("BLOCKED") or overall_status == "REVIEW_LEDGER_UPDATES":
        return overall_status, str(row.get("release_condition", "Wait for external context to clear."))
    if action != "final_review_before_submit" or batch_status != "READY_FOR_RELEASE_REVIEW":
        return "BLOCKED_PLAN_NOT_RELEASED", "Refresh the batch plan after external context clears."
    if audit_gate not in {"AUDIT_PASS", "AUDIT_PASS_WARN_REVIEW"}:
        return "BLOCKED_AUDIT", "Audit evidence is missing or failing."
    if audit_gate == "AUDIT_PASS_WARN_REVIEW":
        return "MANUAL_REVIEW_REQUIRED", "Audit passed with warnings; review warnings and candidate purpose before submit."
    if submission_gate not in {"READY", "READY_REVIEW_WARNINGS"}:
        return "MANUAL_REVIEW_REQUIRED", "Candidate is not marked READY by the audit summary."
    return "READY", "Eligible for official submission after final human/strategy review."


def build_gate(plan: pd.DataFrame, poll: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    status, reason = overall_gate(plan, poll)
    if plan.empty:
        return pd.DataFrame(), status, reason

    rows = []
    for _, row in plan.iterrows():
        gate, gate_reason = slot_gate(row, status)
        rows.append(
            {
                "planned_slot": row.get("planned_slot", ""),
                "candidate_id": row.get("candidate_id", ""),
                "path": row.get("path", ""),
                "slot_role": row.get("slot_role", ""),
                "family": row.get("family", ""),
                "release_gate": gate,
                "release_reason": gate_reason,
                "current_action": row.get("current_action", ""),
                "batch_status": row.get("batch_status", ""),
                "audit_gate": row.get("audit_gate", ""),
                "submission_gate": row.get("submission_gate", ""),
                "priority_score": row.get("priority_score", ""),
                "release_condition": row.get("release_condition", ""),
            }
        )
    return pd.DataFrame(rows), status, reason


def write_report(gates: pd.DataFrame, status: str, reason: str, output: Path, csv_path: Path) -> None:
    cols = [
        "planned_slot",
        "slot_role",
        "family",
        "release_gate",
        "current_action",
        "priority_score",
        "path",
        "release_reason",
    ]
    cols = [c for c in cols if c in gates.columns]
    counts = gates["release_gate"].value_counts().rename_axis("release_gate").reset_index(name="count") if not gates.empty else pd.DataFrame()
    lines = [
        "# Submission Release Gate",
        "",
        "This report checks whether the planned official submission slots may be released. It does not submit anything.",
        "",
        "## Overall Gate",
        "",
        f"- Status: `{status}`",
        f"- Reason: {reason}",
        "",
        "## Gate Counts",
        "",
        markdown_table(counts),
        "",
        "## Planned Slot Gates",
        "",
        markdown_table(gates[cols] if cols else gates),
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
    parser.add_argument("--poll", type=Path, default=DEFAULT_POLL)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    plan = safe_read_csv(args.plan)
    poll = safe_read_csv(args.poll)
    gates, status, reason = build_gate(plan, poll)

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    gates.to_csv(args.output_csv, index=False)
    write_report(gates, status, reason, args.report, args.output_csv)

    print(f"wrote {args.output_csv}")
    print(f"wrote {args.report}")
    print(f"{status}: {reason}")
    if not gates.empty:
        print(gates[["planned_slot", "candidate_id", "release_gate"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
