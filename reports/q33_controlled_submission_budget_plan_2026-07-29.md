# Q33 — controlled submission budget plan

Date: 2026-07-29 04:15 UTC
Task: `q33_controlled_submission_budget_plan` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Outcome: **plan produced. No submission (the task forbids one). Quota untouched at 0/5.**

## 1. The budget, and the fact that reframes it

| | |
|---|---|
| now | 2026-07-29 04:15 UTC |
| deadline | **2026-08-05 23:59 UTC** |
| UTC days remaining (07-29 … 08-05 inclusive) | **8** |
| slots remaining | **8 × 5 = 40** |
| used today (07-29) | **0 / 5** |
| measured scoring latency | **≤ 7.7 h** (`55064411`, still PENDING at 6.5 h) |

**The reframing: zero of those 40 slots are required.**

The final score is the best of **2 selected submissions**, and selection is made from entries that are
*already submitted*. Every candidate in every current recommendation — `54922806` (6.563), `54968060`
(6.643), `54844628` (7.891) — is already submitted and scored. So the current recommendation is
**executable today at a cost of 0 slots**. All 40 remaining slots are discretionary, and the only
question is what information they can buy.

## 2. What a slot can buy, measured

`55064411` landed this round at **6.695** and is the concrete test case. It was a one-line, diff-verified
change against the kernel that produced `54968060` (6.643), so the controlled contrast is:

```
hedge OFF (55064411)  6.695
hedge ON  (54968060)  6.643
                      ------
                      +0.052
```

Against a **config-variance floor of ~0.115**, and against Q18's measurement that pooled gaps ≤ 0.30
reverse on ~45% of random 3-well draws, **+0.052 carries no resolving power**. One slot was spent and
returned no adjudication.

That yields a quantitative criterion, derived from measurement rather than taste:

> **A submission is worth a slot only if its expected public effect exceeds ~0.115.**
> Below that, the leaderboard returns run-to-run noise, not evidence.

Three independent results all point the same way: Q18 (the 0.080 deciding slot 1 is unresolvable),
Q19 (nothing in the public pool to adopt — the published notebooks top out at 7.06–8.86 and the ~200
teams ahead of us have not published), and now `55064411` (+0.052, unresolvable).

## 3. Categorisation of every remaining candidate

| category | candidates | slots needed |
|---|---|---|
| **submittable now** | *none* — no candidate passes the submit gate | 0 |
| **smoke/full needed** | `q37_frontier_gr_sigma_public_repro` (one-token `gs*1.3` frontier run), **blocked** behind `q36` | 1, conditional |
| **diagnostic only** | `q23_frontier_stage_localizer`, `q24_frontier_run_variance_control` (both deferred) | 0 — value of information now below the floor |
| **final-slot only** | `54922806`, `54968060`, `54844628` — all already submitted and scored | **0** |
| **close** | `55064411` (measured, does not enter a slot); plus the standing closed list from Q20 §5 | 0 |

`q36_gr_sigma_in_blend_oof` is `can_submit=false` — it is validation, not a submission, and it is the
gate that decides whether `q37` is ever worth its slot.

## 4. Recommended maximum for the next 24 h: **1**

- **0 submissions** unless `q36` passes its 3-well gate (nested gain > 0 **and** bootstrap 5th > 0 **and**
  helps a majority of wells).
- **1 submission** if it does: `q37`, the one-token `gs*1.3` frontier reproduction, after a smoke.

Rationale for such a low rate with 40 slots in hand: slots are not the scarce resource — *resolving power*
is. Spending slots on sub-0.115 contrasts converts quota into noise, which is exactly what the last slot
did. Holding slots costs nothing, because the final pair needs none of them.

## 5. Contingency for delayed Kaggle scoring

The measured latency is **≤ 7.7 h** (`55064411`: submitted 07-28 20:30, still PENDING at 6.5 h, COMPLETE
by 04:14). This supersedes the ~1 h expectation recorded in `41bb65f`, which had assumed latency tracks
kernel runtime. Kernels-only scoring re-runs the kernel *and* queues behind other users.

Planning consequences:

