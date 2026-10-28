#!/usr/bin/env python3
"""Non-AI queue runner that starts ROGII autopilot tasks with Codex exec.

This is the Codex replacement for `claude_autopilot.py` while Claude Code auth is expired.
It uses the same queue and prompt files, but tracks Codex worker processes in
`.claude/autopilot/codex_jobs/`.
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
CODEX_JOBS = AUTOPILOT / "codex_jobs"
PROMPT_CACHE = AUTOPILOT / "codex_prompts"
KAGGLE = "/home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle"
COMP = "rogii-wellbore-geology-prediction"


ACTIVE_STATES = {"running", "working", "active", "starting"}
TERMINAL_STATES = {"done", "blocked", "failed", "error", "stopped", "cancelled"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_shell(cmd: str, timeout: int = 60) -> str:
    try:
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
    except subprocess.TimeoutExpired as exc:
        partial = (exc.stdout or "").strip() if isinstance(exc.stdout, str) else ""
        return f"TIMEOUT after {timeout}s\n{partial}".strip()


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
    return [json.loads(line) for line in QUEUE_PATH.read_text().splitlines() if line.strip()]


def save_queue(rows: list[dict]) -> None:
    QUEUE_PATH.write_text("".join(json.dumps(row, sort_keys=False) + "\n" for row in rows))


def pid_alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def job_state(handle: str | None) -> dict:
    if not handle:
        return {}
    if not handle.startswith("codex_"):
        return {"state": "missing", "handle": handle, "detail": "not a Codex autopilot handle"}
    status_path = CODEX_JOBS / handle / "status.json"
    if not status_path.exists():
        return {"state": "missing", "handle": handle}
    try:
        data = json.loads(status_path.read_text())
    except Exception as exc:
        return {"state": "unreadable", "handle": handle, "error": str(exc)}
    data["handle"] = handle
    if data.get("state") in ACTIVE_STATES and not pid_alive(data.get("pid")):
        data["state"] = "failed"
        data["detail"] = "worker pid no longer exists before status reached terminal"
        data["updated_at"] = utc_now()
        status_path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")
    return data


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
    js = job_state(current_handle)
    parts = [
        "=== utc_time ===",
        run_shell("date -u '+%Y-%m-%d %H:%M UTC'"),
        "",
        "=== git_status ===",
        run_shell("git status --short --branch && git log --oneline -5", 30),
        "",
        "=== fetch_status ===",
        run_shell("git fetch origin --quiet && git fetch juktong --quiet && echo fetch_ok", 60),
        "",
        "=== current_codex_job_state ===",
        json.dumps(
            {
                "handle": js.get("handle"),
                "state": js.get("state"),
                "detail": js.get("detail"),
                "pid": js.get("pid"),
                "log_file": js.get("log_file"),
                "last_message_file": js.get("last_message_file"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        "",
        "=== codex_auth_health ===",
        run_shell("codex login status 2>&1 | head -40", 30),
        "",
        "=== claude_auth_status ===",
        run_shell("cat ~/.claude/daemon-auth-status.json 2>/dev/null || true", 10),
        "",
        "=== kaggle_submissions_head ===",
        submissions,
        "",
        "=== quota_estimate_utc ===",
        f"used={quota_used}/5 remaining={max(0, 5 - quota_used)}/5",
        "",
        "=== local_processes ===",
        run_shell(
            "ps -eo pid,ppid,stat,etime,cmd | "
            "egrep 'codex|claude|kaggle|papermill|jupyter|python|ipykernel' | "
            "grep -v egrep | cut -c1-220 | head -40",
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
            if js.get("last_message_preview"):
                row["result"] = js["last_message_preview"]
            break
    state["last_finished_at"] = utc_now()
    state["current_handle"] = None
    state["current_task_id"] = None
    return True


def next_task(queue: list[dict]) -> dict | None:
    queued = [row for row in queue if row.get("status") == "queued"]
    if not queued:
        return None
    return sorted(queued, key=lambda r: (int(r.get("priority", 999)), r.get("id", "")))[0]


def build_prompt(task: dict, live: str) -> str:
    task_rel = task["path"]
    task_text = (AUTOPILOT / task_rel).read_text()
    return f"""You are Codex taking over the ROGII Kaggle autopilot because Claude Code auth expired.

