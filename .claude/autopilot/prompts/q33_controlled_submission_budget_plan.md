---
id: q33_controlled_submission_budget_plan
priority: 430
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q33 Controlled Submission Budget Plan

Plan how to use remaining daily submissions with enough time margin.

Goal:

- Convert the remaining queue into a submission budget plan.
- Avoid spending slots on diagnostics after the value of information is low.

Required execution:

1. Read latest queue, ledger, and deadline.
2. Categorise remaining candidates:
   - submittable now;
   - smoke/full needed;
   - diagnostic only;
   - final-slot only;
   - close.
3. Recommend max submissions for the next 24h.
4. Include contingency for delayed Kaggle scoring.
5. Do not submit.

Write `reports/q33_controlled_submission_budget_plan_2026-07-29.md`.

## Q20 addendum (2026-07-29) — this task owns the endgame schedule

The queue was pruned to 5 active tasks. Two DEADLINE-CRITICAL tasks were deferred and **will never be
picked unless this task re-queues them** (the runner only selects `status == "queued"`):

- `q29_final_slot_candidate_packager`
- `q35_status_summary_for_owner`

Required: set both back to `status: "queued"` in `.claude/autopilot/queue.jsonl` at the right time, and
state in the report when they are scheduled for.

Budget facts as of 2026-07-29 03:00 UTC: deadline **2026-08-05 23:59 UTC**; **5/5 slots available today**;
0 used on 07-29; `55064411` PENDING ~6.5 h and does not consume today's allowance. Roughly **35 slots**
remain in total and none are allocated. Note Q18: score evidence cannot resolve the 0.080 that separates
the two slot-1 options, so slots spent to re-rank inside that band buy nothing.
