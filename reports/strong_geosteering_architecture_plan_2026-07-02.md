# Strong Geosteering Architecture Plan - 2026-07-02

## Decision

Start a stronger, original ROGII architecture track named
`strong_geosteering_router_v1`.

This track replaces blind public-notebook tuning with a hidden-compatible,
multi-scenario geosteering system:

```text
full train wells
  -> many candidate TVT paths per well and segment
  -> path diagnostics and uncertainty features
  -> group-CV learned router / ranker
  -> low-dimensional residual corrector
  -> audited Kaggle notebook
```

The goal is not to submit another nearby blend. The goal is to produce a model
family that could plausibly move below the public 7.10 plateau by adding new
geological signal.

## Current Baseline And Gap

Latest checked state:

- Team best public score: `7.182`.
- Latest public rank: `166 / 4113`.
- First public score: `5.262`.
- Gap to first: `1.920` RMSE, requiring about `26.7%` lower RMSE or `46.3%`
  lower squared error.
- Today already has two pending team submissions:
  - `54259463`: `singlewell 000d7d20 weighted router alpha0.1 low-corr probe`
  - `54260126`: `singlewell 00e12e8b router alpha0.2 high-impact probe`

Do not spend more official slots on similar singlewell/router probes until those
two scores resolve.

## Research Basis

The task is a TVT sequence reconstruction problem, not ordinary row-wise
regression. Each horizontal well has `MD`, `XYZ`, `GR`, and known-prefix
`TVT_input`; each well also has a paired vertical typewell with `TVT` and `GR`.
The hidden toe-end `TVT` is scored by RMSE.

Public and domain references point to the same family of methods:

- Kaggle public `7.1-7.2` solutions cluster around PF, beam search, NCC/GR
  matching, tree/meta models, and blends.
- Mycarta's ROGII toolkit emphasizes multi-scale NCC against the typewell,
  self-correlation, trajectory/tortuosity, offset-well priors, and landing-zone
  state.
- ROGII/StarSteer geosteering workflow emphasizes multiple interpretations,
  typewell-to-lateral projection, dynamic dip, fault block/throw, and
  multi-scenario steering.
- Particle filters are a natural state-estimation method for geosteering from
  real-time well-log data.
- shapeDTW/DTW-style alignment is relevant because GR signatures can stretch,
  squeeze, and locally misalign rather than shift rigidly.

Key sources:

- Official competition: https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction
- Official data page: https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction/data
- Mycarta ROGII toolkit: https://github.com/mycarta/rogii-geosteering-toolkit
- ROGII StarSteer: https://rogii.com/products/starsteer
- ROGII geological operations: https://rogii.com/solutions/geological-operations
- Public dual-pipeline style: https://www.kaggle.com/code/fleongg/rogii-wellbore-geology-dual-pipeline-lb-7-2
- Public PF/beam stack guide: https://www.kaggle.com/code/afr1ste/rogii-pf-beam-tabicl-stack-guide-9-062
- shapeDTW: https://arxiv.org/abs/1606.01601
- Geosteering with particle filters: https://arxiv.org/abs/2402.06377

## Architecture

### 1. Candidate TVT Path Generator

Generate many complete hidden-zone TVT paths for each pseudo-hidden train split
and for each hidden test well.

Required families for `v1`:

| family | purpose | first implementation |
| --- | --- | --- |
| anchor | protect against catastrophic moves | `last_value`, capped tail slope |
| PF variants | probabilistic typewell-GR state tracking | current PF plus parameter grid |
| constrained NCC | rigid or semi-rigid GR/typewell alignment | multi-window NCC shift paths |
| constrained DTW / beam | local stretch/squeeze alignment | Sakoe-Chiba band, slope and move caps |
| self-correlation | use known lateral prefix motifs | prefix-to-suffix GR motif paths |
| geometry/dip | infer structural trend from trajectory | Z/MD, signed azimuth, curvature |
| offset prior | borrow structure from similar wells | nearest train wells by XY, azimuth, TVT state |
| fault/throw | handle local discontinuities | piecewise jump candidates with penalties |

