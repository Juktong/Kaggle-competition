#!/usr/bin/env python3
"""Download a Kaggle kernel output folder and run deep submission audit."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


DEFAULT_DATA_DIR = Path("data/sample")
DEFAULT_REFERENCE_REGISTRY = Path("experiments/reference_submission_registry.csv")


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def download_output(kaggle_bin: str, kernel: str, output_dir: Path, force: bool) -> dict[str, object]:
    cmd = [kaggle_bin, "kernels", "output", kernel, "-p", str(output_dir)]
    if force:
        cmd.append("--force")
    proc = run_cmd(cmd)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def find_submission(output_dir: Path, file_name: str) -> Path:
    direct = output_dir / file_name
    if direct.is_file():
        return direct
    matches = sorted(output_dir.rglob(file_name))
    if not matches:
        raise FileNotFoundError(f"{file_name} not found under {output_dir}")
    if len(matches) > 1:
        joined = ", ".join(str(path) for path in matches[:8])
        raise RuntimeError(f"multiple {file_name} files found under {output_dir}: {joined}")
    return matches[0]


def run_pre_submit_audit(
    submission: Path,
    data_dir: Path,
    reference_registry: Path,
    json_out: Path,
) -> tuple[int, str, str, dict[str, object] | None]:
    cmd = [
        sys.executable,
        "scripts/pre_submit_audit.py",
        str(submission),
        "--data-dir",
        str(data_dir),
        "--reference-registry",
        str(reference_registry),
        "--json-out",
        str(json_out),
    ]
    proc = run_cmd(cmd)
    parsed = None
    if json_out.is_file():
        parsed = json.loads(json_out.read_text(encoding="utf-8"))
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip(), parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel", required=True, help="Kaggle kernel slug, e.g. owner/kernel-name")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--kaggle-bin", default="kaggle")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--reference-registry", type=Path, default=DEFAULT_REFERENCE_REGISTRY)
    parser.add_argument("--submission-name", default="submission.csv")
    parser.add_argument("--audit-name", default="deep_pre_submit_audit.json")
    parser.add_argument("--skip-download", action="store_true", help="Audit an existing output folder without calling Kaggle.")
    parser.add_argument("--force-download", action="store_true", help="Pass --force to kaggle kernels output.")
    parser.add_argument("--summary-out", type=Path, default=None)
    args = parser.parse_args()

    summary: dict[str, object] = {
        "kernel": args.kernel,
        "output_dir": str(args.output_dir),
        "download": None,
        "submission": None,
        "audit_json": str(args.output_dir / args.audit_name),
        "audit_status": None,
        "risk_status": None,
        "sha256_submission_csv": None,
        "errors": [],
        "warnings": [],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_download:
        download = download_output(args.kaggle_bin, args.kernel, args.output_dir, args.force_download)
        summary["download"] = download
        if download["returncode"] != 0:
            summary["errors"] = [download["stderr"] or download["stdout"] or "kernel output download failed"]
            text = json.dumps(summary, indent=2, sort_keys=True)
            print(text)
            if args.summary_out is not None:
                args.summary_out.parent.mkdir(parents=True, exist_ok=True)
                args.summary_out.write_text(text + "\n", encoding="utf-8")
            return 1
    else:
        summary["download"] = {"skipped": True}

    try:
        submission = find_submission(args.output_dir, args.submission_name)
        summary["submission"] = str(submission)
        audit_json = args.output_dir / args.audit_name
        code, stdout, stderr, audit = run_pre_submit_audit(
            submission=submission,
            data_dir=args.data_dir,
            reference_registry=args.reference_registry,
            json_out=audit_json,
        )
        summary["pre_submit_audit_returncode"] = code
        summary["pre_submit_audit_stderr"] = stderr
        if audit is None:
            summary["errors"] = ["audit JSON was not written"]
            if stdout:
                summary["pre_submit_audit_stdout"] = stdout
        else:
            summary["audit_status"] = audit.get("status")
            summary["risk_status"] = audit.get("risk_status")
            summary["sha256_submission_csv"] = audit.get("sha256_submission_csv")
            summary["errors"] = audit.get("errors", [])
            summary["warnings"] = audit.get("warnings", [])
            summary["rows"] = audit.get("rows")
        exit_code = 0 if code == 0 and summary["audit_status"] == "PASS" else 1
    except Exception as exc:
        summary["errors"] = [str(exc)]
        exit_code = 1

    text = json.dumps(summary, indent=2, sort_keys=True)
    print(text)
    if args.summary_out is not None:
        args.summary_out.parent.mkdir(parents=True, exist_ok=True)
        args.summary_out.write_text(text + "\n", encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
