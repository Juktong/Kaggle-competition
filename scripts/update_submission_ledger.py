#!/usr/bin/env python3
"""Sync Kaggle competition submission status into submission_ledger.csv."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_COMPETITION = "rogii-wellbore-geology-prediction"
DEFAULT_LEDGER = Path("experiments/submission_ledger.csv")


def normalize_status(value: str) -> str:
    value = str(value or "").strip()
    if value.startswith("SubmissionStatus."):
        value = value.split(".", 1)[1]
    return value.lower()


def normalize_score(value: str) -> str:
    value = str(value or "").strip()
    return value


def read_kaggle_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fetch_kaggle_csv(kaggle_bin: str, competition: str, page_size: int) -> list[dict[str, str]]:
    cmd = [
        kaggle_bin,
        "competitions",
        "submissions",
        competition,
        "--csv",
        "--page-size",
        str(page_size),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"kaggle exited {proc.returncode}")
    return list(csv.DictReader(proc.stdout.splitlines()))


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


def append_missing_row(krow: dict[str, str]) -> dict[str, str]:
    date = str(krow.get("date", "")).split(" ", 1)[0]
    ref = str(krow.get("ref", "")).strip()
    description = str(krow.get("description", "")).strip()
    return {
        "date_utc": date,
        "submission_id": ref,
        "candidate_id": f"unknown_{ref}" if ref else "unknown",
        "kernel_slug": "",
        "kernel_version": "",
        "file_name": str(krow.get("fileName", "")).strip(),
        "public_score": normalize_score(krow.get("publicScore", "")),
        "status": normalize_status(krow.get("status", "")),
        "decision": "needs_review",
        "audit_status": "unknown",
        "cv_summary": "",
        "notes": description,
    }


def sync(
    ledger_path: Path,
    kaggle_rows: list[dict[str, str]],
    append_missing: bool,
    dry_run: bool,
) -> dict:
    fieldnames, ledger_rows = load_ledger(ledger_path)
    by_id = {str(row.get("submission_id", "")).strip(): row for row in ledger_rows}

    updated = []
    appended = []
    unchanged = []
    missing = []

    for krow in kaggle_rows:
        ref = str(krow.get("ref", "")).strip()
        if not ref:
            continue
        status = normalize_status(krow.get("status", ""))
        score = normalize_score(krow.get("publicScore", ""))
        file_name = str(krow.get("fileName", "")).strip()

        row = by_id.get(ref)
        if row is None:
            if append_missing:
                new_row = append_missing_row(krow)
                ledger_rows.append(new_row)
                by_id[ref] = new_row
                appended.append(ref)
            else:
                missing.append(ref)
            continue

        before = dict(row)
        if status:
            row["status"] = status
        if score:
            row["public_score"] = score
        if file_name and not row.get("file_name"):
            row["file_name"] = file_name

        if row != before:
            updated.append(ref)
        else:
            unchanged.append(ref)

    summary = {
        "ledger": str(ledger_path),
        "kaggle_rows": len(kaggle_rows),
        "updated": updated,
        "appended": appended,
        "missing_not_appended": missing,
        "unchanged_known": unchanged,
        "dry_run": dry_run,
    }

    if not dry_run:
        write_ledger(ledger_path, fieldnames, ledger_rows)

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--competition", default=DEFAULT_COMPETITION)
    parser.add_argument("--csv-input", type=Path, default=None, help="Use an existing Kaggle submissions CSV instead of calling kaggle.")
    parser.add_argument("--kaggle-bin", default="kaggle")
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--append-missing", action="store_true", help="Append Kaggle rows not already present in the ledger as needs_review.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        if args.csv_input is not None:
            kaggle_rows = read_kaggle_csv(args.csv_input)
        else:
            kaggle_rows = fetch_kaggle_csv(args.kaggle_bin, args.competition, args.page_size)
        summary = sync(args.ledger, kaggle_rows, args.append_missing, args.dry_run)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
