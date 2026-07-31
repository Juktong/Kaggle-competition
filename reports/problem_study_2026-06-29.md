# ROGII Problem Study - 2026-06-29

This note summarizes the ROGII Wellbore Geology Prediction competition from the official Kaggle pages, the checked sample files, and the current project history.

## 1. Competition Objective

The task is to predict `TVT` (True Vertical Thickness) for the evaluation zone of each horizontal well.

Each well has:

- a horizontal well trajectory with measured depth and spatial coordinates;
- gamma ray (`GR`) measurements along the horizontal well, with gaps;
- a `TVT_input` prefix, where the known portion is provided and the evaluation zone is hidden;
- an associated vertical reference log, called a typewell, with `TVT` and `GR`.

The problem is best understood as sequence reconstruction / geological alignment, not ordinary row-wise regression. For each well, the model has to extend the known `TVT_input` prefix through a hidden lateral interval while staying consistent with the well path, gamma-ray signal, and typewell signature.

## 2. Official Data Layout

Official train files:

- `train/{WELL}__horizontal_well.csv`
- `train/{WELL}__typewell.csv`
- `train/{WELL}.png`

Official test files:

- `test/{WELL}__horizontal_well.csv`
- `test/{WELL}__typewell.csv`

Submission file:

- `sample_submission.csv`

Important hidden-test behavior: the visible `test/` directory only contains a few example instances from the training set. During official notebook rerun, Kaggle replaces these with the actual hidden test wells. This means static public-output replay is invalid; notebooks must dynamically discover and process whatever wells are present under `/kaggle/input/rogii-wellbore-geology-prediction/test`.

## 3. Columns

Training horizontal well columns:

- `MD`: measured depth
- `X`, `Y`, `Z`: spatial coordinates
- `ANCC`, `ASTNU`, `ASTNL`, `EGFDU`, `EGFDL`, `BUDA`: formation surface depths, training only
- `TVT`: true target, training only
- `GR`: gamma ray
- `TVT_input`: provided target prefix, with `NaN` in the evaluation zone

Test horizontal well columns:

- `MD`
- `X`, `Y`, `Z`
- `GR`
- `TVT_input`

Training typewell columns:

- `TVT`
- `GR`
- `Geology`

Test typewell columns:

- `TVT`
- `GR`

## 4. Checked Visible Sample Structure

Downloaded sample files under `data/sample/` for the three visible test wells:

- `000d7d20`
- `00bbac68`
- `00e12e8b`

`sample_submission.csv` contains `14,151` prediction rows across these 3 wells:

| well | test rows | known prefix rows | eval rows | first eval idx | last eval idx | submission rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `000d7d20` | 5,278 | 1,442 | 3,836 | 1,442 | 5,277 | 3,836 |
| `00bbac68` | 7,559 | 1,545 | 6,014 | 1,545 | 7,558 | 6,014 |
| `00e12e8b` | 6,384 | 2,083 | 4,301 | 2,083 | 6,383 | 4,301 |

Submission IDs use:

```text
{WELL}_{row_index}
```

For example, `000d7d20_1442` means well `000d7d20`, row index `1442` in that well's horizontal CSV.

Observed missingness in visible test horizontal files:

| well | missing `GR` | missing `TVT_input` |
| --- | ---: | ---: |
| `000d7d20` | 2,258 | 3,836 |
| `00bbac68` | 942 | 6,014 |
| `00e12e8b` | 584 | 4,301 |

Implication: a strong solution cannot rely only on `GR`; it must tolerate missing logs and use path geometry, prefix continuity, typewell correlation, and physical constraints.

## 5. Scoring

Kaggle scores submissions using RMSE:

```text
RMSE = sqrt(mean((true_tvt - predicted_tvt)^2))
```

Lower is better.

The true `TVT` values for the hidden evaluation rows are not visible to competitors. During the competition, Kaggle reports public leaderboard scores on a public split. The final ranking uses private leaderboard scoring, normally revealed at the end.

## 6. Submission Format

The file must be named:

```text
submission.csv
```

It must have exactly:

```csv
id,tvt
000d7d20_1442,0.0
000d7d20_1443,0.0
...
```

Requirements:

- `id` must match the current Kaggle run's sample submission IDs;
- `tvt` must be numeric;
- no missing, `NaN`, or infinite predictions;
- notebooks must generate this file dynamically for the hidden test set.

## 7. Code Competition Constraints

Official code requirements:

- submissions must be made through Kaggle Notebooks;
- CPU notebook runtime must be at most 9 hours;
- GPU notebook runtime must be at most 9 hours;
- internet must be disabled;
- public external data and pretrained models are allowed if freely and publicly available;
- output file must be `submission.csv`.

Official submission limit:

- maximum 5 submissions per team per day;
- up to 2 final submissions can be selected for judging.

## 8. Current Project State

