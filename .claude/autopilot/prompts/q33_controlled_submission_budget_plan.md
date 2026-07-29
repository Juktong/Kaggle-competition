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
