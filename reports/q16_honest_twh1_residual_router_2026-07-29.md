# Q16 — honest residual router on the deployed line: CLOSED on its prerequisite

Date: 2026-07-29
Task: `q16_honest_twh1_residual_router`
Script: `scripts/q16_residual_predictability.py`
Log: `reports/logs/q16_residual_pred_2026-07-29.log`
Outcome: **CLOSED — no submission, no quota spent.**

## What Q16 proposed and why it was tested this way

Q16 proposed a *bounded residual correction* on the deployed honest line (`54844628`), gated on a
confidence signal. That construction has one load-bearing prerequisite: the **signed** row-level
residual must be predictable from test-available features **on wells the model has not seen**. If it is
not, no gating scheme can rescue it, because there is nothing to route.

Two pieces of banked evidence bore on this and neither settled it:

- the ledger already lists post-hoc residual correction as CLOSED, but on an older feature set;
- N4 measured predictability of the error **magnitude** per well (CV R² 0.0736 on log per-well RMSE)
  and found conditional conformal intervals *wider* than marginal ones. Magnitude is a strictly weaker
  requirement than sign, so N4 bounded this from one side only.

So the prerequisite was measured directly before building any router — the cheapest possible resolution
of the direction. Features are test-available only: neighbour diagnostics from the structural field
(`nnb`, `closest_all`, `closest_surv`), the DWT/PF disagreement, the struct contribution actually
applied, row position within the toe (`row_frac`, `rows_from_anchor`), and the per-well features banked
by N4. 15 features, 3,721,471 rows, 760 wells, `GroupKFold(5)` **split by well**.

## Result — the prerequisite fails

Deployed line signed residual: mean **−0.3832 ft**, std 8.8544, RMSE **8.8626**.

```
=== signed-residual predictability, GroupKFold BY WELL ===
  CV R^2                : -0.0802
  corr(pred, actual)    : 0.0721
  N4 reference (magnitude, log per-well RMSE): 0.0736
```

**CV R² is negative.** The model does not merely fail to predict the held-out signed residual; the
per-row structure it fits on training wells *anti-transfers* to held-out wells, doing worse than
predicting the constant mean. Correlation is 0.0721 — nominally positive, but that is the entire
signal.

Applying the correction at a range of strengths:

```
  correction strength                    pooled  vs deployed
  resid - 0 * predicted                  8.8626       0.0000
  resid - 0.25 * predicted               8.8379      +0.0247
  resid - 0.5 * predicted                8.8874      -0.0248
  resid - 1 * predicted                  9.2024      -0.3398
```

The profile is **non-monotonic** — it peaks at strength 0.25 and is already negative by 0.5. That shape
is the signature of a near-zero signal being fitted against noise: heavy shrinkage extracts a sliver,
and anything past that injects more error than it removes. The full-strength correction costs 0.34 ft.

### The apparent gain is mostly, but not entirely, a constant

Because the residual carries a global mean bias of −0.3832 ft, a correction can appear to help simply by
removing that constant. Isolating it with an out-of-fold **constant-only** correction (subtract the
train-fold mean, no model):

```
constant-only, strength 0.25  : 8.8598   gain +0.0028
constant-only, strength 0.5   : 8.8581   gain +0.0046
constant-only, strength 1     : 8.8578   gain +0.0048
```

So of the +0.0247 at strength 0.25, about +0.005 is the global constant and roughly **+0.020 ft is
genuine per-row signal** — 0.23% of an 8.86 ft RMSE. It is real and it is negligible.

### At competition scale it is indistinguishable from noise

```
  per-well gain at strength 0.5: mean -0.0034 median +0.0011 | helped 50.4% hurt 49.6%
  3-WELL bootstrap: 5th -0.9333  50th +0.0072  95th +0.8933  P(gain>0) 0.5078
```

Per-well it is a coin flip: 50.4% helped, 49.6% hurt, mean gain −0.0034. The 3-well bootstrap — the
gate that matters, since the competition scores 3 wells — spans **−0.93 to +0.89 ft** around a median of
+0.007, with P(gain > 0) = 0.5078. The ±0.9 ft sampling spread at 3-well scale is roughly **40× the
+0.02 ft effect**.

### Gate verdict

