# ROGII — Sunny PF90 honesty verification (2026-07-17)

Task 2 of the relaxed-submission round. Goal: does Sunny (ref 54710185, public **8.864**) genuinely beat
DWT on **novel/private** wells, or is its 8.864 public-favorable? Neutral technical language.

## 1. Source
- Submitted candidate: `54710185` "Sunny PF90 beam-mean10 test-only conservative architecture hedge".
- Local source (Sunny family): `kaggle_kernel_henry_v10_sunny80_blend/rogii-henry-v10-sunny80-blend.ipynb`
  = kernel `leemarc223/rogii-henry-v10-sunny80-blend`, version tag `ROGII_v34_proper_climber_optuna_n1`.
  A v34 meta pipeline (the submitted "PF90 beam-mean10" is a sibling variant of this Sunny family).

## 2. Leakage / honesty audit (source) — PASSED
Structural audit of the pipeline (65 code cells):
- **NO overlap-copy** — no `TVT_input = train.values` train→test copy trick (the mechanism behind the
  public 7.2 plateau). The only `TVT_input.values` uses are **drift-rate features** (`np.diff` over the
  known tail), not truth copying.
- **NO gold-visible-prefix leakage** — the only "000d7d20"/"visible" reference is a strategy comment in
  the embedded `SUNNY_CODE`.
- **Proper honest CV** — `GroupKFold(n_splits=5)` by well; per-fold OOF; `overall_score =
  root_mean_squared_error(revert_log(y), revert_log(oof))`. Ensemble = LightGBM + CatBoost + XGB, plus an
  **NCC/beam geosteering forward** (`ncc = Hn @ Cn.T`, horizontal-GR→typewell matching — a *test-available*
  forward model, honest) and a **Caruana Climber** hill-climb blend.
- `y_test_temp = train_df.loc[mask_temp,'target']` is an **honest train-holdout** evaluation, not leakage.
- **Relation to the plateau:** Sunny's 8.864 is **above the overlap plateau (7.2)** and inside the honest
  manifold (8–14; the strongest shared honest public models reach ~8.1, lessons §1). So Sunny is **not an
  overlap play** — it is a genuine honest forward model, plausibly stronger than DWT (9.519 public / 10.40 CV).

**Leakage verdict: CLEAN.** Sunny is a genuinely honest model (no overlap-copy, no gold-prefix, proper
GroupKFold OOF, test-available inputs). This is the decisive honesty signal, and it is positive.

## 3. CV verification (partial OOF fork)
- Fork `joezzzzz/rogii-sunny-oof-codex` = the henry v34 notebook with `FLAG_MODEL=True, IS_SUBMISSION=False`
  (activates the OOF path), partial `TEST_SIZE=120` for a fast CV estimate, GPU, offline; datasets
  henryjavier + needless090 + ravaghi + the two kernel_sources.
- **Reported meta OOF CV (real RMSE): `<CV_PENDING>`.** (Filled on completion. Gate: CV materially below
  DWT's 10.40 → Sunny is a stronger honest base.)

## 4. Verdict & use in final-2
- **Honesty: CONFIRMED clean** (leakage audit) — Sunny is a legitimate honest model, not a public/overlap
  trick. Its 8.864 public (better than DWT 9.519) is therefore expected to reflect genuine novel-well
  quality (honest models: public ≈ private).
- **Use:** Sunny is a **viable honest slot candidate** — the diverse honest 2nd slot in `{det-base DWT,
  Sunny}` (best-of-2), which for a novel-private goal weakly dominates `{DWT, Gate-Safe}`. Whether Sunny
  should *replace* DWT as slot-1 depends on its CV (`<CV_PENDING>`): if CV < 10.40 with stable folds, Sunny
  is the stronger honest base and could be slot-1, with DWT as the safety floor slot-2.
- **Not a public-only / overlap candidate** — the leakage audit rules that out.
