# N4 — calibrated per-well uncertainty (split conformal on the banked OOF), 2026-07-28

Autopilot task `n4_conformal_well_uncertainty` (`requires_gpu=false`, `can_submit=false`,
`max_submit_cost=0`). No model was refitted. Script: `scripts/n4_conformal_well_uncertainty.py`
(CPU, ~2 min). Log: `reports/logs/n4_conformal_2026-07-28.log`.

**Headline: the conditional part is a negative result, and it closes the per-well confidence-gating
axis.** The *marginal* conformal bound is valid and is retained as a usable artifact, and two
by-products — the 3-well draw distribution and a measured OOF→leaderboard transfer ratio — are the round's
most decision-relevant output.

## Setup

- Source: `aligned_preds.npz`, column `s_54844628` (the deployed honest candidate, public 7.891).
  Toe-only rows, **760 wells, 3,721,471 rows**, pooled OOF RMSE **8.8626** — reproduces the banked figure
  exactly, confirming the right artifact was loaded.
- Conditioning features are **test-available only**: `nnb`, closest surviving mate distance,
  prefix fraction, toe MD length, prefix MD length, well MD length, GR std (full and toe), mean
  inclination, tortuosity. No structural surface, no `Geology`, no truth.
- **Splits are by well, never by row.** Lag-1 residual autocorrelation within a well is +0.9998, so a
  row-level split would leak and report meaningless coverage. 380 calibration / 380 validation wells.

## A. Marginal split conformal — valid, and retained

| nominal | width (ft) | empirical coverage on held-out wells |
|---|---|---|
| 0.80 | 9.986 | 0.853 |
| 0.90 | 13.431 | 0.942 |
| 0.95 | 17.530 | 0.966 |

Coverage is at or slightly above nominal at every level — the expected mildly conservative behaviour of
split conformal at this sample size. **Usable statement: for the deployed honest line, 90% of wells have
a per-well RMSE at or below 13.43 ft and 95% at or below 17.53 ft**, distribution-free.

## B/C. Conditional (Mondrian) conformal — no usable per-well information

Feature association with per-well OOF RMSE is weak across the board:

```
feature           pearson  spearman
nnb               -0.1528   -0.1722      <- strongest
well_md            0.1217    0.1484
toe_md             0.1183    0.1458
closest_surv       0.1082    0.1448
prefix_frac       -0.1163   -0.1192
gr_std_toe         0.1383    0.0972
mean_incl         -0.0391   -0.0432
tortuosity        -0.0283   -0.0140
```

Binning on the strongest features does move the interval, but only slightly — width separation across
4 bins is **1.28×–1.61×** (best: `closest_surv` 1.612×, `nnb` 1.533×), while the true per-well RMSE
spans **8.56×** from median to max. Coverage stays valid inside every bin (0.878–0.966 at nominal 0.90),
so the intervals are honest; they are simply not informative.

The decisive check is efficiency — a conditional interval only earns its keep if it is **narrower on
average** at the same coverage:

```
scheme                        avg_width   coverage
marginal (unconditional)         13.431      0.942
mondrian on closest_surv         13.758      0.921
mondrian on nnb                  13.966      0.945
```

**Conditioning costs width rather than saving it.** Cross-validated confirmation on the same features:

```
5-fold CV R^2 predicting log(per-well OOF RMSE): 0.0736
spearman(predicted, actual per-well RMSE):        0.2457
```

7.4% of log-RMSE variance is not a usable per-well signal.

**Consequence for the queue.** The variant-matrix round flagged *per-well confidence gating* as an axis
the frontier never exposes. This measurement shows that axis has **no usable input from test-available
features**: a gate built on them would be close to random, and any per-well interval built on them is
wider than simply using the fleet-wide bound. The axis is closed unless a materially different feature
source appears. This mirrors the closed anti-harm guard (AUC 0.53) — the failure is not the choice of
target but the absence of per-well signal in the available covariates.

## D. Where the 3 visible test wells sit

| well | per-well OOF RMSE | fleet percentile | nnb | closest surv. mate | prefix frac | toe MD |
|---|---|---|---|---|---|---|
| `000d7d20` | 3.622 | 0.264 | 13 | 291.7 | 0.273 | 3836 |
| `00bbac68` | 5.066 | 0.480 | 40 | 343.6 | 0.204 | 6014 |
| `00e12e8b` | 5.181 | 0.499 | 13 | 354.5 | 0.326 | 4301 |

Fleet: median 5.181, p90 12.138, max 44.375. **All three test wells are at or below the fleet median** —
the visible test set is an easier-than-typical draw for the honest line, not a hard one. No test-available
red flag, consistent with the earlier audit.

## E. Two by-products that carry more decision value than the intervals

### E1. The 3-well scoring scale, measured on the error level

Per-well OOF RMSE is heavy-tailed (p50 5.181, p75 8.337, p90 12.138, p99 29.867, max 44.375). Drawing 3
wells at random and pooling row-weighted the way the leaderboard does, **for one fixed model**:

```
5th 3.491   25th 5.040   median 6.708   75th 8.990   95th 15.138   99th 25.374
```

A single fixed model's own score spans **3.49 to 15.14** across 3-well draws. This is an independent
corroboration of the project's 3-well gate doctrine, and a new one: the doctrine was previously derived
from the variance of per-well *gains*; this measures the variance of the error *level*. It is the
quantitative reason a ~0.1 margin cannot be validated at this scale.

The actual 3 test wells pool to **4.756** (train-copy OOF), at percentile **0.207** of that distribution.

### E2. Conformal on OOF does not bound the leaderboard — measured

```
OOF on the 3 test wells 4.756  vs public 7.891  ->  ratio 1.659
```

The conformal machinery calibrates the **fleet distribution of OOF error**. It does **not** calibrate the
OOF→leaderboard transfer, and the measured 1.659× gap on exactly the scored wells is direct evidence that
the transfer carries its own bias. Consequence: the marginal bound in section A is a statement about
train-masked OOF and must not be reported as a bound on the private score. This bounds how much N4 can
contribute to slot selection, and is recorded so the interval is not over-read later.

## Verdict

- **Negative on the task's primary question.** Per-well interval width does vary across bins (1.3–1.6×)
  but carries no usable information: CV R² 0.074, and the conditional intervals are wider than the
  unconditional one at matched coverage. Per-well confidence gating is closed on these features.
- **Retained artifacts.** The marginal conformal bound (90% ≤ 13.43 ft, 95% ≤ 17.53 ft, coverage
  verified out-of-sample) and the per-well uncertainty table at
  `/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/n4_well_uncertainty.csv`.
- **Most valuable output.** The 3-well draw distribution (5th 3.49 → 95th 15.14 for a fixed model) and
  the measured 1.659× OOF→public transfer gap.
- No submission (`can_submit=false`); quota untouched at 0/5. Slot recommendation unchanged.
