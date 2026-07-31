# ROGII submission ledger — 2026-07-26

Team = "lee Marc223" (`joezzzzz` + `leemarc223`), quota 5/day team-wide.
**Today (2026-07-26 UTC) used: 1 of 5 → 4 remaining.** Live-checked 15:09 UTC.
Deadline **2026-08-05 23:59 UTC** (~10.9 days).

## Board

| ref | date | public | side | role |
|---|---|---|---|---|
| `54922806` | 07-23 | **6.563** | teammate | best-public (frontier overlap-ON) — slot 1 |
| `54990075` | 07-26 | 6.690 | **ours** | frontier SP45-only — settled the post-SP45 question |
| `54968060` | 07-25 | **6.643** | **ours** | frontier overlap-OFF (validated no-retrieval) |
| `54896975` | 07-22 | 6.669 | teammate | frontier overlap-ON |
| `54923144` | 07-23 | 6.678 | teammate | frontier GR-sigma branch |
| `54844628` | 07-20 | 7.891 | ours | fully-owned honest — slot-2 provenance-first fallback |
| `54878409` | 07-21 | 7.953 | ours | excluded (regression) |

## Round 1 (2026-07-26)

**No submission.** Rotation infrastructure built and G1.2 completed with zero quota and zero GPU
(the frontier's own masked-split reports were reused). Round-2 candidate identified:
SP45-projection-only (non-homogeneous, best proxy RMSE) — needs smoke → full before the gate applies.

`54968060` was validated this round as a **genuine no-retrieval run** (`alpha=0.0`, `applied_wells=0`
in the selected prefix profile, plus `guarded_overlap_override: False`), so its 6.643 is a clean
measurement of the frontier without any train-copy lookup.

## Round 2 result (2026-07-26)

**`54990075` = 6.690 COMPLETE** (G2.1 SP45-projection-only, kernel
`joezzzzz/rogii-frontier-sp45-only-full` v1, commit `9f0d6a4`). Today 1/5 used, 4 remaining.

Pre-registered reading resolved to the `> 6.678` branch: **the frontier's post-SP45 stages earn their
place** on the leaderboard, and the local train-copy proxy that favoured SP45-only pointed the wrong way
— an independent confirmation of the G1.2 §3 saturation finding. The submission did its job: it answered
a question that no local evidence could settle.

Slot recommendation after this result (all three criteria converge):
**slot 1 `54922806` (6.563) + slot 2 `54844628` (7.891)** — see
`reports/final_slot_package_corrected_gate_2026-07-26.md`.

## 2026-07-28 (autopilot rounds 4–5)

**Quota used today: 0 of 5.** No submission. Board unchanged since `54990075` (6.690, 07-26).
Deadline 2026-08-05 23:59 UTC.

- Round 4 `live_refresh_and_decision`: state refreshed, queue advanced.
- Round 5 `g35_honest_prefix_calibration`: **closed on evidence, no submission** — the prefix-cut
  calibration prerequisite does not hold once the same-run confound is removed.

- Round 6 `g13_dependency_provenance_audit`: **completed, no submission**. Quota still **0/5 today**.
- Round 7 `g32_learned_alignment_smoke`: **completed, no submission**. Quota still **0/5 today**.

- Round 8 `g33_multi_hypothesis_smoke`: **closed on evidence, no submission**. Quota still **0/5 today**.

- Round 9 `frontier_variant_matrix_lite`: **no submission**, both live axes HOLD. Quota still **0/5 today**.

- Round 10 `new_direction_search`: **no submission** (`can_submit=false`, `max_submit_cost=0`). Quota still **0/5 today**.

- Round 11 `n4_conformal_well_uncertainty`: **no submission** (`can_submit=false`). Quota still **0/5 today**.

- Round 12 `n2_increment_structural_field`: **no submission** (3-well gate fails for both variants). Quota still **0/5 today**.

- Round 13 `n1_geometry_bounded_alignment`: **no submission** (`can_submit=false`, negative result). Quota still **0/5 today**.

- Round 14 `n3_multiscale_gr_matching`: **no submission** (`can_submit=false`, diagnostic). Quota still **0/5 today**.

- Round 15 `n6_public_solution_audit`: **no submission** (`can_submit=false`, survey; named repo 404, substitute audited). Quota still **0/5 today**.

- Round 16 `n5_typewell_fingerprint_families`: **no submission** (`can_submit=false`, diagnostic). Quota still **0/5 today**.

- Round 17 `n8_azimuth_matched_neighbours`: **no submission** (3-well gate fails at every tolerance). Quota still **0/5 today**.

- Round 18 `n7_q3d_tortuosity_features`: **no submission** (`can_submit=false`, gate failed). Quota still **0/5 today**.

- Round 19 `n9_self_correlation_prefix_template`: **no submission** (`can_submit=false`, gate failed). Quota still **0/5 today**. **Queue exhausted** — 19 rounds on 2026-07-28, zero submissions, quota never spent.

- Round 20 `q10_twh1_scorer_dp_candidate`: **no submission** (beats flat but does not narrow the gap to deployed; gate is an AND). Quota still **0/5 today**.

- Round 21 `q11_twh1_pf_seed_ranker`: **no submission** (every ranker arm loses to the PF mean default). Quota still **0/5 today**.

- Round 22 `q12_coverage_gated_self_template`: **no submission** (coverage does not stratify the effect). Quota still **0/5 today**.

- Round 23 `q13_twh1_self_hybrid_emission`: **no submission** (emission gain reverses sign through the DP). Quota still **0/5 today**.

- Round 25 `q14 collect + submit`: **SUBMITTED ref `55064411`** — frontier hedge-OFF
  (`_BH_CAP 2.00 -> 0.00`), kernel `joezzzzz/rogii-frontier-hedgeoff-full` v1, commit `f491826`,
  output sha256 `4eec813b1213c94d`. Quota **1/5**. Audit HARD PASS; non-homogeneous (rmse 1.756 vs
  54968060). **Public score still PENDING at hand-off (~45 min).**

  **Operational fact worth carrying:** this is a **kernels-only** competition, so submitting re-runs the
  kernel against the hidden test set. Scoring latency therefore tracks **kernel runtime (~1 hour)**, not
  the few minutes typical of file submissions. A `PENDING` status at 20-45 minutes is normal here and is
  not evidence of a problem — do not resubmit or assume failure on that basis. Poll on an hour-scale
  cadence.

## 2026-07-29 — `55064411` still PENDING; Q16 round consumed no quota

**Quota: 1/5 used for the day. No submission was made this round.** `q16_honest_twh1_residual_router`
closed on its prerequisite (signed-residual CV R^2 **-0.0802** by well; 3-well bootstrap 5th **-0.9333**)
and therefore never reached a submittable artifact — see
`reports/q16_honest_twh1_residual_router_2026-07-29.md`.

**`55064411`** (Q14 hedge-OFF; kernel `joezzzzz/rogii-frontier-hedgeoff-full` v1; commit `f491826`;
output sha256 `4eec813b1213c94d`) re-checked this round: **`SubmissionStatus.PENDING`, 2 h 20 m+** after
the 2026-07-28 20:30:17 UTC submission, `public_score` empty. This is now **past** the ~1 h
kernel-runtime expectation recorded in `41bb65f`. The carry-forward rule is unchanged — in a
kernels-only competition scoring re-runs the kernel, so PENDING is not itself a failure and is not a
reason to resubmit — but the latency is longer than the recorded expectation and that is worth noting
rather than smoothing over. A background poller remains armed; the score is the FIRST action of the
next round.

Standing scored references for the decision when it lands:

| ref | public | note |
|---|---|---|
| 54922806 | **6.563** | best scored frontier |
| 54968060 | 6.643 | overlap-OFF diagnostic |
| 54896975 | 6.669 | Kaiwalya PF bimodal midpoint repro |
| 54923144 | 6.678 | GR sigma 1.0 PF frontier |
| 54990075 | 6.690 | G2.1 SP45-projection-only |

If `55064411` lands at or below **6.563** it becomes an own-account frontier competitive with the
teammate's best, and the slot-1 recommendation should be re-evaluated on **provenance**.

**Tooling fact recorded for the next round's score check:** the `kaggle` package was missing from the
environment and was reinstalled with `python3 -m pip install --user --break-system-packages kaggle`
(PEP 668 environment). Credentials resolve from `~/.kaggle/access_token`. The API returns **snake_case**
attributes — `s.public_score`, `s.private_score`, `s.status` — not the camelCase names.

## 2026-07-29 addendum — `55064411` scoring has STALLED, and the UTC day has rolled over

Two facts established after the Q16 round closed, both material for the remaining schedule.

### 1. The scoring stall is on Kaggle's side, not ours

`55064411` is **still `PENDING` roughly 4.5 h** after the 2026-07-28 20:30:17 UTC submission, after a
further 2 h of automated 3-minute polling. Full submission record: `public_score` `''`,
`private_score` `''`, **`error_description` `''`** — no failure is reported.

The kernel itself is healthy:

```
kernels_status('joezzzzz/rogii-frontier-hedgeoff-full')
  -> {"status": "COMPLETE", "failureMessage": null}
```

So the notebook is COMPLETE with no failure message, while the submission tied to
`scriptVersionId=338650633` remains unscored. **This is a Kaggle-side scoring-queue delay, not a defect
in our kernel or output.**

**This revises the expectation recorded in `41bb65f`.** That commit recorded scoring latency as tracking
the kernel's own runtime (~1 h). The observed latency is now ~4.5 h and still open, so ~1 h is a *floor*,
not an estimate. Revised operating rule:

- treat a PENDING of **several hours** as normal-but-unresolved in this kernels-only competition;
- **do NOT resubmit to "retry"** — it would spend a quota slot on a near-duplicate output, which the
  standing rules forbid, and would not clear the queue;
- **do not let any final-slot decision depend on a score that may not arrive.** With the deadline at
  2026-08-05 23:59 UTC, a candidate submitted late enough may never be scored before selection. Any
  submission intended to inform slot choice must go in with several hours of margin.

### 2. Daily quota reset — today is a fresh 5

Verified against the API at **2026-07-29 01:01 UTC**: submissions dated 2026-07-28 UTC = **1**
(that is `55064411`), submissions dated 2026-07-29 UTC = **0**.

The UTC day has rolled over, so **`55064411` no longer counts against today's quota**. As of now:

| | value |
|---|---|
| quota used today (2026-07-29 UTC) | **0 / 5** |
| quota remaining today | **5** |
| deadline | 2026-08-05 23:59 UTC (~7 days) |

The "quota 1/5, 4 remaining" figure recorded during the Q16 round was correct for 2026-07-28 and is
superseded for 2026-07-29. A pending-but-unscored submission from a previous day does not consume the
new day's allowance.

**Unchanged:** recording `55064411`'s score remains the first action of the next round *if it has landed*
— but the next round is no longer blocked on it, since a full quota is available and the stall is
external.

## 2026-07-29 04:15 UTC — `55064411` LANDED: public **6.695**

| field | value |
|---|---|
| ref | **55064411** |
| public | **6.695** |
| private | not visible (empty for every submission) |
| status | COMPLETE |
| submitted | 2026-07-28 20:30:17 UTC |
| scored by | 2026-07-29 04:14 UTC |
| **scoring latency** | **<= 7.7 h** (still PENDING at 6.5 h) |
| kernel | `joezzzzz/rogii-frontier-hedgeoff-full` v1 |
| commit | `f491826` |
| output sha256 | `4eec813b1213c94d` |
| quota | consumed on 2026-07-28; **0/5 used on 07-29** |

### The pre-registered reading, applied — and a correction to how it was framed

Q19 §4 pre-registered the reading before the number landed. Applying it requires one correction first,
and the correction changes which branch fires.

**The threshold was framed against the wrong comparator.** Q19 wrote "materially worse than 6.563", but
`54922806` (6.563) is a *different branch* — the teammate's overlap-ON rerun. `55064411` was built and
**diff-verified against the kernel that produced `54968060` (6.643)**, one line, `_BH_CAP 2.00 -> 0.00`.
The controlled contrast is therefore against 6.643, not 6.563.

```
55064411  6.695   hedge OFF   (overlap-OFF base)
54968060  6.643   hedge ON    (same base, one-line diff)
                  ------
delta     +0.052  cost of turning the hedge off, on public
```

**+0.052 is inside the ~0.115 config-variance floor**, and Q18 measured that pooled gaps <= 0.30 reverse
their ranking on ~45% of random 3-well draws. So the contrast is **not resolvable**. Neither pre-registered
branch fires cleanly; the honest outcome is a third one:

> **The bimodal hedge is not load-bearing on the public leaderboard, in either direction. The public
> score does not adjudicate Q14's local finding.**

### A second correction — the `my0705` datapoint is also inside the floor

Q19 §4 presented `my0705`'s result (base 6.568 -> 6.520 after pushing well `00e12e8b` a further +0.522 ft)
as support for "the hedge is tuned to the 3 public wells". That change is **−0.048**, likewise inside the
~0.115 floor. It does not establish the claim either. **The "hedge is tuned to public wells" hypothesis is
neither confirmed nor refuted — it is unresolvable at this scale**, and Q19's framing overstated it.

What survives unchanged: Q14's **local** measurement that the hedge applies +2.0 ft to `00e12e8b` whose
own residual was already −0.19 ft, manufacturing +1.81 ft of bias. That evidence is untouched by the
public result, because the public result carries no resolving power here.

### Consequence for the final slots — none

`55064411` at 6.695 is our **worst** frontier candidate on public and does not displace `54968060`
(6.643) as the our-account frontier representative. **The slot recommendation is unchanged:**

| view | pair |
|---|---|
| score / diversity / provenance-first | `54922806` + `54844628` |
| our-account-first | `54968060` + `54844628` |

### What the slot actually bought

One quota slot returned a contrast of +0.052 against a noise floor of ~0.115 — i.e. **no resolving
information**. This is the concrete, measured basis for the submission criterion adopted in Q33: a
submission is worth a slot only if its expected public effect exceeds the ~0.115 floor.
