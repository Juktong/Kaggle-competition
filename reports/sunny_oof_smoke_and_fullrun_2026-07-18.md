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
- Smoke v2 (`FLAG_MODEL=False` + early-subset + GroupKFold, TEST_SIZE=15, 2-fold): **<STATUS>**.
- Result (GroupKFold meta OOF CV on the smoke subset): **<CV_RESULT>**.

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
(per-well error correlation + nested well-level blend weight). Result: **<BLEND_RESULT>**. Decision on a
DWT+Sunny blend submission: **<BLEND_DECISION>**. (Under best-of-2, a blend is only worth a slot if it beats
BOTH DWT and Sunny; the default honest deliverable is the best-of-2 selection `{det-base DWT, Sunny}`.)

## 6. Next action
**<NEXT_ACTION>**
