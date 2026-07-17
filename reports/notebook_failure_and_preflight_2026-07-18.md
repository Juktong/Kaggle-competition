# ROGII — notebook failure incident + preflight requirement (2026-07-18)

Filed after the user reported "my notebook failed". Neutral technical language.

## 1. Which notebook failed
- **`joezzzzz/rogii-sunny-oof-codex`** (ERROR). Last run 2026-07-17 15:41:39, GPU **Tesla P100-PCIE-16GB**.
- All other recent user-owned kernels are COMPLETE (checked via `kaggle kernels status`):
  `rogii-dwt-affine-codex`, `rogii-dwt-detbase-codex`, `rogii-b4-guarded-codex`, `rogii-dwt-honest-codex`.
  There is **no newer failed kernel** — the Sunny OOF fork is the failure.
- This kernel = my fork of `henry_v10_sunny80_blend` (the Sunny v34 meta) with `FLAG_MODEL=True,
  IS_SUBMISSION=False, TEST_SIZE=120`, created to obtain Sunny's honest OOF CV (task 2 of the prior round).

## 2. Failure details (CONFIRMED from the Kaggle log)
- **Ran ~60.1 min**, then failed. **No valid output produced** — only the log was written (no OOF,
  no submission, no artifact).
- **Failed cell:** Jupyter `In [51]` (the OOF-consolidation cell), at line
  `_dbg(f"Estadísticas de predicciones (OOF):\n{oof_preds_df.describe()}")`.
- **Exception:** `ValueError: Cannot describe a DataFrame without columns` — i.e.
  `oof_preds_df = pd.DataFrame(oof_preds)` had **zero columns** because the `oof_preds` dict was **empty**.

## 3. Root cause (CONFIRMED)
- `oof_preds` is initialized `{}` and is meant to be filled by the per-model OOF-training cells, each
  guarded by a **per-model flag**: the notebook ships with **`flag_cat = 0`** and **`flag_xgb = 0`**
  (CatBoost / XGBoost training disabled), and the LightGBM OOF path likewise did not populate the dict
  under this configuration.
- My fork changed only the **mode** flags (`FLAG_MODEL=True, IS_SUBMISSION=False`), which activate the
  OOF-**consolidation** cells (`if FLAG_MODEL and not IS_SUBMISSION:`), but it did **not** enable the
  per-model **training** flags. Result: the consolidation cell ran on an **empty `oof_preds`** and crashed.
  Additionally, `modelos-20-pozos` (a referenced pretrained-model dataset) was not attached to the fork's
  `dataset_sources` — a contributing factor if a load-path was expected instead of training.
- **This is a flag/configuration mismatch, not a data or algorithm error.** It is exactly the class of
  error a short smoke run surfaces in minutes; here it cost ~60 min of GPU time and produced nothing.

## 4. Confirmed vs. unconfirmed
- **Confirmed:** the failing kernel, runtime (~60 min), failed cell (`In [51]`), exact exception, empty
  `oof_preds` cause, `flag_cat=0/flag_xgb=0`, no output artifact.
- **Unconfirmed:** the exact per-model flag wiring that *would* populate `oof_preds` in OOF mode (needs a
  smoke to determine which of `flag_cat/flag_xgb/flag_lgb` + `modelos-20-pozos` the OOF path expects);
  Sunny's numeric OOF CV (never computed — the run died before consolidation).

## 5. Impact on current conclusions — NONE
- The failure does **not** change any final-2 / Sunny / qwer / DWT conclusion.
  - **Sunny** honesty was already established by the **source leakage audit** (no overlap-copy, no
    gold-prefix, GroupKFold OOF, NCC/beam forward) — the CV was only a *quantification*, not the honesty
    verdict. Sunny remains a viable honest slot; under best-of-2 the exact CV is not decision-critical.
  - **qwer** (excluded), **DWT det-base** (54775625 = 9.487 honest floor), **Gate-Safe** (overlap fallback)
    are unaffected.
- **Final-2 recommendation stands:** novel/mixed `{det-base DWT 54775625, Sunny PF90 54710185}`;
  overlap-heavy `{det-base DWT 54775625, Gate-Safe 54289934}`.

## 6. Preflight checklist for future long Kaggle runs (now Directive 4 in CLAUDE.md)
Before any multi-hour Kaggle/GPU/CPU run or submission:
1. imports / paths / packages / secrets / dataset+kernel_sources resolve;
2. notebook runs **end-to-end to the key output cell** on a tiny input or `SMOKE_RUN`/`FAST_MODE`
   (small `TEST_SIZE`, 1–2 folds, few epochs, `nrows`) — confirm the *output-producing* cells run, not
   just setup;
3. for Kaggle-only pipelines: push a short smoke kernel / set `SMOKE_RUN=True` and read the completed log;
4. validate output format (file exists, columns, row count, all finite, id set/order, value range);
5. record the preflight command / time / result / commit / notebook ref;
6. no full long run and no submission slot until the smoke passes; document any skip + its risk;
7. when forking a heavy public notebook, verify the **flag combination** activates the intended path on a
   tiny run first (this incident: mode flags on, but model-training flags left off → empty OOF).

## 7. Fix needed? Assessment — the fix is NOT small; DEFERRED (not blindly re-run)
- **A fix is only needed if a future round still wants Sunny's numeric OOF CV / OOF array** (for the
  DWT+Sunny blend test). It is **not** needed for the current final-2 (Sunny is already verified honest).
- **On inspection the fix is NOT a small/low-risk change.** The LightGBM OOF population (cell that does
  `oof_preds["lightgbm-i"] = _oof`) sits inside a **load-vs-train branch** (`if models_dir.exists() and
  models_dir.is_dir(): ... else: train`) that interacts with `FLAG_LOG`, `flag_cat`, `flag_xgb`, and the
  `FLAG_MODEL/IS_SUBMISSION` mode. Producing a non-empty `oof_preds` in OOF mode requires reverse-engineering
  which branch/flag combination the notebook expects (load a saved OOF vs train from scratch; which model
  families; whether `modelos-20-pozos` must be attached). This is a multi-flag mode-wiring investigation,
  not a one-line change.
- **Decision: DEFER.** Per Directive 4 (never launch a long run on an unvalidated config) and the
  "only low-risk small fixes" constraint, I did **not** blindly re-run another ~1 h GPU job with a guessed
  flag change — doing so would repeat the exact mistake this incident is about. The correct next step for a
  future round that wants the CV: (a) read the load-vs-train wiring to fix the flag combo; (b) add a
  `SMOKE_RUN` toggle (few wells, 2 folds) + a `print(len(oof_preds))` assert right before the consolidation;
  (c) push the **smoke** and confirm from the log that `oof_preds` is non-empty and a CV prints; (d) only
  then scale up. Even fixed, the *full* 5-fold OOF trains 3 model families on 773 wells (hours) — a
  smoke-scale partial CV is the realistic target, and it is not decision-critical (Sunny is already honest).
