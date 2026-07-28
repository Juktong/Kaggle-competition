#!/usr/bin/env python3
"""Small non-AI runner for the ROGII Claude prompt queue.

Most polling is shell-only and does not call Claude. Claude is called only when
there is no active job and the next queued prompt should be started.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
AUTOPILOT = REPO / ".claude" / "autopilot"
QUEUE_PATH = AUTOPILOT / "queue.jsonl"
STATE_PATH = AUTOPILOT / "state.json"
SENT_LOG_PATH = AUTOPILOT / "sent_log.jsonl"
CLAUDE = "/home/ubuntu/.local/bin/claude"
KAGGLE = "/home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle"
COMP = "rogii-wellbore-geology-prediction"


ACTIVE_STATES = {"working", "running", "active", "starting"}
TERMINAL_STATES = {"done", "blocked", "failed", "error", "stopped", "cancelled"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_shell(cmd: str, timeout: int = 60) -> str:
    proc = subprocess.run(
        cmd,
        cwd=REPO,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    return proc.stdout.strip()


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n")


def load_queue() -> list[dict]:
    if not QUEUE_PATH.exists():
        return []
    rows = []
    for line in QUEUE_PATH.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def save_queue(rows: list[dict]) -> None:
    QUEUE_PATH.write_text("".join(json.dumps(row, sort_keys=False) + "\n" for row in rows))


def job_state(handle: str | None) -> dict:
    if not handle:
        return {}
    path = Path.home() / ".claude" / "jobs" / handle / "state.json"
    if not path.exists():
        return {"state": "missing", "handle": handle}
    try:
        data = json.loads(path.read_text())
        data["handle"] = handle
        return data
    except Exception as exc:  # pragma: no cover - defensive for corrupt state
        return {"state": "unreadable", "handle": handle, "error": str(exc)}


def daily_quota_used(submissions_text: str) -> int:
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    used = 0
    for line in submissions_text.splitlines():
        if re.match(r"^\s*\d{6,}\s+", line) and today in line:
            used += 1
    return used


def live_status(current_handle: str | None) -> str:
    submissions = run_shell(f"{KAGGLE} competitions submissions {COMP} 2>/dev/null | head -14", 120)
    quota_used = daily_quota_used(submissions)
    quota_remaining = max(0, 5 - quota_used)
    js = job_state(current_handle)
    js_summary = {
        "handle": js.get("handle"),
        "state": js.get("state"),
        "detail": js.get("detail"),
        "tempo": js.get("tempo"),
        "tokens": js.get("tokens"),
        "sessionId": js.get("sessionId"),
    }
    parts = [
        "=== utc_time ===",
        run_shell("date -u '+%Y-%m-%d %H:%M UTC'"),
        "",
        "=== git_status ===",
        run_shell("git status --short --branch && git log --oneline -3", 30),
        "",
        "=== fetch_status ===",
        run_shell("git fetch origin --quiet && git fetch juktong --quiet && echo fetch_ok", 60),
        "",
        "=== current_claude_job_state ===",
        json.dumps(js_summary, ensure_ascii=False, indent=2),
        "",
        "=== kaggle_submissions_head ===",
        submissions,
        "",
        "=== quota_estimate_utc ===",
        f"used={quota_used}/5 remaining={quota_remaining}/5",
        "",
        "=== local_processes ===",
        run_shell(
            "ps -eo pid,ppid,stat,etime,cmd | "
            "egrep 'claude|kaggle|papermill|jupyter|python|ipykernel' | "
            "grep -v egrep | head -30",
            30,
        ),
    ]
    return "\n".join(parts)


def mark_current_task_finished(state: dict, queue: list[dict], js: dict) -> bool:
    task_id = state.get("current_task_id")
    if not task_id:
        return False
    status = js.get("state", "unknown")
    if status not in TERMINAL_STATES:
        return False
    for row in queue:
        if row.get("id") == task_id and row.get("status") == "in_progress":
            row["status"] = status
            row["finished_at"] = utc_now()
            row["detail"] = js.get("detail")
            row["handle"] = state.get("current_handle")
            break
    state["last_finished_at"] = utc_now()
    state["current_handle"] = None
    state["current_task_id"] = None
    if js.get("sessionId"):
        state["resume_session_id"] = js["sessionId"]
    return True


def next_task(queue: list[dict]) -> dict | None:
    queued = [row for row in queue if row.get("status") == "queued"]
    if not queued:
        return None
    return sorted(queued, key=lambda r: (int(r.get("priority", 999)), r.get("id", "")))[0]


def build_prompt(task: dict, live: str) -> str:
    task_rel = task["path"]
    task_path = AUTOPILOT / task_rel
    task_text = task_path.read_text()
    return f"""Continue the same ROGII Kaggle Claude context.

