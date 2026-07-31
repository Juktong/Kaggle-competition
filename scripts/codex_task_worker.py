#!/usr/bin/env python3
"""Run one queued ROGII autopilot task through Codex exec and write a small status file."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--handle", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--log-file", required=True)
    parser.add_argument("--last-message-file", required=True)
    parser.add_argument("--status-file", required=True)
    args = parser.parse_args()

    repo = Path(args.repo)
    prompt = Path(args.prompt_file).read_text()
    log_path = Path(args.log_file)
    last_path = Path(args.last_message_file)
    status_path = Path(args.status_file)

    status_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    last_path.parent.mkdir(parents=True, exist_ok=True)

    existing_status = {}
    if status_path.exists():
        try:
            existing_status = json.loads(status_path.read_text())
        except Exception:
            existing_status = {}

    status = {
        "handle": args.handle,
        "task_id": args.task_id,
        "state": "running",
        "detail": "codex exec running",
        "pid": existing_status.get("pid"),
        "started_at": utc_now(),
        "updated_at": utc_now(),
        "log_file": str(log_path),
        "last_message_file": str(last_path),
    }
    status_path.write_text(json.dumps(status, indent=2, sort_keys=False) + "\n")

    cmd = [
        "codex",
        "exec",
        "-C",
        str(repo),
        "--dangerously-bypass-approvals-and-sandbox",
        "-c",
        'model_reasoning_effort="high"',
        "--json",
        "-o",
        str(last_path),
        "-",
    ]
    with log_path.open("w") as log:
        proc = subprocess.run(
            cmd,
            input=prompt,
            cwd=repo,
            text=True,
            stdout=log,
            stderr=subprocess.STDOUT,
        )

    status.update(
        {
            "state": "done" if proc.returncode == 0 else "failed",
            "detail": f"codex exec exited {proc.returncode}",
            "returncode": proc.returncode,
            "finished_at": utc_now(),
            "updated_at": utc_now(),
        }
    )
    if last_path.exists():
        text = last_path.read_text(errors="replace").strip()
        status["last_message_preview"] = text[:2000]
    status_path.write_text(json.dumps(status, indent=2, sort_keys=False) + "\n")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
