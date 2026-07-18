# ROGII — Sunny physical/beam honest OOF + leakage correction (2026-07-18)

Session `06dd2efb` (chain `…→276bd506→06dd2efb`). Objective: isolate the Sunny PF90 physical/beam model's
**honest** OOF (novel-well component) and test a DWT+physical blend. Neutral technical language.

## 1. Source mapping (DONE)
- The submitted **Sunny PF90 beam-mean10 (54710185, public 8.864)** physical component is `SUNNY_CODE`
  (338-line pure-CPU script — numpy/pandas/scipy only, no GPU/parquet), embedded + exec'd in cell 108 of
  `henry_v10_sunny80_blend`, writing `submission_sunny_physical.csv`. The henry final = 0.80·sunny_physical
  + 0.20·v10_artifact.
- Prediction (cell-108 main loop, L283-331): for each well,
  - **PF forward** `tvt_pf = run_pf_lik_ensemble(hw, tw, n_particles=500, n_seeds=128)` — a 128-seed
    likelihood-weighted particle filter that matches horizontal GR to the typewell GR-vs-TVT profile,
    starting from the known heel (`TVT_input`). **Test-available inputs only → honest forward model.**
  - **`tvt_phys = tvt_from_contacts(hw_tr, tw_tr)`** — computed ONLY for wells in `train_wids`.
- Combine: **if the well is in train → use `tvt_phys` (primary, "RMSE ~0.007 ft"); else (novel) → use `tvt_pf`.**

## 2. LEAKAGE CORRECTION (important — revises the 2026-07-17 "clean" audit)
`tvt_from_contacts` (L51-58) is **not honest** and only runs on overlap wells:
```
offset = (hw_tr['TVT'] - (ref_tvt - (hw_tr['Z'] - hw_tr[ref_col]))).mean()   # hw_tr['TVT'] = toe TRUTH
return ref_tvt - (hw_tr['Z'] - hw_tr[ref_col]) + offset                       # hw_tr[ref_col]=EGFDU (train-only surface)
```
- It uses **`hw_tr['TVT']` (the toe truth)** in the offset → **train-label leakage**; and **`hw_tr['EGFDU']`
  (a structural surface that is TRAIN-ONLY — test wells carry only MD,X,Y,Z,GR,TVT_input)**, so it is not even
  computable on a genuinely novel test well. Hence the `if wid in train_wids:` guard — it only fires on wells
  present in train (the 3 visible + any hidden duplicates), where it reconstructs the toe ~exactly (~0.007 ft).
- **Consequence:** the submitted Sunny PF90's **public 8.864 is inflated by overlap leakage** on the
  train-duplicate wells; on genuinely **novel** wells it uses only the honest **PF forward** (`tvt_pf`).
  The 2026-07-17 leakage audit graded the henry *notebook* clean but did not decode the exec'd `SUNNY_CODE`
  string — this corrects that: **Sunny PF90 is NOT purely honest; its honest novel-well component is the PF
  forward, whose OOF is measured below.**

## 3. Honest PF-forward OOF (the novel-well proxy)
Harness (`scripts/pf_forward_oof.py`): run `run_pf_lik_ensemble` on each TRAIN well using only its heel
(`TVT_input`) + typewell (NO `tvt_from_contacts`, NO toe truth), predict the toe, score vs `TVT`. This is the
honest forward performance = what Sunny PF90 does on novel wells.
- **Smoke (3 wells, n_seeds=8): PASS** — harness runs, honest toe-RMSE = 3.88 / 19.75 / 5.62 (NOT the leaked
  ~0.007), ~2.5 s/well. Local, pure-CPU.
- **Formal (773 wells, n_seeds=32, local, ~60 min): <FORMAL_STATUS>**
- **Honest PF-forward OOF pooled CV (toe TVT RMSE): <PF_CV>** vs DWT native-mask **10.3987**.
  (Caveat: n_seeds=32 < the submitted 128 → this is a slightly-conservative upper bound on the RMSE.)

## 4. DWT + Sunny-physical blend / selector
Well-level + row-level nested analysis vs DWT `combo_state`: **<BLEND_RESULT>**.

## 5. Final-2 implication
**<FINAL2_IMPLICATION>**