`v1` should not try a large neural sequence model first. It should build a strong
candidate matrix and router. Neural models can later predict residuals or router
confidence after this framework exists.

### 2. Path Diagnostics

Every candidate path must emit features that a router can use without hidden
truth:

- prefix length, GR coverage, GR variance, missingness;
- known-prefix TVT slope, curvature, recent plateau state;
- candidate TVT range, smoothness, jump rate, move magnitude;
- typewell GR likelihood, NCC score, DTW cost, best shift, shift stability;
- PF posterior spread, ESS/resampling pressure, move confidence;
- self-correlation score, motif location, motif consistency;
- candidate disagreement versus anchor and versus other candidates;
- trajectory features: Z slope, inclination proxy, azimuth, curvature,
  tortuosity;
- offset-neighbor agreement and neighbor uncertainty.

The current matrix already stores several useful features, including move
magnitude. The immediate upgrade is to plumb PF uncertainty diagnostics and
alignment diagnostics into the full-data matrix.

### 3. Learned Router / Ranker

Train on pseudo-hidden suffix splits from full train wells.

Recommended stages:

1. `router_v1`: per-well candidate-family classifier/ranker.
2. `router_v2`: per-segment candidate-family router.
3. `router_v3`: low-dimensional mixture or residual correction.

Model choices:

- First pass: sklearn HistGradientBoosting or RandomForest if local dependencies
  are limited.
- Kaggle pass: LightGBM/CatBoost if available in the notebook runtime.
- Target: candidate win/rank or candidate residual RMSE, not direct row-wise TVT.

Hard gates remain outside the model:

- reject hidden-incompatible features;
- reject out-of-range TVT, extreme jumps, bad GR coverage, unstable shifts;
- fallback to anchor when router confidence is low.

### 4. Residual Corrector

After the router chooses a candidate path, apply only small, structured
corrections:

- constant offset;
- slope/dip correction;
- one optional fault jump;
- smooth basis over MD.

Do not add arbitrary row-wise residuals. This problem rewards stable path shape,
not noisy point fitting.

## Validation Design

Use the full training set, not sample wells.

Splits:

- native `TVT_input` split;
- synthetic prefix fractions: `0.25`, `0.35`, `0.50`, `0.65`, and `0.80` where
  enough hidden rows remain.

Folds:

- GroupKFold by well;
- secondary stratification by prefix fraction, signed azimuth, median TVT,
  hidden-zone length, and spatial cell if available.

Metrics:

- pooled weighted RMSE;
- mean and median per-well delta;
- win rate over anchor;
- catastrophic rate: `delta_rmse > +5`;
- top-worst well table;
- candidate selection counts;
- public-score calibration ledger.

Promotion gate before any official submission:

- beats `last_value` and current router on full-data weighted RMSE;
- catastrophic rate not worse than anchor by more than `0.5%` absolute;
- passes hidden-compatibility source scan;
- output range and shape audit passes;
- differs meaningfully from known 7.182 / 7.153-family outputs;
- answers one named structural question.

## First Implementation Batch

### Q1. Can PF become useful when it exposes uncertainty?

Options:

- add PF posterior std / quantiles / ESS / likelihood score to the matrix;
- sweep PF parameter grid over `sigma_gr`, process noise, fault probability, and
  OU pull;
- train an OOF move+uncertainty gate rather than a single move threshold.

Selected first action:

- implement PF diagnostics and a small OOF router probe.

Success condition:

- full-data OOF RMSE improves at least `0.03` over `last_value` with catastrophic
  rate under `1%`.

### Q2. Does constrained alignment beat rigid shift?

Options:

- multi-window NCC shift paths;
- constrained DTW path with slope/move penalties;
- beam search over TVT state with GR likelihood and anchor penalty.

Selected first action:

- implement a constrained DTW/beam candidate with narrow band and strong anchor
  penalty; emit DTW cost and path smoothness.

Success condition:

- candidate is not necessarily always-on better, but has a high-confidence subset
  where OOF routing improves global RMSE and does not create catastrophic tails.

