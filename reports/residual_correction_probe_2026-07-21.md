# Residual correction on the deployed honest slot — validation result (2026-07-21)

**Direction 2** of the continuous optimization queue. Status: **no stable improvement observed; gate not met.**

## Question

The deployed honest slot (submission `54844628`, public 7.891, OOF **8.8626**) is

```
base = 0.5*DWT + 0.5*PF
out  = base,  with  out = 0.85*base + 0.15*struct  on gated rows
gate = (well nnb >= 4) AND (well closest_mate < 1000 ft)
```

Is the remaining residual `truth - out` predictable from test-available signals? If yes, a learned
correction term would improve the honest slot without any new data source.

## Setup

- Script: `scripts/residual_correction.py`
  (run copy: `/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/residual_correction.py`)
- Rows: **3,721,471** toe rows over **760** wells; 87.3% gated.
- Reproduces the deployed pipeline exactly: OOF **8.8626** vs reference 8.8626.
- Residual: mean **+0.383**, std **8.854**.

**Feature matrix (3721471, 18) — test-available only.** `row_frac, toe_dist_md, gr_rough, curvature,
gbm_disagree, heel_drift, n_eval, gr_missing, tw_range, z_span, nn_dist (per-row), nnb, closest,
pf_unc, lik_disp, struct_minus_base, dwt_minus_pf, abs_dwt_pf`.

`tw_pressure` was **explicitly excluded** as truth-derived — it is a diagnostic only and would have
been leakage. This is the single most important honesty guard in this probe.

Fitting: nested GroupKFold by well (5 folds), then the applied correction is further scaled by a
**nested shrinkage scalar** fit on half the wells and applied to the other half (3 seeds), so the
strength of the correction is never chosen with knowledge of the rows it is applied to.

## Result

| model | corr(pred_resid, resid) OOF | nested result | gain vs deployed |
|---|---|---|---|
| Ridge | **−0.0919** | 8.8626 | **+0.0000** |
| Huber | **−0.0679** | 8.8679 | −0.0052 |
| HistGradientBoosting | **+0.0811** | 8.9156 | −0.0530 |

Fixed-λ sweep for HGB (the only model with positive correlation):

```
lam=0.25: 8.8313  gain +0.0314
lam=0.50: 8.8825  gain -0.0199
lam=0.75: 9.0149  gain -0.1523
lam=1.00: 9.2251  gain -0.3624
NESTED shrinkage : 8.9156  gain -0.0530
```

```
BEST: ridge -> 8.8626 (gain +0.0000 vs deployed 8.8626)
bootstrap(200 wells): mean=+0.0000 5th=+0.0000 frac>0=0%
GATE (>= +0.10 with stably positive bootstrap): DOES NOT MEET
```

## Interpretation

1. **The linear models anti-correlate out-of-fold** (−0.09, −0.07). They are not merely uninformative;
   they fit in-fold residual structure that reverses on held-out wells. The nested shrinkage scalar
   correctly collapsed Ridge's coefficient to zero, which is why Ridge lands exactly on the deployed
   score — the honest procedure recognised that no correction was the best correction.
2. **The HGB +0.031 at λ=0.25 is a fixed-λ artifact, not a gain.** λ was chosen by reading the sweep,
   i.e. with knowledge of the full-data outcome. When λ is instead fit honestly on held-out wells the
   result is **−0.053**. This is exactly the kind of number that would have looked like a +0.03
   improvement had the sweep been reported without the nested column, and it is worth recording as a
   procedural warning: *a λ sweep is not a validation.*
3. A residual correlation of +0.08 is far below the transfer-noise threshold (~0.02 on the RMSE scale
   is already marginal); it does not carry a usable correction.

The mechanism is that the deployed pipeline has **already consumed** what these features predict —
`gbm_disagree`, `pf_unc`, `nn_dist`, `nnb`/`closest` are the very signals the DWT ensemble, the PF
forward model and the structural gate are built on. Re-reading them at the residual stage finds
leftovers that are noise with respect to test-available information.

## Reproduction

```bash
cd /home/ubuntu/workstation/JoeProject/Kaggle-competition
FOLDS=5 SUB=4 python3 scripts/residual_correction.py
```
Required artifacts (stable shared dir `/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/`):
`decomp_features.npz`, `struct_oof_rowdist.npz`, `pf_unc.npz`.

## Disposition

Direction 2 is closed as a negative. It is **not** evidence that the honest slot is at its limit —
only that *post-hoc correction using signals the pipeline already uses* does not transfer. See
`reports/autonomous_backlog_status_2026-07-21.md` for the shared mechanism across directions 2/3/4
and the resulting reprioritisation toward genuinely decorrelated information sources.