1. **Serial information rounds cost ~8 h each.** A submission whose result must inform the *next*
   submission cannot be turned around more than ~2–3 times per day. Parallel submissions still score
   independently, so breadth is cheap and depth is expensive.
2. **Last informative submission: 2026-08-05 12:00 UTC.** That leaves ~12 h of margin against a measured
   7.7 h latency before the 23:59 deadline. Treat this as hard.
3. **Last submission of any kind: 2026-08-05 16:00 UTC**, and only if its result is not needed for the
   selection decision.
4. **Do not resubmit a PENDING entry.** It spends a slot on a near-duplicate and does not clear the queue.
5. **A stall is not a failure.** `55064411` sat PENDING for 6.5 h with `error_description` empty while
   `kernels_status` reported `COMPLETE, failureMessage null`.

## 6. The action that has no quota cost and a hard deadline

**Selecting the final 2 submissions is a separate action from submitting them.** It does not consume
quota, but it *does* have to happen before 2026-08-05 23:59 UTC, and if it is not done Kaggle falls back
to its own default choice. This is the single highest-consequence remaining step and it is currently
unscheduled.

**Recommendation: perform the selection by 2026-08-04**, a full day early, using whichever pair the owner
prefers from §7. It can be revised afterwards if something changes; leaving it to the final hours cannot.

## 7. Final pair — unchanged by this round

| view | pair | note |
|---|---|---|
| score / diversity / provenance-first | `54922806` + `54844628` | best public number on the board |
| our-account-first | `54968060` + `54844628` | both slots on our own account; costs +0.000 worst, +0.040 mean |

Per Q18, the 0.080 separating the two slot-1 options is not resolvable at 3-well scale, so this remains an
**ownership judgement for the owner**, not something further submissions can settle. `55064411` (6.695)
does not enter either pair.

## 8. Endgame scheduling — the Q20 addendum discharged

Q20 deferred two deadline-critical tasks and made this task responsible for re-queueing them, because the
runner only selects `status == "queued"` and deferred rows are never picked.

| task | action taken | scheduled for |
|---|---|---|
| `q35_status_summary_for_owner` | **re-queued now**, priority 550 | next rounds — timely, since `55064411` landed and the public standing is newly measured |
| `q29_final_slot_candidate_packager` | **re-queued now**, priority 560, with a self-check | it must verify its trigger and **re-defer itself with a new target date** if unmet |

`q29`'s trigger, written into its prompt: proceed only if (a) date ≥ **2026-08-03**, and (b) `q36` has
reported. If either fails, re-defer and record the new target — so the task can neither run prematurely
nor be silently lost.

## 9. Day-by-day allocation

| date (UTC) | planned submissions | purpose |
|---|---|---|
| 07-29 | **0–1** | only `q37`, and only if `q36` passes its gate |
| 07-30 → 08-02 | **≤ 1/day** | only candidates with an expected effect > 0.115; otherwise none |
| 08-03 | 0 | `q29` final packaging |
| **08-04** | 0 | **perform the final selection** (no quota cost) |
| 08-05 | 0 | reserve only; last informative submission 12:00 UTC if anything is genuinely open |

Expected total spend: **0–4 of 40**. The plan deliberately leaves most of the budget unused, because the
measured evidence says additional submissions inside the noise floor do not improve the private outcome.

## 10. Limits

- The 0.115 config-variance floor comes from a prior measurement of GPU run-to-run nondeterminism, not
  from a large sample; it is the best figure available but is itself uncertain.
- The 7.7 h latency is an **upper bound from one observation** (the true value lies between 6.5 h and
  7.7 h). Queue depth may differ near the deadline, plausibly worse, which is why §5 uses 12 h of margin.
- "40 slots" assumes the daily allowance resets at 00:00 UTC and that no submission is rejected. Verified
  once, at the 07-28 → 07-29 rollover.
- This plan does not assert any candidate will improve the private score. It only allocates the budget so
  that slots are spent when they can resolve something and held when they cannot.

## 11. Next

`q36_gr_sigma_in_blend_oof` — it is the gate that determines whether the next 24 h spends 0 slots or 1.
