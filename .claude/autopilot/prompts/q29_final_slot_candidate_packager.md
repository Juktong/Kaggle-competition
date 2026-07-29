---
id: q29_final_slot_candidate_packager
priority: 390
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q29 Final Slot Candidate Packager

Prepare a clear final-submission package that can be shared with teammates.

Goal:

- Keep final selection separate from ongoing experiments.
- Give score-first, diversity-first, provenance-first, and our-account-first recommendations.
- Include pending `55064411` handling.

Required execution:

1. Update final-slot package after Q21-Q28 and `55064411` status.
2. Produce a compact recommendation table:
   - slot 1;
   - slot 2;
   - backup if teammate submission unavailable;
   - backup if public-derived stack is disallowed by team preference;
   - pending-score contingency.
3. Do not submit.

Write `reports/q29_final_slot_candidate_packager_2026-07-29.md`.

## Q33 addendum (2026-07-29) — TRIGGER CHECK FIRST

This task was re-queued by `q33_controlled_submission_budget_plan` to discharge Q20's deferral risk.
**Before doing any packaging work, check the trigger:**

Proceed only if BOTH hold:
- (a) the current UTC date is **>= 2026-08-03**; and
- (b) `q36_gr_sigma_in_blend_oof` has reported (its row in `queue.jsonl` is `done` or `hold`).

**If either fails:** do NOT package. Instead set this row's `status` back to `"deferred"` in
`.claude/autopilot/queue.jsonl`, set `deferred_reason` to the unmet condition and a new target date, and
say so in one short report. This keeps the task from running prematurely without letting it be silently
lost — deferred rows are never picked by the runner.

Context when the trigger does fire: the final pair needs **0 quota slots** (all members are already
submitted and scored). The recommendation as of 2026-07-29 is `54922806` + `54844628` under score-,
diversity- and provenance-first, and `54968060` + `54844628` under our-account-first, at +0.000 worst /
+0.040 mean. Q18 showed the 0.080 separating the two slot-1 options is not resolvable at 3-well scale, so
present this as an **ownership judgement for the owner**, not as a score conclusion.

**Also flag in the report:** performing the final selection on Kaggle is a separate action from
submitting, costs no quota, and must be done before 2026-08-05 23:59 UTC. Q33 recommends doing it by
**2026-08-04**.