### Q3. Can offset wells predict hidden drift?

Options:

- nearest wells by XY center;
- nearest wells by signed azimuth and prefix TVT state;
- residual templates from similar train wells.

Selected first action:

- build an offset-prior diagnostic table first, then add path candidates only if
  neighbor agreement is stable.

Success condition:

- neighbor residual agreement predicts candidate win/loss better than prefix
  holdout alone.

### Q4. What is the first official submission candidate?

Do not submit from this architecture until a local candidate clears the promotion
gate. The next official architecture submission should be one of:

- `strong_router_v1_anchor_plus_pf_uncertainty`;
- `strong_router_v1_anchor_plus_constrained_alignment`;
- `strong_router_v1_segment_router`.

If today's two pending singlewell probes score below `7.182`, use them as
negative calibration and keep building. If one beats `7.182`, inspect its largest
well-level moves and fold the signal into this router plan before submitting
another variant.

## Work Order

1. Add PF diagnostic plumbing to `PathCandidate.diagnostics` and
   `full_data_router_matrix.py`.
2. Add an OOF learned diagnostic router script:
   `scripts/strong_router_probe.py`.
3. Add constrained alignment candidate:
   `constrained_typewell_alignment_candidate`.
4. Regenerate full-data matrix on all wells.
5. Compare:
   - `last_value`;
   - current `oof_move_gated_pf`;
   - PF uncertainty router;
   - constrained alignment router;
   - combined PF+alignment router.
6. Write architecture report with candidate deltas and worst wells.
7. Only if the promotion gate passes, package a Kaggle notebook.

## Initial Execution Notes

Completed in this work block:

- Added PF uncertainty diagnostics:
  - `pf_post_std_p90`
  - `pf_post_std_max`
  - `pf_max_abs_dev`
  - `pf_ess_mean`
  - `pf_ess_min`
  - `pf_resample_rate`
- Updated the full-data matrix builder so candidate diagnostics are preserved in
  `experiments/full_data_router_candidate_matrix.csv`.
- Added `scripts/strong_router_probe.py`, a lightweight OOF diagnostic gate
  probe that can test whether a candidate's own diagnostics predict when it
  should replace the anchor.

Smoke / first-pass results:

| matrix | router | result |
| --- | --- | --- |
| existing full matrix, old feature columns | diagnostic-gated PF | `14.6952`, worse than `last_value 14.6844` |
| 20-well smoke matrix with new PF diagnostics | diagnostic-gated PF | `13.1805`, worse than `last_value 13.0955` |
| 10-well smoke matrix with constrained alignment | always-on constrained alignment | `14.6098`, better than `last_value 14.8305`, 0 catastrophic |
| 50-well mid sample with constrained alignment | always-on constrained alignment | `12.5292`, worse than `last_value 12.3982` |
| 50-well mid sample with constrained alignment | OOF diagnostic gate | `12.5225`, worse than `last_value 12.3982` |
| 50-well mid sample with PF | always-on PF | `12.3174`, better than `last_value 12.3982`, but contradicts prior full-data PF result |
| 50-well mid sample with PF | OOF diagnostic gate | `12.5160`, worse than `last_value 12.3982` |

Interpretation:

- The PF diagnostic plumbing works.
- The initial constrained alignment candidate is implemented and hidden-compatible,
  but its default state model does not generalize from 10 to 50 wells.
- The 50-well PF win is not enough to override the prior full-data result where
  PF was worse; subset wins are informative but not submission-grade.
- Do not spend official submissions on PF threshold variants or this first
  constrained-alignment version.
- Next build target: improve alignment from anchor-relative offset DP to a
  segment-aware beam/path model, or add offset-neighbor priors that can predict
  when PF/alignment wins.

## Non-Goals

- Do not train a complex model directly on public leaderboard feedback.
- Do not spend official slots on adjacent blend weights without new structural
  signal.
- Do not use train-only formation columns in submission-time routing.
- Do not static-replay visible test submissions.
- Do not chase first place with a single high-capacity neural model before
  candidate-path validation exists.
