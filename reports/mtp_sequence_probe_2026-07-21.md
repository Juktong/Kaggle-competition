# Sequence / MTP / MDN headroom diagnostic (2026-07-21)

**Direction 6** of the continuous optimization queue. Status: **headroom measured and found small;
no sequence model built this round.** Script: `scripts/seq_headroom.py`.

This probe produced the structural explanation for why directions 2, 3 and 4 all returned negatives, so
it is the most load-bearing result of the queue even though it is itself a negative.

## Approach

A sequence / multi-token-prediction / mixture-density model can only help if the deployed prediction
leaves *sequence structure* unexploited. Rather than build one and measure afterwards, three cheap
measurements were taken first (the same protocol that paid off in direction 5):

1. residual autocorrelation along the toe row index
2. whether **nested-fit** smoothing of the prediction along MD reduces RMSE (bandwidth chosen on
   held-out wells, so the bandwidth is never selected using the rows it is applied to)
3. whether the residual is multi-modal / heavy-tailed enough for a mixture head to pay off

Base: deployed honest slot `54844628`, 760 wells, 3,721,471 rows, OOF **8.8626**.

## Result

**1) Residual autocorrelation along the trajectory**

```
lag     1: +0.9998
lag     5: +0.9991
lag    20: +0.9942
lag   100: +0.9497
lag   500: +0.6365
lag  2000: -0.0409
```

**2) Nested-fit smoothing along MD**

```
k=    1: 8.8626  +0.0000
k=    5: 8.8623  +0.0004
k=   15: 8.8613  +0.0013
k=   51: 8.8567  +0.0059
k=  151: 8.8466  +0.0160
k=  501: 8.8800  -0.0173
k= 1501: 9.3194  -0.4567
NESTED bandwidth selection: 8.8466   gain +0.0160
```

**3) Residual shape**

```
mean=+0.383 std=8.854 skew=+0.223 kurtosis=+9.172
|r|<1ft 18.1%   |r|>10ft 16.4%   |r|>25ft 2.2%
GMM k=1: BIC=1438494
GMM k=2: BIC=1376501   means=[1.59, 0.08]  weights=[0.214, 0.786]
GMM k=3: BIC=1376913   means=[0.11, -5.47, 8.50]  weights=[0.718, 0.149, 0.133]
```

## Interpretation — this explains directions 2, 3 and 4

An autocorrelation of **0.9998 at lag 1**, still 0.95 at lag 100, says the remaining error contains
**essentially no high-frequency component**. The error is not row-level noise; it is a **smooth,
slowly-varying, per-well bias** that drifts over roughly 500–2000 rows (autocorrelation reaches zero at
lag ≈ 2000).

That single fact accounts for the whole pattern of negatives in this queue:

- **Smoothing cannot help** (direction 6): there is no white noise to average away. Nested smoothing
  gains only **+0.0160** — at or below the ~0.02 transfer-noise threshold, so it is not distinguishable
  from noise and is far below the +0.10 gate.
- **Post-hoc residual correction cannot help** (direction 2): a smooth per-well bias would have to be
  predicted from test-available features, and it is not — the models anti-correlated out-of-fold.
- **Group calibration cannot help** (direction 3): the bias is per *well*, not per group, and the
  structural field already removes the per-well level via its own heel anchor.
- **Routing cannot help** (direction 4): a smooth bias shifts all candidates in the same direction, so
  no candidate is systematically right on an identifiable family of rows — hence the near-uniform
  38/31/31 oracle mix.

The residual behaves like the well's own unknown structural deviation from the field model: coherent
along the wellbore, different for each well, and — on the evidence of directions 2–4 — not recoverable
from any signal available at test time.

**Multi-modality does exist** but does not convert to RMSE. GMM k=2 clearly beats k=1 on BIC
(1,376,501 vs 1,438,494): a 78.6% core component tight around zero plus a 21.4% wider component, with
kurtosis +9.17. k=3 does not improve on k=2. A mixture-density head would therefore model the
*uncertainty* better — but under RMSE the optimal point estimate is the conditional mean, which
averaging already provides, and using the extra spread information for routing/selection has now been
refuted twice (direction 4 here, and the earlier single-variable PF-uncertainty probe).

## Decision

No sequence/MTP/MDN model is built this round. The measured headroom for the mechanisms such a model
would supply — smoothing (+0.016) and density shape (no RMSE path) — does not approach the +0.10 gate,
and the diagnostic cost was ~7 minutes against what would have been a multi-day build.

## What would reopen this line

Evidence that the smooth per-well bias is recoverable from information we are not currently using. The
bias has a ~500–2000-row coherence length, which is the scale of a structural feature (a fault block or
a dip change), so a model with access to a genuinely new source of cross-well structural information
could in principle track it. That is the same conclusion the rest of the queue points to, and it is why
remaining effort is directed at decorrelated information sources rather than at post-processing.

## Reproduction

```bash
cd /home/ubuntu/workstation/JoeProject/Kaggle-competition
python3 scripts/seq_headroom.py
```
Artifacts: `decomp_features.npz`, `struct_oof_rowdist.npz` in
`/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/`; log
`reports/logs/seq_headroom_2026-07-21.log`.