The script's stated gate: *a materially positive signed-residual R² **AND** a 3-well bootstrap 5th
percentile > 0.*

| condition | required | observed | verdict |
|---|---|---|---|
| signed-residual CV R² | materially positive | **−0.0802** | FAIL |
| 3-well bootstrap 5th pct | > 0 | **−0.9333** | FAIL |

Both fail. **Q16 closes on its prerequisite without the router being built.**

## What this adds to the ledger

- It **completes** the bound N4 left open. N4 showed error *magnitude* is weakly predictable
  (R² 0.0736); Q16 shows the *sign* is not predictable at all (R² −0.0802) on the same well-split
  protocol. Magnitude-without-sign cannot drive a correction — you can know a row is likely wrong and
  still have no information about which way to move it. This is why the conditional conformal intervals
  in N4 came out wider than marginal ones, and the two results are now consistent under one explanation.
- It **generalises** the older post-hoc-residual-correction closure from a specific feature set to the
  full test-available feature set currently in hand, including the N4 per-well uncertainty features.
- It is consistent with **Rule #1** (averaging/shrinkage transfers; fitted per-row structure does not):
  the only positive-gain regime here is heavy shrinkage toward zero, and the negative R² is fitted
  structure failing to cross the well boundary.

## Negative results and limits, stated plainly

- The +0.020 ft per-row component is a genuine non-zero effect, not exactly zero. The closure is on
  *magnitude and reliability*, not on the existence of signal.
- The learner is `HistGradientBoostingRegressor`, not the exact-split `GradientBoostingRegressor`
  originally written. Reason recorded below. A different model family (or a much richer feature set)
  is not excluded by this measurement, but it would have to overcome a **negative** transfer R², not a
  small positive one.
- The measurement is on the 760-well train pool. Per the standing 3-well-scale rule, its relevance to
  the competition is expressed through the 3-well bootstrap above, which is the binding statistic.

## Method / operational facts worth carrying

1. **Exact-split GBM is not viable at this row count.** `GradientBoostingRegressor` is single-threaded;
   5 folds × 300 trees on 3.7M rows exceeded a 3000 s cap once and was on track to exceed a 2400 s cap
   again. `HistGradientBoostingRegressor` fits the **full 3.7M rows** multithreaded in about a minute.
   The switch improved the science as well as the cost: no subsampling was needed, so the estimate uses
   every row rather than a 300k sample.
2. **Redirect Python with `-u`.** The first two attempts wrote to a log that stayed at 0 bytes for
   20 minutes and read as hung; stdout was block-buffered to the file. `python3 -u ... | tee` streams.
3. **Verify a PID before killing it.** `pgrep -f "<pattern>" | head -1` returned a transient PID
   (312935) that was not the run (312966); the first kill therefore did nothing. Confirm with
   `ps -o pid,cmd -p <pid>` first. Related: a waiter whose own command line contains the pattern it
   greps for never exits — the self-match bug, hit again this round.
4. **The `kaggle` package was missing from the environment this round** and was reinstalled with
   `python3 -m pip install --user --break-system-packages kaggle` (PEP 668 environment). Note the API
   returns **snake_case** attributes: `s.public_score`, `s.private_score` — not `publicScore`.

## Submission 55064411 — still pending

Re-checked this round: `55064411` (Q14 hedge-OFF, kernel `joezzzzz/rogii-frontier-hedgeoff-full` v1)
remains **`SubmissionStatus.PENDING`**, now **2 h 20 m+** after the 2026-07-28 20:30 UTC submission.
That is past the ~1 h kernel-runtime expectation recorded in commit `41bb65f`, though the recorded rule
still holds that PENDING is not itself a failure in a kernels-only competition. No resubmission was made
and no quota was spent this round. Quota remains **1/5 used** for the day.

Scored reference points for when it lands: 54922806 **6.563** (best), 54968060 6.643, 54896975 6.669,
54923144 6.678, 54990075 6.690. The recorded next action stands: record the score in the ledger and the
final-slot package, and if it is ≤ 6.563 re-evaluate slot 1 on provenance (own account vs teammate).

## Next

`q17_kaggle_gpu_tiny_training_followup`. `q15_frontier_dependency_replacement` remains not-started — it
needs its own frontier full run, which the standing rules forbid overlapping with one in flight, and
55064411's kernel re-run is still in flight.
