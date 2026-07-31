---
id: status_summary_for_user
priority: 100
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Status Summary For User

Produce a concise Chinese status summary for the owner.

Must include:

- Whether a Claude job is still running.
- Current candidate/task.
- Whether any Kaggle GPU/kernel is running.
- Daily quota used/remaining.
- New or modified files.
- Latest commit SHA.
- New submission ref and public score, if any.
- Current slot1/slot2 recommendation by score-first, diversity-first, and provenance-first.
- What the autopilot will do next.

Do not run heavy experiments. Do not submit.
