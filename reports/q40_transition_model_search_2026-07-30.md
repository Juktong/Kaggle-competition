# Q40 — transition-model search: the existing L1 term is the best of 45 arms

Date: 2026-07-29 17:25 UTC
Task: `q40_transition_model_search` (`requires_gpu=false`, `can_submit=true`, `max_submit_cost=1`)
Script: `scripts/q40_transition_model_search.py` · Log: `reports/logs/q40_transition_search_2026-07-30.log`
Outcome: **gate FAILS on all three conditions. No Kaggle path prepared, no submission. Quota 0/5.**

## 1. What the transition model actually is

Q17 closed the emission lever; Q10 and N1 both name the transition model as the remaining one. Reading
`scripts/q10_twh1_scorer_dp.py:run_dp`, the entire transition model is one term:

```python
step = C[j, lo:hi] + lam * |t - s| / BAND
```

An L1 penalty on the change in TVT state, **one parameter**, depending only on the previous state. Six
families were tested, all strictly containing it:

| family | term | idea |
|---|---|---|
| `l1` | `lam·\|d\|/BAND` | the baseline |
| `l2` | `lam·(d/BAND)²` | cheap small moves, expensive large ones |
| `huber` | L2 below `hub`, L1 above | small drift cheap, genuine jumps not over-penalised |
| `drift` | `lam·\|d − μ\|/BAND` | **trajectory-derived prior** — penalise deviation from the well's own heel-estimated drift, not from zero |
| `curv` | `lam·\|d − d_prev\|/BAND` | penalise change of slope rather than slope |
| `l1curv` | both, 2 parameters | |

`μ` is estimated **only from the known prefix** (median per-row change in `TVT_input`, scaled by the DP's
row subsampling), so it is test-available. `l1` is the `μ=0` special case of `drift`, making that arm a
clean single-factor test of *"does the DP wrongly assume zero drift is free?"*

Protocol per the standing rules: splits **by well**, 40 eval wells (same split seed as Q10/Q17), every
parameter chosen **nested**. Validation is on **DP output only**, never a pointwise emission metric —
Q17's rule.

## 2. Result — no variant beats the baseline

45 arms. The best arm of each family, pooled over 40 wells:

```
l1      lam=60             12.170     <- baseline, and the best of all 45 arms
huber   lam=150 hub=5      12.313
l1curv  lam=60 lam2=150    12.453
l2      lam=150            13.975
drift   lam=20             16.018
curv    lam=20             18.368
flat-anchor                12.722     deployed honest reference 8.8626
```

`l1` at λ=60 gives **12.170**, exactly reproducing Q10's headline — the harness is faithful.

Nested by well, each family against the `l1` family:

```
family      nested    l1 base       gain    helps%
l1          12.601     12.601     +0.000      0.0%
l1curv      12.854     12.601     -0.253     57.5%
l2          14.955     12.601     -2.355     42.5%
huber       15.444     12.601     -2.844     37.5%
curv        18.368     12.601     -5.767     40.0%
drift       24.076     12.601    -11.475     42.5%
```

All 45 arms pooled into one nested selection — the honest question:

```
nested-over-everything 14.452  vs l1 baseline 12.601  gain -1.851
helps 20.0% of held-out wells
3-WELL bootstrap 5th -5.845  50th -0.365  95th +2.847  P(>0) 0.3111
```

| gate condition | required | observed | verdict |
|---|---|---|---|
| nested gain over `l1` | > 0 | **−1.851** | FAIL |
| helps a majority of wells | > 50% | **20.0%** | FAIL |
| 3-well bootstrap 5th | > 0 | **−5.845** | FAIL |

**All three fail.** Note `l1curv` is the only family helping a majority (57.5%) yet still losing on nested
RMSE — a mirror image of the usual tail pattern, and not enough to pass.

## 3. The informative negative — why the drift prior fails, measured

