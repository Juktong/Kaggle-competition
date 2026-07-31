# Architecture Gap Review - 2026-07-01

## Current State

Source snapshot:

- Kaggle API submission sync: `2026-07-01 02:15 UTC`
- Kaggle public leaderboard: `artifacts/leaderboards/rogii-wellbore-geology-prediction-2026-07-01T0215Z/rogii-wellbore-geology-prediction-publicleaderboard-2026-07-01T02:15:44.csv`
- Official competition page: https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction
- Leaderboard page: https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction/leaderboard

Current official calibration:

| candidate | submission | public score | interpretation |
| --- | ---: | ---: | --- |
| active-account baseline reproduction | `54174151` | `7.182` | current trusted anchor |
| Fleongg learned branch | `54174876` | `7.787` | weak; do not promote raw learned branch |
| SP45 projection dynamic rerun | `54198676` | `7.753` | weak; do not spend more slots on dependent SP45 blend sweep |
| Henry/TabICL retry | `54162612` | `13.453` | negative calibration |

Planning state after refresh:

| item | value |
| --- | --- |
| pending official submissions | `0` |
| running kernels | `0` |
| batch status | `NEEDS_NEW_ARCHITECTURE_CANDIDATES` |
| release gate | `BLOCKED_STRATEGY_PIVOT=5` |
| validation errors | `0` |

The automation has been updated so weak SP45/Fleongg official scores block the old planned batch. Current planned slots are tracked for evidence, but all are gated by `build_new_architecture_first`.

## Leaderboard Gap

| target | public score | absolute RMSE gap from `7.182` | MSE reduction needed |
| --- | ---: | ---: | ---: |
| first place | `5.285` | `1.897` | `45.85%` |
| rank 2 | `5.444` | `1.738` | `42.54%` |
| rank 10 | `6.321` | `0.861` | `22.54%` |
| rank 50 | `6.986` | `0.196` | `5.38%` |
| rank 100 | `7.159` | `0.023` | `0.64%` |

Interpretation:

- A top-100 move may come from better reproduction or small low-risk correction.
- A top-50 move is plausible with a useful structural candidate.
- A top-10 move needs a real architecture improvement.
- First place is not plausibly reachable by blend weights, smoothing constants, or minor parameter tuning alone.

## Research Notes

Task interpretation:

- The target is `TVT` for the masked toe-end of each horizontal well, not a generic row-wise label.
- Each well has a horizontal `MD/X/Y/Z/GR/TVT_input` sequence and a paired vertical typewell with `TVT/GR`.
- External notes describe the problem as 773 horizontal wells with GR, trajectory, paired typewell, and masked toe-end TVT prediction.
- Relevant source: https://github.com/vamseeachanta/kaggle-rogii-2026/blob/main/docs/task-brief.md

Domain geosteering sources emphasize:

- correlate lateral gamma to one or more typewells;
- segment the well;
- stretch/squeeze correlations;
- handle faults, dynamic dip, target-line/trajectory projection, and multi-scenario interpretations.
- Relevant source: https://rogii.com/solutions/geological-operations

Public ROGII code/research cluster:

- Public notebooks around the `7.1-7.2` band mostly combine PF, beam search, NCC/GR matching, ridge/tree models, and blends.
- Degnonguidi/Baidalin/Pilkwang/Romantamrazov/Shinyanagai style notebooks are useful architecture references, but public material does not reveal the first-place `5.285` method.
- Mycarta's toolkit frames useful features as multi-scale NCC, self-correlation, trajectory/tortuosity, offset-well priors, landing-zone state, and group-aware validation.
- Relevant sources:
  - https://github.com/mycarta/rogii-geosteering-toolkit
  - https://www.kaggle.com/code/degnonguidi/public-score-rogii-lb-7-159
  - https://www.kaggle.com/code/baidalinadilzhan/rogii-lb-7-201
  - https://www.kaggle.com/code/pilkwang/rogii-target-free-tvt-geosteering
  - https://www.kaggle.com/code/romantamrazov/rogii-super-solution-lb-top-3
  - https://www.kaggle.com/code/shinyanagai123/triple-signal-beam-search-dual-pf-lightgbm

