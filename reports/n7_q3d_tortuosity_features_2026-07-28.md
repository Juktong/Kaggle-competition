# N7 — Q-3D wellbore tortuosity as a residual predictor, 2026-07-28

Autopilot task `n7_q3d_tortuosity_features` (`requires_gpu=false`, `can_submit=false`,
`max_submit_cost=0`). Script: `scripts/n7_q3d_tortuosity.py`. Log:
`reports/logs/n7_tortuosity_2026-07-28.log`. No submission; quota untouched at 0/5.

**Result: tortuosity does not predict our honest line's error, at either the well level or the row level.
It fails the task's gate (CV R² 0.0292 against the 0.0736 bar) and the direction is closed.** The smoke
also caught a real implementation defect before any conclusion was drawn.

## 1. Provenance — what was actually implemented

The task specifies implementing from Jing et al. (2022), *"Actual wellbore tortuosity evaluation using a
new quasi-three-dimensional approach"*, Petroleum 8, 118–127. **The paper's full text could not be
retrieved in this environment** — ScienceDirect returns HTTP 403 and a DOI guess resolved to a different
article. Recorded as a constraint rather than worked around silently.

What is implemented follows the principles stated in the paper's abstract — a **Peak-Valley**
decomposition of the trajectory into oscillation segments, and indices incorporating both the **amplitude**
and the **frequency** of fluctuation, computed separately in the inclination and azimuth planes and then
combined — but it is **our implementation of those principles, not a verified reproduction of the paper's
exact equations**. No code was copied from any third-party repository (the MIT-licensed reference
implementation was deliberately not consulted, per the task).

To stop the conclusion hinging on one formula, a **family** of measures is computed: industry-standard
dogleg severity, plane-separated accumulated angular change (`T_incline`, `T_azimuth`), Peak-Valley
amplitude/frequency indices (`Gamma_*`, `freq_*`, `amp_med_*`), the combined `TQG_*` and `TQG_Q3D`. If none
of them predicts our error, the direction closes regardless of which exact index the paper intends.

All inputs are MD/X/Y/Z only, so every quantity is test-available on the full well including the toe.

## 2. The smoke caught a defect — 1 ft differencing measures quantization noise, not geology

The first 40-well smoke produced values that are physically impossible:

```
dls_mean median 49.7 deg/100ft      (real dogleg severity is 0-15)
amp_med_incline 0.5727 deg          (exactly at the 0.5 deg detection threshold)
nseg_incline 2281 over ~4800 ft     (one "oscillation" every ~2 ft)
```

Cause: the data is on a **1 ft MD grid with ~0.01 ft XY resolution**, so a 0.01 ft lateral wobble across a
1 ft step is ≈0.6° of spurious azimuth swing. Differencing at 1 ft measures coordinate quantization.
Real directional surveys are taken every 30–100 ft, so the trajectory is now resampled to `STATION_FT`
before any angle is computed. After the fix the values are physically sane and — importantly — **stable
across the station-spacing sweep**, so the measure is not an artifact of the chosen spacing:

```
STATION_FT      10       30       60      100
dls_mean      1.694    1.511    1.390    1.221     (median over wells, deg/100ft)
dls_p90       3.386    2.979    2.648    2.260
TQG_Q3D       8.506    8.421    7.726    6.419
nseg_incline      9        9        9        9
```

Full split at `STATION_FT=30`, 760 wells: `dls_mean` median 1.569 (p5 0.740, p95 4.124), `dls_max` median
5.52 — a realistic lateral. Median ~12 azimuth-plane and ~9 inclination-plane oscillation segments per
well. No non-finite values.

## 3. Well-level test (the task's specified gate)

Correlation of each index against the banked per-well honest OOF RMSE, 760 wells:

```
feature            pearson   spearman        feature          pearson   spearman
span_ft             0.1182     0.1461        T_azimuth        -0.0643    -0.0758
T_incline           0.0306     0.0344        nseg_azimuth      0.0269     0.0353
nseg_incline        0.0620     0.0929        Gamma_azimuth    -0.0032    -0.0128
Gamma_incline       0.1184     0.1105        freq_azimuth     -0.0771    -0.1021
freq_incline       -0.0196    -0.0128        amp_med_azimuth  -0.0105     0.0100
amp_med_incline     0.0852     0.0954        TQG_azimuth      -0.0567    -0.0599
TQG_incline         0.0445     0.0632        TQG_Q3D          -0.0470    -0.0522
dls_mean           -0.0409    -0.0470        dls_p90          -0.0450    -0.0523
```

Nothing exceeds |0.118|, and the two largest are `span_ft` (well length — not tortuosity, and already
present in N4's set as `toe_md`) and `Gamma_incline`. **The dedicated Q-3D indices are the weakest of
all**: `TQG_Q3D` −0.0470.

The decisive comparison, using N4's exact protocol (5-fold CV, GBM, target = log per-well OOF RMSE):

```
N4 feature set alone          : 0.0736     <- the bar
tortuosity family alone       : 0.0292
N4 + tortuosity               : 0.0765     (+0.0029 over N4 alone)
```

**Fails the gate.** The tortuosity family explains 2.9% of log-RMSE variance against the 7.4% bar, and
adding it to N4's features buys +0.0029 — inside the noise of a 5-fold estimate.

## 4. Row-level test (added, because the well-level test could miss the real usage)

The public repo's reported −0.107 gain is tortuosity as a **per-row feature** inside a LightGBM predicting
TVT, not a per-well summary. A well-level test can miss a row-level signal, so local tortuosity in a
±600 ft MD window around each toe row was correlated against that row's `|residual|` of the deployed
honest line — 584,179 rows over 120 wells:

```
local tortuosity (deg/100ft): p5 1.038  p50 1.896  p95 3.271
ROW-LEVEL pooled      pearson -0.0204   spearman -0.0416
WITHIN-WELL spearman  mean -0.0831  median -0.0964  std 0.3712  |rho|>0.2 in 60.8% of wells
```

Also negative. The within-well spread is the informative part: **60.8% of wells show |ρ| > 0.2, but the
mean is −0.08 with a standard deviation of 0.37** — the relationship exists per well and its *sign flips
between wells*. That is signal that does not transfer, the same failure mode recorded for well-level
features elsewhere in this ledger.

## 5. What this does and does not say

It does **not** refute the public repo's ablation. Two different questions:

- **Theirs:** does tortuosity help a LightGBM *predict TVT* inside their pipeline (reported OOF ~10.5)?
  A feature can help a model interpolate without correlating with a *different* model's residual.
- **Ours:** does tortuosity explain *where our deployed honest line errs*? Measured here: no, at either
  granularity.

Ours is the right question for our decision — whether to spend effort adding it to our stack — and the
task specified exactly this gate. The honest scope of the finding is "no usable signal **for us**".

## 6. Verdict

- Task step 4 resolves to the negative branch: **close the direction and record the measured
  correlation.** Done. The full 760-well computation was run anyway (it is cheap, geometry-only), so the
  closure rests on the complete split rather than the 40-well smoke.
- Retained artifact: `scripts/n7_q3d_tortuosity.py` and the per-well table at
  `rogii_sprint_shared/tmp/n7_tortuosity.csv`, reusable if a future direction needs trajectory-shape
  descriptors.
- Retained caution worth carrying: **any angle computed from this dataset's 1 ft XYZ grid must be
  resampled to a 30 ft+ station spacing first**, or it measures coordinate quantization. This applies to
  any future trajectory feature, not just tortuosity.
- No submission.
