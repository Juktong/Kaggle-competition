#!/usr/bin/env python3
"""Poll Kaggle kernel status for rows in kernel_run_ledger.csv."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path


DEFAULT_LEDGER = Path("experiments/kernel_run_ledger.csv")
DEFAULT_POLL_STATUSES = {"RUNNING", "PENDING", "QUEUED"}
TERMINAL_STATUSES = {"COMPLETE", "ERROR", "CANCELLED"}


def normalize_status(value: str) -> str:
    value = str(value or "").strip().strip('"')
    if value.startswith("KernelWorkerStatus."):
        value = value.split(".", 1)[1]
    return value.upper()


def parse_status_output(output: str) -> str:
    match = re.search(r'has status\s+"([^"]+)"', output)
    if match:
        return normalize_status(match.group(1))
    tail = output.strip().splitlines()[-1:] or [""]
    return normalize_status(tail[0])


def fetch_kernel_status(kaggle_bin: str, slug: str) -> str:
    proc = subprocess.run(
        [kaggle_bin, "kernels", "status", slug],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or f"kaggle exited {proc.returncode}"
        raise RuntimeError(message)
    return parse_status_output(proc.stdout)


def load_ledger(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if reader.fieldnames is None:
            raise ValueError(f"ledger has no header: {path}")
        return reader.fieldnames, rows


def write_ledger(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def row_key(row: dict[str, str]) -> str:
    version = str(row.get("kernel_version", "")).strip()
    slug = str(row.get("kernel_slug", "")).strip()
    return f"{slug}/v{version}" if version else slug


def default_terminal_next_action(status: str) -> str:
    if status == "COMPLETE":
        return "download_output_and_deep_audit"
    if status == "ERROR":
        return "download_log_and_triage"
    if status == "CANCELLED":
        return "record_cancelled_and_rerank"
    return "review_kernel_status"


def sync(
    ledger_path: Path,
    kaggle_bin: str,
    poll_statuses: set[str],
    apply: bool,
    update_next_action: bool,
) -> dict[str, object]:
    fieldnames, rows = load_ledger(ledger_path)
    checked: list[dict[str, str]] = []
    updated: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    skipped: list[str] = []

    for row in rows:
        current = normalize_status(row.get("status", ""))
        slug = str(row.get("kernel_slug", "")).strip()
        if not slug or current not in poll_statuses:
            skipped.append(row_key(row))
            continue

        try:
            remote = fetch_kernel_status(kaggle_bin, slug)
        except Exception as exc:
            errors.append({"kernel": row_key(row), "error": str(exc)})
            continue

        checked.append({"kernel": row_key(row), "local_status": current, "remote_status": remote})
        if remote and remote != current:
            before = dict(row)
            row["status"] = remote
            if update_next_action and remote in TERMINAL_STATUSES:
                row["next_action"] = default_terminal_next_action(remote)
            updated.append(
                {
                    "kernel": row_key(before),
                    "from": current,
                    "to": remote,
                    "next_action": row.get("next_action", ""),
                }
            )

    summary: dict[str, object] = {
        "ledger": str(ledger_path),
        "checked": checked,
        "updated": updated,
        "errors": errors,
        "skipped_count": len(skipped),
        "apply": apply,
    }

    if apply and updated:
        write_ledger(ledger_path, fieldnames, rows)

    return summary


def parse_statuses(values: list[str]) -> set[str]:
    statuses: set[str] = set()
    for value in values:
        for part in value.split(","):
            part = normalize_status(part)
            if part:
                statuses.add(part)
    return statuses


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--kaggle-bin", default="kaggle")
    parser.add_argument("--poll-status", nargs="*", default=sorted(DEFAULT_POLL_STATUSES))
    parser.add_argument("--apply", action="store_true", help="Write changed statuses back to the ledger.")
    parser.add_argument(
        "--no-next-action-update",
        action="store_true",
        help="Do not adjust next_action when a row reaches a terminal status.",
    )
    args = parser.parse_args()

    try:
        summary = sync(
            ledger_path=args.ledger,
            kaggle_bin=args.kaggle_bin,
            poll_statuses=parse_statuses(args.poll_status),
            apply=args.apply,
            update_next_action=not args.no_next_action_update,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