## Why The Current Architecture Is Not Enough

Current architecture families:

- baseline physics/PF stack around `7.18`;
- SP45 projection branch, now officially `7.753`;
- Fleongg learned branch, now officially `7.787`;
- SP45+Fleongg blend sweep, now low-value because both endpoints are weak;
- GR/typewell light corrections, locally plausible but low-upside;
- plateau quantile rule, locally sparse and single-well dominated.

Failure pattern:

- The best active baseline is still in the public `7.1` band.
- Independent branches we hoped would add signal instead scored worse.
- Local pseudo-test CV shows simple plateau rules only narrowly beat `last_value`, with high fallback.
- Linear/drift-only strategies can be catastrophically unstable.

Conclusion: the current system is useful for audited submission discipline, but the model family is not strong enough to chase first place. It lacks a per-well mechanism for selecting among competing geological interpretations.

## Required Architecture Pivot

Build a multi-hypothesis geosteering router.

Layer 1: Candidate path generator per well.

- stable hold/last-value and PF baseline;
- multiple PF variants with different process noise and GR likelihoods;
- beam-search variants with smoothness and anchor constraints;
- DTW/NCC typewell alignment paths at multiple scales/lags;
- self-correlation paths using the known lateral prefix;
- geometry/trajectory paths using `Z`, signed azimuth, curvature, tortuosity, and inferred dip;
- offset-well or nearest-neighbor structural priors;
- fault/throw or piecewise-affine correction candidates.

Layer 2: Diagnostic features.

- prefix length and prefix TVT slope/curvature;
- known-prefix anchor consistency;
- GR missingness/noise and local variance;
- typewell NCC/DTW scores at multiple windows;
- self-NCC scores between known lateral and predicted suffix;
- candidate disagreement and uncertainty;
- trajectory `Z/MD`, signed azimuth, Q-3D tortuosity;
- typewell range pressure and formation-state/landing-zone features;
- offset-neighbor structural residuals.

Layer 3: Router/gate.

- choose candidate family per well or per segment;
- do not directly fit high-complexity row-wise TVT from public leaderboard feedback;
- train router on pseudo-hidden suffix splits with GroupKFold/stratified GroupKFold;
- target candidate choice, residual drift, or low-dimensional mixture weights;
- use hard safety gates for missing GR, bad NCC, range violation, and catastrophic slope.

Layer 4: Segment correction.

- piecewise affine TVT correction;
- dynamic dip per segment;
- stretch/squeeze of typewell-to-lateral mapping;
- optional fault jump/throw candidate;
- smoothing only after path choice, not as the main model.

Layer 5: Validation and submission.

- hide suffixes from train wells at multiple prefix fractions;
- score both global RMSE and per-well catastrophic tail risk;
- compare router decisions against individual candidate families;
- official submissions should test structural hypotheses, not adjacent blend weights;
- public score can calibrate the validation framework, but should not train a complex public-LB model.

## Immediate Next Questions

1. Which path-generator families can we implement first without pulling in fragile private artifacts?
   - Recommended first batch: PF variants, NCC/DTW alignment, self-correlation, and piecewise-affine correction.

2. What is the router target?
   - Recommended: per-well candidate-family selection plus optional residual drift, not direct row-wise TVT.

3. What local validation split best predicts public score?
   - Recommended: multiple hidden suffix splits per train well, grouped by well, stratified by prefix length/azimuth/TVT range.

4. What should be submitted next?
   - Not the old SP45/Fleongg blend batch.
   - Submit only after a new router candidate beats baseline families in pseudo-hidden validation and passes the existing audit/release gate.

## Decision

Set the project direction to `multi_hypothesis_geosteering_router`.

The next engineering batch should build the candidate-path matrix and router validation harness. Current low-upside GR/plateau candidates may remain as tracked information slots, but they should not be treated as a credible path to first place.