Read and obey these repo files before acting:
- .claude/autopilot/standing_rules.md
- .claude/autopilot/templates/task_wrapper.md
- .claude/autopilot/{task_rel}

Do not only plan. Execute the selected task. If it is blocked, record the blocker and move to the next queued task in the repo queue.

Live status gathered by the non-AI runner:

```text
{live}
```

Selected task `{task['id']}`:

```text
{task_text}
```
"""


def start_claude_task(state: dict, queue: list[dict], task: dict, live: str, dry_run: bool = False) -> int:
    prompt = build_prompt(task, live)
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    name = f"ROGII autopilot {task['id']} {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')}"

    if dry_run:
        print(f"DRY RUN: would start {task['id']} hash={prompt_hash} chars={len(prompt)}")
        return 0

    resume_id = state.get("resume_session_id")
    if not resume_id:
        raise RuntimeError("state.json missing resume_session_id")

    cmd = [
        CLAUDE,
        "--resume",
        resume_id,
        "--bg",
        "--effort",
        "max",
        "--permission-mode",
        "bypassPermissions",
        "--name",
        name,
        "--model",
        "opus",
        prompt,
    ]
    proc = subprocess.run(cmd, cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout)
    if proc.returncode != 0:
        return proc.returncode

    match = re.search(r"backgrounded\s+.\s+([0-9a-f]{8})", proc.stdout)
    if not match:
        match = re.search(r"\b([0-9a-f]{8})\b", proc.stdout)
    if not match:
        raise RuntimeError(f"Could not parse Claude handle from output: {proc.stdout}")
    handle = match.group(1)

    for row in queue:
        if row.get("id") == task["id"]:
            row["status"] = "in_progress"
            row["started_at"] = utc_now()
            row["handle"] = handle
            row["prompt_hash"] = prompt_hash
            break
    state["current_handle"] = handle
    state["current_task_id"] = task["id"]
    state["last_started_at"] = utc_now()
    save_queue(queue)
    save_json(STATE_PATH, state)
    SENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SENT_LOG_PATH.open("a") as f:
        f.write(json.dumps({
            "at": utc_now(),
            "task_id": task["id"],
            "handle": handle,
            "resume_session_id": resume_id,
            "prompt_hash": prompt_hash,
            "prompt_chars": len(prompt),
        }, sort_keys=False) + "\n")
    return 0


def run_once(dry_run: bool = False) -> int:
    state = load_json(STATE_PATH, {})
    queue = load_queue()
    current_handle = state.get("current_handle")
    js = job_state(current_handle)

    if js.get("state") in ACTIVE_STATES:
        print(f"Active Claude job {current_handle}: {js.get('state')} - {js.get('detail')}")
        return 0

    changed = mark_current_task_finished(state, queue, js)
    if changed:
        save_queue(queue)
        save_json(STATE_PATH, state)

    task = next_task(queue)
    if not task:
        print("No queued tasks remain.")
        return 0

    live = live_status(state.get("current_handle"))
    return start_claude_task(state, queue, task, live, dry_run=dry_run)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--sleep", type=int, default=900)
    args = parser.parse_args()

    if args.loop:
        while True:
            code = run_once(dry_run=args.dry_run)
            if code:
                return code
            time.sleep(args.sleep)
    return run_once(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
