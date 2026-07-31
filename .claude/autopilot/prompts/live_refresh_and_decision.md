---
id: live_refresh_and_decision
priority: 5
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Live Refresh And Queue Decision

Refresh project state and update the queue without doing a heavy experiment.

Tasks:

- Check Kaggle submissions, daily quota, and whether any kernels are running.
- Check local processes for Claude/Kaggle/papermill/notebook/watchers.
- Check git status, fetch `origin` and `juktong`, and confirm PR branch state.
- Check whether Mark/Marc `origin/main` has new commits.
- Read the latest rotation reports and identify the next runnable queued task.
- Update `.claude/autopilot/state.json` if needed.
- Update `reports/rotation_pipeline_status_2026-07-26.md` only if the live state changed materially.

Do not submit anything. Do not run heavy training.
