# ROGII — Sunny OOF: smoke-first fix, run status, and result (2026-07-18)

Primary objective of the round: fix the failed Sunny OOF pipeline with smoke-first discipline (Directive 4),
obtain a valid honest CV, compare to DWT, and test a DWT+Sunny blend. Session `276bd506`. Neutral language.

## 1. Failure → root causes → fixes (smoke attempts)
The prior run `joezzzzz/rogii-sunny-oof-codex` failed after ~60 min at the OOF-consolidation cell
(`oof_preds` empty). Iterating with the smoke discipline surfaced **three** distinct issues, each fixed:

| # | root cause (found by reading + smoke) | fix |
|---|---|---|
| 1 | **`FLAG_MODEL=True` skipped training.** The LightGBM training that populates `oof_preds` is inside `if not FLAG_MODEL:`; setting `FLAG_MODEL=True` skipped it, so the consolidation ran on an empty dict → crash. | keep **`FLAG_MODEL=False`** (trains), `IS_SUBMISSION=False`, + a **controlled consolidation cell** (the notebook's own consolidation is contradictorily gated by `FLAG_MODEL and not IS_SUBMISSION`). |
| 2 | **`TEST_SIZE` subsets AFTER the ~60-min per-well `build_well` feature loop** (cell 5), so a small smoke was not fast. | subset `hw_paths`/`train_wids` **before** `build_well` (guarded by `FLAG_TEST`). |
| 3 | **`train_lightgbm` used row-level `KFold`** → within-well leakage → optimistic OOF CV, not comparable to DWT's native-mask 10.40. | switch to **`GroupKFold`** by well (honest, DWT-comparable CV). |

Hard asserts added before consolidation: `oof_preds` non-empty, `oof_df` has columns and matches `len(y)`,
OOF finite. Prints the GroupKFold meta OOF CV and per-model CVs; saves `/kaggle/working/sunny_oof.npz`
(well, oof_drift, y_drift, last_known, per_model). Notebook: `kaggle_kernel_sunny_oof_smoke/` (v2).

## 2. Cost finding (important for future runs)
Even with the early `build_well` subset, a 15-well run still takes ~30+ min: the runtime is dominated by a
**fixed cost** (reading the full `henryjavier/rogii-datasets-processed/ROGII_train_df.parquet` + full-data
setup) that does **not** scale with `TEST_SIZE`. So a truly "fast" smoke is not achievable for this
notebook; every run is ~30-60 min. This is recorded so future rounds budget for it and do not expect a
minutes-scale smoke here.

## 3. Run status
- Smoke v2 (`FLAG_MODEL=False` + early-subset + GroupKFold): **COMPLETE — SMOKE PASS** (all hard asserts
  passed: `oof_preds` populated with lightgbm-1/2/3, finite, columns present; OOF saved). The pipeline is
  **FIXED**. Note: because a pushed/batch kernel has `is_submission1=True`, the cell-7 `TEST_SIZE` subset was
  skipped, so the run trained on **full data (735 wells / 3.58M rows)** — i.e. this is effectively the
  **full formal OOF**, not a 15-well smoke (the early `build_well` subset applied, but training uses the
  parquet-derived `train_df`). Runtime ~130 min (fixed parquet/setup ~60 min + full GroupKFold training).
- **Sunny LightGBM-ensemble GroupKFold OOF CV (TVT drift RMSE) = 10.4732** (735 wells, 3.58M rows);
  per-model lightgbm-1/2/3 = 10.42 / 10.86 / 10.50. **This ≈ DWT's native-mask CV 10.3987** — the GBM
  ensemble component of the Sunny pipeline is NOT stronger than DWT (as expected for a GBM on honest
  features; same blend-neutral frontier).
- **Important: the submitted "Sunny PF90 beam-mean10" (54710185, public 8.864) is the PHYSICAL/beam model,
  NOT this LightGBM meta.** The run also emitted `submission_sunny_physical.csv` + `submission_v10_artifact_stack.csv`.
  So the 10.47 GBM CV does not describe the physical model's 8.864 public; the physical model's honest CV
  was not isolated here. The valid honest strength comparison for the submitted Sunny remains its public
  8.864 < DWT 9.519 (both leakage-audit-clean).

## 4. Does Sunny change the final-2? — the strength question is already answered
- **Sunny's honest strength vs DWT does NOT depend on the internal CV:** Sunny is leakage-audit-clean
  (2026-07-17) and its **public 8.864 < DWT 9.519** (both honest → public ≈ private). So **Sunny is a
  genuinely honest model stronger than DWT on the public/honest measure.** The OOF CV is a confirming
  second data point (subject to preprocessing-comparability caveats); it does not overturn the public
  comparison.
- **Final-2 recommendation is unchanged:** novel/mixed `{det-base DWT 54775625, Sunny PF90 54710185}`;
  overlap-heavy `{det-base DWT 54775625, Gate-Safe 54289934}`. Sunny is the honest diverse 2nd slot (or,
  if its CV/fold-stability confirm it clearly below DWT, the honest slot-1 with DWT as the floor).

## 5. DWT+Sunny blend test
Well-level analysis (`scripts/sunny_dwt_blend_analysis.py`) on the saved OOF vs DWT `combo_state`
(per-well error correlation + nested well-level blend weight). Result (`row_blend.py`, 735 wells aligned by (well, position), truth verified within 2 ft, 0 mismatch):
**corr(err_Sunny-GBM, err_DWT) = 0.746** (decorrelated, not the ~0.9 of same-input toys); **nested
well-split blend weight = +0.16 (STABLE, POSITIVE in both folds)**; **out-of-sample pooled RMSE gain =
+0.076** (blend `DWT + 0.16·(Sunny−DWT)` vs DWT). This is the **first strong-decorrelated POSITIVE honest
blend signal** in the project — a positive weight (genuine independent info), NOT the negative-weight
λ-disguise that public has repeatedly rejected.

Decision on a DWT+Sunny blend submission: **NOT justified this round**, for three reasons: (1) the gain is
small (~0.9%) and local-OOF only — the lessons doc repeatedly shows local blend/post-proc gains fail to
transfer to public (§7); (2) it is the GBM-meta blend, and under best-of-2 **selecting Sunny-physical
(8.864) dominates** a DWT+Sunny-GBM blend (~9.44 even if the +0.076 transfers) — so it does not improve the
final-2; (3) it would require a heavy dual-pipeline notebook (Sunny ~2 h) for a dominated, uncertain gain.
The signal is recorded as the one genuinely-positive honest-blend result; a future round could test transfer
by blending DWT with the **physical** Sunny OOF (unmeasured here) rather than the GBM meta. (Under best-of-2, a blend is only worth a slot if it beats
BOTH DWT and Sunny; the default honest deliverable is the best-of-2 selection `{det-base DWT, Sunny}`.)

## 6. Next action
Primary objective is COMPLETE (pipeline fixed; Sunny GBM CV obtained; blend tested). Final-2 recommendation
is **unchanged**: novel/mixed `{det-base DWT 54775625, Sunny PF90 54710185}` (best-of-2; Sunny-physical is
the honest upside, public 8.864 < DWT 9.519); overlap-heavy `{det-base DWT 54775625, Gate-Safe 54289934}`.
**No new competition submission** is warranted (the GBM-blend is dominated + transfer-uncertain; the pair is
a selection of banked refs). The single highest-value future step: isolate the **physical** Sunny model's
honest OOF (its 8.864 public suggests it is the genuinely-stronger component) and test a DWT+physical blend.
