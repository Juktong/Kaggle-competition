# First-Place Architecture Research - 2026-07-01

## Current Situation

Latest checked Kaggle API state:

- leaderboard snapshot: `artifacts/leaderboards/current/rogii-wellbore-geology-prediction-publicleaderboard-2026-07-01T02:53:46.csv`
- team: `lee Marc223`
- members: `joezzzzz, leemarc223`
- current public rank: `148`
- current public score: `7.182`
- first public score: `5.285`
- top-10 cutoff: `6.321`
- top-50 cutoff: `6.986`
- top-100 cutoff: `7.162`

Gap from current `7.182`:

| target | score | RMSE improvement needed | MSE reduction needed |
| --- | ---: | ---: | ---: |
| first | `5.285` | `1.897` | `45.85%` |
| rank 5 | `5.813` | `1.369` | `34.49%` |
| rank 10 | `6.321` | `0.861` | `22.54%` |
| rank 50 | `6.986` | `0.196` | `5.38%` |
| rank 100 | `7.162` | `0.020` | `0.56%` |

Recent official submissions:

| candidate | public score | decision |
| --- | ---: | --- |
| active-account baseline reproduction | `7.182` | trusted current anchor |
| Fleongg branch | `7.787` | weak; do not promote |
| SP45 projection rerun | `7.753` | weak; stop dependent blend sweep |
| Henry/TabICL retry | `13.453` | negative calibration |

Current release gate remains `BLOCKED_STRATEGY_PIVOT`: no official submission should be made until a new structural architecture has stronger local evidence.

## What The Latest Local CV Says

The current pseudo-hidden router CV is useful as a diagnostic harness, but it is not yet a first-place architecture.

| method | weighted RMSE | interpretation |
| --- | ---: | --- |
| `last_value` | `14.7640` | conservative baseline |
| `router_confidence_guarded` | `14.5068` | small safe improvement, mostly by sparse self-correlation / Z gating |
| `piecewise_tail_slope_md` | `14.6828` | local signal, but MD extrapolation is unsafe as a submission rule |
| `piecewise_tail_slope_Z` | `15.1159` | not stable enough |
| `fault_step_recent_level` | `14.8487` | sparse and unstable |

The key result is negative but valuable:

- lightweight dynamic-dip / piecewise / recent-step rules do contain local signal;
- the signal is not stable enough to be the main model;
- the guarded router must reject train-only formation columns and hidden-incompatible features;
- first-place chasing needs a stronger candidate generator plus a learned per-well router, not more nearby blend weights.

## Research Findings

Official/problem sources say this is a well-wise TVT sequence reconstruction problem, not simple row-wise tabular regression. The target is the masked toe-end TVT for horizontal wells, using `MD/X/Y/Z/GR/TVT_input` and paired typewell `TVT/GR`.

Useful public and domain references point to the same architecture family:

- Mycarta's ROGII toolkit describes 773 wells with GR, XYZ trajectory, paired typewell, and masked toe-end TVT, and uses multi-scale NCC, self-correlation, Q-3D tortuosity, trajectory features, offset-well priors, and landing-zone state features.
- ROGII/StarSteer's geosteering workflow emphasizes segmenting, stretching/squeezing, faulting, dynamic dip, target-line projection, multi-typewell steering, and multi-scenario interpretations.
- Public Kaggle search results around stronger notebooks repeatedly mention particle filters, beam search, GR signal alignment, formation plane fitting, ensemble ML, LightGBM/CatBoost, and self-verifying pipelines.
- DTW/shapeDTW literature supports local-shape-aware sequence alignment when standard pointwise matching fails.
- Geosteering state-estimation literature treats particle filters as a natural way to process real-time well-log data and estimate stratigraphic position.

Sources:

- Official competition: https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction
- Competition rules: https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction/rules
- Mycarta ROGII toolkit: https://github.com/mycarta/rogii-geosteering-toolkit
- ROGII geological operations / StarSteer workflow: https://rogii.com/solutions/geological-operations
- Public top-style notebook search result: https://www.kaggle.com/code/saurabhrajvarma/rogii-wellbore-geology-prediction-top-3
- Dual pipeline search result: https://www.kaggle.com/code/lightningv08/rogii-dual-pipeline-self-verifying
- PF/beam/TabICL search result: https://www.kaggle.com/code/afr1ste/rogii-pf-beam-tabicl-stack-guide-9-062
- shapeDTW paper: https://arxiv.org/abs/1606.01601
- Geosteering particle-filter/RL paper: https://arxiv.org/abs/2402.06377

## Architecture Needed To Have A Real Chance

The required pivot is a **multi-scenario geosteering candidate generator plus learned router**, not a single direct TVT model.

### Layer 1: Candidate Path Generator

Generate many complete TVT paths per well and per segment:

