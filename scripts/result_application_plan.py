#!/usr/bin/env python3
"""Turn current poll, score, and kernel state into an actionable result plan."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_POLL = Path("experiments/poll_refresh_summary.csv")
DEFAULT_SUBMISSIONS = Path("experiments/submission_ledger.csv")
DEFAULT_KERNELS = Path("experiments/kernel_run_ledger.csv")
DEFAULT_MATRIX = Path("experiments/result_branch_matrix.csv")
DEFAULT_RELEASE = Path("experiments/submission_release_gate.csv")
DEFAULT_FINAL_PACKAGE = Path("experiments/final_submission_package_summary.csv")
DEFAULT_OUTPUT_CSV = Path("experiments/result_application_plan.csv")
DEFAULT_REPORT = Path("reports/result_application_plan.md")

BASELINE_CANDIDATE = "lucifer_baseline_repro_joezzzzz"
FLEONGG_CANDIDATE = "fleongg_pretrained_branch_calibration"
DEGNONGUIDI_KERNEL = "joezzzzz/rogii-degnonguidi-7159-preflight-codex"
FLEONGG_COMPETITIVE_MARGIN = 0.10


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


def score(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return float("nan")


def latest_by(df: pd.DataFrame, column: str, value: str) -> pd.Series:
    if df.empty or column not in df.columns:
        return pd.Series(dtype=object)
    rows = df[df[column].astype(str) == value]
    if rows.empty:
        return pd.Series(dtype=object)
    return rows.iloc[-1]


def matrix_lookup(matrix: pd.DataFrame) -> dict[str, dict[str, str]]:
    if matrix.empty or "branch_id" not in matrix.columns:
        return {}
    out: dict[str, dict[str, str]] = {}
    for _, row in matrix.iterrows():
        out[str(row.get("branch_id", ""))] = {key: str(row.get(key, "")) for key in matrix.columns}
    return out


def branch_command(branches: dict[str, dict[str, str]], branch_id: str, fallback: str = "") -> str:
    row = branches.get(branch_id, {})
    return row.get("next_command", "") or fallback


def add_row(
    rows: list[dict[str, Any]],
    area: str,
    branch_id: str,
    status: str,
    action: str,
    evidence: str,
    command: str,
    blocks_release: bool,
) -> None:
    rows.append(
        {
            "area": area,
            "branch_id": branch_id,
            "status": status,
            "action": action,
            "evidence": evidence,
            "next_command": command,
            "blocks_release": blocks_release,
        }
    )


def build_plan(
    poll: pd.DataFrame,
    submissions: pd.DataFrame,
    kernels: pd.DataFrame,
    matrix: pd.DataFrame,
    release: pd.DataFrame,
    final_package: pd.DataFrame,
) -> tuple[pd.DataFrame, str, str]:
    rows: list[dict[str, Any]] = []
    branches = matrix_lookup(matrix)

    submission_updates = int_poll_value(poll, "submission_updates_detected")
    kernel_updates = int_poll_value(poll, "kernel_updates_detected")
    pending = int_poll_value(poll, "pending_official_submissions")
    running = int_poll_value(poll, "running_kernels")
    validation_errors = int_poll_value(poll, "planning_validation_error_failures")

    if submission_updates or kernel_updates:
        commands = []
        if submission_updates:
            commands.append("python3 scripts/poll_and_refresh_state.py --apply-submission-updates")
        if kernel_updates:
            commands.append("python3 scripts/poll_and_refresh_state.py --apply-kernel-updates")
        add_row(
            rows,
            "ledger_updates",
            "REVIEW_LEDGER_UPDATES",
            "REVIEW_REQUIRED",
            "Review dry-run updates, apply ledger changes explicitly, then rerun the full poll refresh.",
            f"submission_updates={submission_updates}; kernel_updates={kernel_updates}",
            " && ".join(commands),
            True,
        )
    else:
        add_row(
            rows,
            "ledger_updates",
            "NO_UNAPPLIED_UPDATES",
            "PASS",
            "No dry-run ledger updates were detected in the latest poll.",
            "submission_updates=0; kernel_updates=0",
            "python3 scripts/poll_and_refresh_state.py",
            False,
        )

    baseline = latest_by(submissions, "candidate_id", BASELINE_CANDIDATE)
    baseline_status = str(baseline.get("status", "") or "").lower()
    baseline_score = score(baseline.get("public_score", ""))
    baseline_valid = baseline_status == "complete" and np.isfinite(baseline_score) and baseline_score <= 8.5

    if baseline_status in {"pending", "submitted", "running"} or not baseline_status:
        add_row(
            rows,
            "baseline_anchor",
            "WAIT_BASELINE_SCORE",
            "WAIT",
            "Keep planned slots blocked until active-account baseline score resolves.",
            f"status={baseline_status or 'missing'}; public_score={fmt(baseline_score)}",
            "python3 scripts/poll_and_refresh_state.py",
            True,
        )
    elif baseline_valid:
        add_row(
            rows,
            "baseline_anchor",
            "B01_baseline_anchor_valid",
            "ACTION_READY",
            "Promote the active-account baseline anchor and allow dependent candidate review.",
            f"status={baseline_status}; public_score={baseline_score:.6g}",
            branch_command(branches, "B01_baseline_anchor_valid"),
            False,
        )
    else:
        add_row(
            rows,
            "baseline_anchor",
            "B02_baseline_anchor_failed",
            "BLOCK",
            "Block dependent submissions and repair the active-account baseline path first.",
            f"status={baseline_status}; public_score={fmt(baseline_score)}",
            branch_command(branches, "B02_baseline_anchor_failed"),
            True,
        )

    fleongg = latest_by(submissions, "candidate_id", FLEONGG_CANDIDATE)
    fleongg_status = str(fleongg.get("status", "") or "").lower()
    fleongg_score = score(fleongg.get("public_score", ""))
    if not baseline_valid:
        add_row(
            rows,
            "fleongg_calibration",
            "WAIT_BASELINE_FIRST",
            "WAIT",
            "Fleongg interpretation depends on a valid active-account baseline anchor.",
            f"baseline_valid={baseline_valid}; fleongg_status={fleongg_status or 'missing'}",
            "python3 scripts/poll_and_refresh_state.py",
            True,
        )
    elif fleongg_status in {"pending", "submitted", "running"} or not fleongg_status:
        add_row(
            rows,
            "fleongg_calibration",
            "WAIT_FLEONGG_SCORE",
            "WAIT",
            "Keep blend sweep blocked until Fleongg calibration score resolves.",
            f"status={fleongg_status or 'missing'}; public_score={fmt(fleongg_score)}",
            "python3 scripts/poll_and_refresh_state.py",
            True,
        )
    elif np.isfinite(fleongg_score) and fleongg_score <= baseline_score + FLEONGG_COMPETITIVE_MARGIN:
        add_row(
            rows,
            "fleongg_calibration",
            "B03_fleongg_competitive",
            "ACTION_READY",
            "Prioritize the SP45+Fleongg blend sweep after final release checks.",
            f"baseline={baseline_score:.6g}; fleongg={fleongg_score:.6g}; margin={FLEONGG_COMPETITIVE_MARGIN:.2f}",
            branch_command(branches, "B03_fleongg_competitive"),
            False,
        )
    else:
        add_row(
            rows,
            "fleongg_calibration",
            "B04_fleongg_weak",
            "ACTION_READY",
            "Downweight Fleongg blend slots and rerank toward SP45/plateau alternatives.",
            f"baseline={baseline_score:.6g}; fleongg={fmt(fleongg_score)}; margin={FLEONGG_COMPETITIVE_MARGIN:.2f}",
            branch_command(branches, "B04_fleongg_weak"),
            False,
        )

    deg = latest_by(kernels, "kernel_slug", DEGNONGUIDI_KERNEL)
    deg_status = str(deg.get("status", "") or "").upper()
    deg_version = str(deg.get("kernel_version", "6") or "6")
    if deg_status in {"RUNNING", "PENDING", "QUEUED"} or not deg_status:
        add_row(
            rows,
            "degnonguidi_reference",
            "WAIT_DEGNONGUIDI_KERNEL",
            "WAIT",
            "Keep dependent release decisions blocked until Degnonguidi v6 reaches terminal state or is explicitly deferred.",
            f"status={deg_status or 'missing'}; version={deg_version}",
            "python3 scripts/poll_and_refresh_state.py",
            True,
        )
    elif deg_status == "COMPLETE":
        add_row(
            rows,
            "degnonguidi_reference",
            "B05_degnonguidi_complete_clean",
            "ACTION_READY",
            "Download Degnonguidi output and run deep audit before deciding whether to insert it.",
            f"status={deg_status}; version={deg_version}",
            branch_command(branches, "B05_degnonguidi_complete_clean"),
            True,
        )
    else:
        add_row(
            rows,
            "degnonguidi_reference",
            "B06_degnonguidi_error_or_defer",
            "ACTION_READY",
            "Record Degnonguidi terminal status or deferral, then rerun plan without waiting on it.",
            f"status={deg_status}; version={deg_version}",
            branch_command(branches, "B06_degnonguidi_error_or_defer"),
            False,
        )

    release_gates = set(release.get("release_gate", pd.Series(dtype=str)).astype(str)) if not release.empty else set()
    package_gates = set(final_package.get("package_gate", pd.Series(dtype=str)).astype(str)) if not final_package.empty else set()
    if pending or running or any(gate.startswith("BLOCKED") for gate in release_gates) or validation_errors:
        add_row(
            rows,
            "release_sequence",
            "RELEASE_BLOCKED",
            "WAIT",
            "Do not prepare or submit official slots until external blockers and validation errors clear.",
            f"pending={pending}; running={running}; release_gates={sorted(release_gates)}; validation_errors={validation_errors}",
            "python3 scripts/poll_and_refresh_state.py",
            True,
        )
    elif any(gate in {"READY_TO_PACKAGE", "REVIEW_READY_TO_PACKAGE"} for gate in package_gates):
        add_row(
            rows,
            "release_sequence",
            "PACKAGE_READY",
            "ACTION_READY",
            "Prepare the selected local package only after final review.",
            f"package_gates={sorted(package_gates)}",
            "python3 scripts/final_submission_package.py --prepare --planned-slot N",
            False,
        )
    else:
        add_row(
            rows,
            "release_sequence",
            "FINAL_REVIEW_REQUIRED",
            "REVIEW_REQUIRED",
            "Release blockers appear clear; perform final human/strategy review before packaging.",
            f"release_gates={sorted(release_gates)}; package_gates={sorted(package_gates)}",
            "python3 scripts/final_submission_package.py",
            True,
        )

    out = pd.DataFrame(rows)
    if submission_updates or kernel_updates:
        overall = "REVIEW_LEDGER_UPDATES"
        reason = "Poll dry-run detected external updates that must be applied before branch decisions."
    elif pending or running:
        overall = "WAIT_EXTERNAL_CONTEXT"
        reason = "Official scores or reference kernels are still pending."
    elif validation_errors:
        overall = "BLOCKED_VALIDATION"
        reason = "Planning validation has error failures."
    elif any(out["status"].astype(str).isin(["BLOCK", "REVIEW_REQUIRED"])):
        overall = "REVIEW_REQUIRED"
        reason = "At least one branch requires review before release."
    else:
        overall = "ACTION_READY"
        reason = "Branch actions can proceed according to the plan."
    return out, overall, reason


def write_report(plan: pd.DataFrame, overall: str, reason: str, output: Path, csv_path: Path) -> None:
    counts = plan["status"].value_counts().rename_axis("status").reset_index(name="count") if not plan.empty else pd.DataFrame()
    display_cols = ["area", "branch_id", "status", "blocks_release", "action", "evidence", "next_command"]
    display_cols = [col for col in display_cols if col in plan.columns]
    lines = [
        "# Result Application Plan",
        "",
        "This report turns current external-result state into concrete next actions. It does not edit ledgers or submit to Kaggle.",
        "",
        "## Overall",
        "",
        f"- Status: `{overall}`",
        f"- Reason: {reason}",
        "",
        "## Status Counts",
        "",
        markdown_table(counts),
        "",
        "## Action Plan",
        "",
        markdown_table(plan[display_cols] if display_cols else plan),
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
    parser.add_argument("--submissions", type=Path, default=DEFAULT_SUBMISSIONS)
    parser.add_argument("--kernels", type=Path, default=DEFAULT_KERNELS)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--release", type=Path, default=DEFAULT_RELEASE)
    parser.add_argument("--final-package", type=Path, default=DEFAULT_FINAL_PACKAGE)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    plan, overall, reason = build_plan(
        poll=safe_read_csv(args.poll),
        submissions=safe_read_csv(args.submissions),
        kernels=safe_read_csv(args.kernels),
        matrix=safe_read_csv(args.matrix),
        release=safe_read_csv(args.release),
        final_package=safe_read_csv(args.final_package),
    )
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    plan.to_csv(args.output_csv, index=False)
    write_report(plan, overall, reason, args.report, args.output_csv)
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.report}")
    print(f"{overall}: {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