`drift` was the most principled idea and it failed hardest (−11.475). With μ ≈ 0 in most wells
(mean +0.045, median +0.000, |μ|>1 in only 2%), it should have been nearly identical to `l1`. It was not,
so the mechanism was tested rather than assumed:

```
degeneracy control: 11 wells with mu EXACTLY 0  ->  max|drift - l1| = 0.000000
                    29 wells with mu != 0       ->  mean degradation +2.216
corr(|mu|, degradation)        = +0.796
DP steps per well: median 477, max 783
predicted accumulated pull |mu| x steps: median 48.4 ft, max 810 ft
```

The degeneracy control is exact — the term reduces to `l1` to the last decimal when μ=0, so this is not an
implementation error. The damage scales with |μ| at **+0.796** correlation.

**The mechanism: the DP integrates the transition term over the path.** A per-step directional prior of a
fraction of a grid unit compounds over ~477 steps into **tens of feet** of systematic pull — median 48 ft
against a 12 ft RMSE scale. A drift estimate that is *unbiased in the median* is therefore not neutral;
its per-well noise is amplified by path length.

### This is the same failure class as Q13

Q13 recorded that a coverage-masked emission — clearly better pointwise — produced a worse trajectory,
because it applied a **directional pull** that was marginally good per row and cumulatively harmful. Q40's
drift prior is the same mechanism on the transition side, now with a clean degeneracy control and a
quantified predictor.

**Proposed standing rule:** *any per-step directional term in a path DP is multiplied by the path length.
Estimate quality must be judged against the accumulated pull (|estimate| × steps), not against the
per-step magnitude; a near-zero-mean noisy estimate is actively harmful, not neutral.*

## 4. What this closes, and what it does not

**Closes:** the transition-model lever **within the penalty-shape and local-prior family** — L1 vs L2 vs
Huber, a trajectory-derived drift prior, curvature, and the two-parameter L1+curvature combination. The
deployed L1 term is the best of all 45 arms, and no family passes any gate condition. Combined with Q17
(emission lever closed) and Q10/N1's earlier findings, both named levers on the alignment line are now
measured rather than assumed.

**Does not close:** transition models outside this family — a learned or state-dependent transition, or a
per-well adaptive λ tied to a test-available quantity. Those were **not tested** here. Any such attempt
now carries a concrete warning from §3 and must be validated on DP output with the accumulated-pull check.

## 5. No submission, and it would not have been submittable anyway

Two independent reasons, either sufficient:

1. **The gate fails on all three conditions.** Step 5 of the task ("if a candidate passes, prepare a
   smoke-tested Kaggle path") does not trigger.
2. Even had it passed, this line sits at **~12.2** against the deployed honest line's **8.8626** — 37%
   worse. The research gate and the submit gate are different bars, and this artifact clears neither. It
   would also fail the submit gate's "clear information value" requirement as a strictly worse output.

Consistent with Q33: the next 24 h spends **0 slots**.

## 6. Limits

- 40 eval wells, one scorer seed, one emission (TWH=1). The transition conclusions are conditional on that
  emission, though Q17 showed emission quality moves the DP very little in the reachable range.
- The λ grid is {5, 20, 60, 150, 400}; λ=60 is an interior optimum for `l1`, so the baseline is not at a
  grid edge. Other families may have optima outside their grids, but all are far enough behind that a
  grid extension is unlikely to close 2–11 RMSE.
- `μ` uses the median per-row prefix change over the last ≤400 known rows. A different drift estimator
  might be less noisy — but §3 shows the failure is driven by *any* per-step bias being compounded, so a
  better estimator changes the magnitude, not the mechanism.
- Beam width K=6 and BAND=60 are inherited from Q10 and were not varied; they are arguably part of the
  transition model and remain untested.

## 7. Next

Queue continues with `q41_nonhomogeneous_ensemble_search`. `q29_final_slot_candidate_packager` reactivates
**2026-08-03**; the final selection action is due by **2026-08-04** and costs no quota.