From `reports/big_signal_public_lb_push.md` and the current Kaggle submission history:

Best confirmed project score:

- `7.235`: Wellbore wizard physics PF stack

Useful references:

- `7.263`: David v12 budget guarded clean GPU
- `7.588` to `7.606`: Fleongg / Ricardo-style blends
- `7.703`: David bimodal fastcpu no-sameid

Rejected or dangerous routes:

- `20.579`: pure artifact inference mismatch
- `11551.955`: direct train-TVt overlap lookup
- `15357.198`: public 7.159-style attempt failed catastrophically in current implementation
- static embedded visible-test CSV replay failed hidden rerun format checks

Current public leaderboard context checked on 2026-06-29:

- public rank top score is about `5.291`;
- current project best `7.235` is meaningfully behind top public solutions, so future work needs real signal, not tiny near-duplicates.

## 9. What Makes This Problem Hard

1. Hidden rerun changes the visible test wells.
   Static submissions generated for the visible three examples are not robust.

2. The target is a well-wise trajectory.
   Row-wise ML can violate smoothness, prefix continuity, and geological plausibility.

3. `GR` is useful but incomplete.
   Each visible test well has missing `GR` rows, so signal alignment must be robust to gaps.

4. Typewell alignment is central.
   Horizontal `GR` should be correlated against the vertical typewell `GR` indexed by `TVT`.

5. Public LB can reward brittle mechanisms.
   Some public notebooks or artifacts may encode assumptions that do not transfer unless faithfully reproduced.

6. Submission budget is scarce.
   With 5 submissions per day, leaderboard probing must be guarded by local validation.

## 10. Likely Modeling Families

### A. Physical / Kinematic Extension

Use known `TVT_input` prefix and continue a smooth trajectory through the hidden interval.

Useful checks:

- first hidden prediction should match last known `TVT_input`;
- slopes should be plausible;
- no sudden large jumps;
- predictions should remain within typewell `TVT` range plus reasonable margin.

Strength: stable and hidden-compatible.
Weakness: may miss geological layer changes.

### B. GR-to-Typewell Alignment

Align horizontal `GR` sequence to vertical typewell `GR` over `TVT`.

Common tools:

- dynamic time warping;
- normalized cross-correlation;
- beam search;
- particle filtering;
- smoothed path constraints.

Strength: directly uses geological log similarity.
Weakness: sensitive to missing/noisy `GR` and repeated signatures.

### C. Supervised / Learned Models

Train on full training wells where true `TVT` is visible, then infer hidden zones.

Possible features:

- `MD`, `X`, `Y`, `Z`;
- prefix-derived slope and curvature;
- `GR` windows;
- typewell alignment features;
- well-level geometry features.

Strength: can learn recurring patterns.
Weakness: hidden test may differ; pure row-wise models can be unstable.

### D. Ensemble / Stack

Blend a physical/PF baseline with artifact/model predictions.

Strength: often improves robustness if components are independent.
Weakness: near-duplicate blends have low upside; artifact mismatches have caused bad scores.

## 11. Recommended Submission Gate

Before spending a Kaggle submission, every output should pass:

1. Format check:
   - file exists as `submission.csv`;
   - columns exactly `id,tvt`;
   - row count and IDs match the run's `sample_submission.csv`;
   - no `NaN`, `inf`, or non-numeric `tvt`.

2. Hidden-compatible generation check:
   - notebook scans `test/*.csv` dynamically;
   - no hardcoded visible well IDs;
   - no fixed 14,151-row assumption.

3. Anchor continuity:
   - first hidden prediction should be close to last known `TVT_input`;
   - initial slope should not sharply disagree with prefix slope.

4. Shape check:
   - no large one-step jumps;
   - controlled curvature;
   - per-well trajectories remain smooth.

5. Typewell range check:
   - predictions should mostly stay within typewell `TVT` span plus margin.

6. Historical comparison:
   - compare against known 7.235, 7.263, 7.588-7.606, 7.703, 20.579, 11551.955 shapes;
   - reject candidates that resemble known bad submissions.

7. Local surrogate scoring:
   - run `scripts/local_surrogate_score.py` after downloading each kernel output;
   - block `reject_known_bad`, `reject_far_from_best`, and `high_shape_risk` candidates unless there is an explicit reason.

## 12. Recommended Next Steps

1. Build a lightweight `pre_submit_audit.py` around the checks above.
2. Run Kaggle kernels freely for output generation, but do not submit until the audit passes.
3. Prioritize hidden-compatible notebooks over static replay.
4. Use the current 7.235 physics/PF stack as the baseline.
5. Explore higher-upside approaches only when they add signal beyond near-duplicate blending:
   - stronger GR/typewell alignment;
   - robust particle filter / beam search;
   - careful artifact stack reproduction;
   - uncertainty-based per-well routing.