Read these files fully before acting:
- .claude/autopilot/codex_context.md
- .claude/autopilot/standing_rules.md
- .claude/autopilot/templates/task_wrapper.md
- .claude/autopilot/{task_rel}

Use reasoning effort high. Continue through files, not hidden chat memory.

Do not only plan. Execute the selected task. If it is blocked, record the blocker in `queue.jsonl`, write a report if useful, commit and push, then leave the queue ready for the runner to continue.

Live status gathered by the non-AI runner:

```text
{live}
```

Selected task `{task['id']}`:

```text
{task_text}
```
"""


def start_codex_task(state: dict, queue: list[dict], task: dict, live: str, dry_run: bool = False) -> int:
    prompt = build_prompt(task, live)
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    handle = f"codex_{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{task['id']}"
    job_dir = CODEX_JOBS / handle
    job_dir.mkdir(parents=True, exist_ok=True)
    PROMPT_CACHE.mkdir(parents=True, exist_ok=True)
    prompt_file = PROMPT_CACHE / f"{handle}.md"
    log_file = job_dir / "codex.jsonl"
    last_file = job_dir / "last_message.md"
    status_file = job_dir / "status.json"
    prompt_file.write_text(prompt)

    if dry_run:
        print(f"DRY RUN: would start {task['id']} handle={handle} hash={prompt_hash} chars={len(prompt)}")
        return 0

    cmd = [
        sys.executable,
        str(REPO / "scripts" / "codex_task_worker.py"),
        "--repo",
        str(REPO),
        "--handle",
        handle,
        "--task-id",
        task["id"],
        "--prompt-file",
        str(prompt_file),
        "--log-file",
        str(log_file),
        "--last-message-file",
        str(last_file),
        "--status-file",
        str(status_file),
    ]
    proc = subprocess.Popen(cmd, cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    save_json(
        status_file,
        {
            "handle": handle,
            "task_id": task["id"],
            "state": "running",
            "detail": "codex worker launched",
            "pid": proc.pid,
            "started_at": utc_now(),
            "updated_at": utc_now(),
            "log_file": str(log_file),
            "last_message_file": str(last_file),
        },
    )

    for row in queue:
        if row.get("id") == task["id"]:
            row["status"] = "in_progress"
            row["started_at"] = utc_now()
            row["handle"] = handle
            row["prompt_hash"] = prompt_hash
            break
    state["agent_provider"] = "codex"
    state["current_handle"] = handle
    state["current_task_id"] = task["id"]
    state["last_started_at"] = utc_now()
    state["queue_exhausted"] = False
    save_queue(queue)
    save_json(STATE_PATH, state)
    SENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SENT_LOG_PATH.open("a") as f:
        f.write(json.dumps({
            "at": utc_now(),
            "provider": "codex",
            "task_id": task["id"],
            "handle": handle,
            "prompt_hash": prompt_hash,
            "prompt_chars": len(prompt),
            "reasoning_effort": "high",
        }, sort_keys=False) + "\n")
    print(f"backgrounded · {handle} · ROGII Codex autopilot {task['id']}")
    print(f"  status {status_file}")
    print(f"  log    {log_file}")
    print(f"  last   {last_file}")
    return 0


def run_once(dry_run: bool = False) -> int:
    state = load_json(STATE_PATH, {})
    queue = load_queue()
    js = job_state(state.get("current_handle"))

    if js.get("state") in ACTIVE_STATES:
        print(f"Active Codex job {state.get('current_handle')}: {js.get('state')} - {js.get('detail')}")
        return 0

    if mark_current_task_finished(state, queue, js):
        save_queue(queue)
        save_json(STATE_PATH, state)

    task = next_task(queue)
    if not task:
        state["queue_exhausted"] = True
        save_json(STATE_PATH, state)
        print("No queued tasks remain.")
        return 0

    live = live_status(state.get("current_handle"))
    return start_codex_task(state, queue, task, live, dry_run=dry_run)


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