1. Conservative anchors
   - `last_value`
   - known PF baseline path
   - simple Z/trajectory projection with strict move caps

2. GR/typewell alignment paths
   - multi-scale NCC over typewell TVT shifts;
   - DTW / shapeDTW path with slope and smoothness constraints;
   - beam-search paths with monotonicity and anchor penalties;
   - GR missingness-aware likelihoods.

3. Particle-filter family
   - multiple process-noise settings;
   - multiple GR likelihood widths;
   - dynamic dip state;
   - optional fault-jump state.

4. Geometry and structure paths
   - local `Z`, inclination, azimuth, curvature, and tortuosity;
   - signed drilling azimuth;
   - lateral-only structural baseline;
   - formation-plane or local plane fitting from neighboring wells where available.

5. Self-correlation paths
   - match hidden-suffix GR against known-prefix GR motifs;
   - use only high-confidence correlation windows;
   - convert matched prefix TVT deltas into suffix path candidates.

6. Offset-well priors
   - nearest wells by XY/azimuth/median TVT;
   - learned residuals from similar wells;
   - uncertainty penalty when spatial neighbors disagree.

### Layer 2: Candidate Diagnostics

For each candidate path, compute router features:

- prefix anchor error;
- prefix holdout RMSE by candidate;
- GR/typewell NCC and DTW cost;
- self-correlation score;
- path smoothness, jump rate, TVT range pressure;
- candidate disagreement;
- GR missingness/noise;
- Z span and within-well TVT-Z decoupling indicators;
- azimuth, curvature, tortuosity, and landing-zone state;
- offset-neighbor agreement.

### Layer 3: Learned Router

Train the router on pseudo-hidden suffix splits from full train data.

Recommended target:

- first version: choose one candidate family per well;
- second version: choose per-segment candidate family;
- third version: predict a low-dimensional mixture or residual correction.

Recommended models:

- LightGBM/CatBoost ranker or classifier over candidate paths;
- group-aware folds by well;
- stratify by prefix length, TVT range, azimuth, and spatial cell;
- use hard gates for hidden-incompatible columns, bad NCC, large jumps, and out-of-range TVT.

Avoid:

- direct high-capacity row-wise TVT regression as the only model;
- training a complex model on public leaderboard scores;
- hidden-test static replay;
- train-only formation columns in submission-time routing.

### Layer 4: Segment-Level Residual Model

After path choice, add a small residual corrector:

- smooth residual over MD, not arbitrary row-wise noise;
- low-dimensional basis: slope, curvature, plateau, fault jump;
- candidate-specific residual models;
- uncertainty cap so the residual cannot destroy a good path.

TCN/sequence models can be explored, but only after the candidate-path framework exists. A TCN that predicts TVT directly is likely brittle; a TCN that predicts residuals, gates, or candidate confidence is safer.

### Layer 5: Validation And Submission Policy

Required local validation before any official submission:

- full train pseudo-hidden suffix CV, not only the three visible sample wells;
- multiple prefix fractions: native, 0.25, 0.35, 0.50, 0.65;
- GroupKFold by well;
- per-well catastrophic-risk table;
- output-distance audit against known good and known bad submissions;
- hidden-compatibility source scan;
- no train-only columns in submission-time decisions.

Public submissions should test structural hypotheses:

- one reference/anchor;
- one new candidate generator;
- one router/gate variant;
- one residual/segment correction;
- one flexible slot only if it answers a different question.

Do not spend slots on adjacent SP45/Fleongg weights while both endpoints are officially weak.

## Direct Answer: What Should We Change?

Change from:

```text
public fork / baseline output
  -> small GR or plateau correction
  -> blend sweep
  -> official submission
```

to:

```text
full train data
  -> candidate-path matrix per well
  -> diagnostics per candidate
  -> learned candidate router
  -> segment residual corrector
  -> hidden-compatible Kaggle notebook
  -> audited structural submission
```

The first concrete build target should be:

1. Download/use full train data locally or run the same job in Kaggle.
2. Build a reusable candidate matrix with at least:
   - current PF/baseline path;
   - last-value path;
   - multi-scale NCC shift path;
   - constrained DTW/beam path;
   - self-correlation path;
   - Z/trajectory projection path;
   - offset-neighbor prior path if full train data is present.
3. Train a LightGBM/CatBoost router to select candidates on pseudo-hidden suffix splits.
4. Only then package one Kaggle notebook candidate.

## Probability Judgment

Current architecture:

- can plausibly improve around top-100/top-50 range if a small structural candidate transfers;
- is not credible for first place by tuning alone.

New architecture:

- could plausibly target top-50/top-10 if candidate generation and routing validate on full train data;
- first place is possible only if we discover a strong alignment/structural signal or a public/private split insight not currently present in this repo.

The next best engineering decision is therefore not another official submission. It is to build the full-data candidate-path matrix and learned router.
