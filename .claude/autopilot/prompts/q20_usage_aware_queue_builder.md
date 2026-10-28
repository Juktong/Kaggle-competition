---
id: q20_usage_aware_queue_builder
priority: 300
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q20 Usage-Aware Queue Builder

End-of-round management task. Build the next queue only from evidence, and avoid broad long-context loops.

Goal:

- Summarise Q10-Q19.
- Keep only candidates with a concrete smoke and plausible gain.
- Limit the next queue to high-value tasks unless a task itself discovers strong evidence.

Required execution:

1. Read `sent_log.jsonl`, current queue, and latest reports.
2. Summarise:
   - tasks completed;
   - submissions used;
   - current quota;
   - current Claude usage if available;
   - retained signals;
   - closed directions.
3. Add at most 5 next prompts unless strong evidence justifies more.
4. Keep prompt files short and let the runner attach live status.
5. Do not submit.

Write `reports/q20_usage_aware_queue_builder_2026-07-29.md`.
