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
Harness (`scripts/pf_forward_oof.py` → batched/checkpointed `pf_oof_ckpt.py`): run `run_pf_lik_ensemble`
on each TRAIN well using only its heel (`TVT_input`) + typewell (NO `tvt_from_contacts`, NO toe truth),
predict the toe, score vs `TVT`. This is the honest forward performance = what Sunny PF90 does on novel wells.
- **Smoke (3 random train wells, n_seeds=8): PASS** — honest toe-RMSE ≈ 10.47 pooled (NOT the leaked
  ~0.007). The earlier 3-*visible*-well smoke (3.88/19.75/5.62 ≈ 13.4 pooled) was atypical — dominated by the
  hard visible well 00bbac68 (19.75). Random wells sit near DWT.
- **Formal (773 wells, n_seeds=24, local, batched+checkpointed, 57 min): COMPLETE** (partial reads at
  160/272/416 wells all stable; the first single-shot 773/n_seeds=32 run was resource-killed with no
  checkpoint → redesigned to checkpoint every 16 wells + stream a tailable log + resume).
- **Honest PF-forward OOF pooled CV (toe TVT RMSE) = 10.9952** (773 wells, 3,783,989 toe rows) vs DWT
  native-mask **10.3987** → PF is **~0.60 ft weaker than DWT standalone in pooled RMSE**. KEY nuance: the
  pooled RMSE is **tail-dominated** (a few long high-drift wells); PF's **median well = 5.65 < DWT's median
  well = 6.41** — PF is *better on the typical well*; the pooled lag comes entirely from the high-drift tail.
  (n_seeds=24 < the submitted 128 → this is a slightly-conservative upper bound; more seeds would only lower
  the PF RMSE, strengthening the blend.)

## 4. DWT + Sunny-physical (PF) blend — the actionable result (DEFINITIVE, 773 wells)
Row-level nested analysis vs DWT `combo_state` (`scripts/pf_dwt_blend.py`; aligned by (well, toe-row),
truth-verified, **773/773 wells, 0 mismatch**). Stable & consistent across 160→272→773 wells:
- **error corr(err_DWT, err_PF) = 0.511** — genuinely decorrelated (vs the Sunny-GBM blend's 0.746) → the PF
  physical model carries independent information from DWT's GBM.
- **Complementarity (stable):** easy wells (DWT 3.28) PF=5.39 (PF<DWT 32%); mid (DWT 6.48) PF=7.28 (53%);
  **hard/high-drift wells (DWT 14.16) PF=11.20 (PF<DWT 67%)** → PF systematically rescues the wells DWT
  struggles on. Oracle per-well selector = **7.56** (upper bound, not deployable — needs truth to route).
- **Deployable fixed 0.5/0.5 blend: OOF CV = 9.2969 vs DWT 10.3987 → +1.10 ft (10.6%).** Nested 2-fold
  `DWT + a·(PF−DWT)`: a = 0.40/0.48 (stable both folds), OOS gain +1.08. **Well-level bootstrap: mean +1.12,
  5th-pct +0.66, 100% of resamples positive** → extremely robust (tightened from +0.09 at 272 → +0.66 at 773).
- **Transfer-robustness: the gain is DECORRELATION-driven, not bias-cancellation** — adding a per-fold
  intercept changes the OOS gain by only −0.018 ft (both models near-unbiased: DWT −0.04, PF −0.69). Pure
  variance-reduction from two decorrelated honest predictors is a statistical property that transfers, unlike
  train-specific bias correction or the negative-weight λ-disguise public has repeatedly rejected.
- **This is the strongest honest signal in the project** (vs the GBM blend's +0.076): a **positive-weight,
  decorrelated, distinct-model-class blend** taking the honest CV from 10.40 to **9.30**.

## 5. Submittable notebook (built + locally validated; push is a user hand-off)
`kaggle_kernel_dwt_pf_blend/` = the banked det-base DWT notebook + one inserted honest-PF-blend cell
(between DWT's `pred` and the write): discovers test wells, runs `run_pf_lik_ensemble` (NS=64, honest,
NO `tvt_from_contacts`), aligns by `id={well}_{row_idx}`, sets `pred = 0.5·DWT + 0.5·PF`. On the hidden
(novel) rerun wells this is a **pure honest blend** (no overlap exploitation).
- **Local blend-cell validation: PASS** — 14,151 rows, PF coverage 100%, all finite, id-set unchanged vs
  `sample_submission`, `blend == 0.5·DWT+0.5·PF` exact, sane TVT range.
- **Pre-submit audit (Directive 1):** (a) honest inputs only — PF uses hw[MD,X,Y,Z,GR,TVT_input]+tw[TVT,GR];
  grep-clean of `tvt_from_contacts`/EGFDU/Geology/`hw['TVT']`; DWT part is the banked audited notebook.
  (b) format/finite/id-order/range all PASS locally; weight fixed (0.5), no test-time tuning.
- **This env has NO kaggle CLI/creds** → cannot push/submit here. Hand-off commands (user runs in an
  authenticated session; interactive run = the 3-visible-well **smoke** per Directive 4, submit = hidden rerun):
  ```
  kaggle kernels push -p kaggle_kernel_dwt_pf_blend      # runs interactive on 3 wells = smoke
  kaggle kernels status joezzzzz/rogii-dwt-pf-blend-codex # wait complete; read [PF-blend] log lines
  kaggle kernels output joezzzzz/rogii-dwt-pf-blend-codex -p /tmp/blendout   # validate submission.csv
  # then, only if smoke log + output validate:  submit via the kernel's "Submit to Competition"
  ```

## 6. Final-2 implication
The honest OOF is the only valid **novel-well** proxy (public = 3 visible overlap wells → a leakage game; the
notebook reruns on hidden novel wells for the private prize). On that proxy:
- **DWT** honest OOF = 10.40. **Sunny PF90 on novel = the honest PF forward ≈ 11.0 ≈ DWT** (its public 8.864
  is overlap leakage on the 3 visible wells, `0.80·leaked_tvt_phys + 0.20·v10`, NOT novel strength) → Sunny
  PF90 is **not** a novel upgrade over DWT.
- **DWT+PF blend honest OOF = 9.30 (+1.10 vs DWT), robust + decorrelation-driven + transfer-plausible** →
  the **strongest honest novel-well model found**, and it **dominates Sunny PF90 as the honest 2nd-slot
  candidate** (blend 9.30 < Sunny-on-novel ~11.0 ≈ DWT 10.40).

**Recommended action (Directive-1-authorized by a clear, reproducible, robust honest OOF improvement):**
**submit the DWT+PF blend** (notebook `kaggle_kernel_dwt_pf_blend/`, built + locally validated + audit-clean).
Under best-of-2 the safest pairing for the stated **novel** goal is **{det-base DWT 9.487 (proven honest
floor), DWT+PF blend (honest upside)}** — DWT floors any transfer shortfall, the blend is pure upside; this
**replaces the prior {DWT, Sunny PF90}** (Sunny adds nothing on novel). If overlap-in-private is a concern,
substitute Gate-Safe for one slot ({DWT+PF blend, Gate-Safe 7.212} covers novel + overlap, at the cost of
DWT's proven floor).

**Caveats / honesty:** (1) transfer is **untested** — this background environment has no kaggle CLI/creds, so
the blend was not submitted; the OOF gain is decorrelation-driven (the transfer-robust kind), but §7 warns
some local gains do not transfer, so the **public/private check must be done at submit time** (interactive
run on the 3 visible wells = the Directive-4 smoke; then Submit for the hidden rerun). (2) n_seeds=24 is a
conservative PF; the submission uses NS=64 (≥ OOF), which can only help. (3) The blend is a **pure honest
play** (no overlap override) — its value is on the novel/private set, by design.

## 6. Secondary scan — other honest forward / sequence / alignment pipelines (map, verified)
Repo-wide audit for distinct honest novel-well models beyond DWT/Sunny/Gate-Safe. Verified by direct
grep of the sources (not just the agent report). **No graph/GNN model exists anywhere.**
- **TIER 1 — Lucifer `kaggle_kernel_lucifer_wellbore_wizard_pf_stack/wellbore-wizard-physics-pf-stack.ipynb`
  is a SUPERSET of Sunny's PF.** Confirmed present: `beam_search` (beam-search DP alignment / DTW-form),
  `run_pf_ancc` (ANCC-anchored PF), `run_pf_z` (Z-velocity-coupled PF), `run_pf_lik_ensemble` (the SAME
  128-seed lik-PF Sunny ships — this round's OOF measures exactly this one), `multi_scale_ncc` (multi-scale
  NCC matcher), + `selector_well` (well router). All take `(hw, tw)` and derive inputs from the known-heel
  mask only → **honest, OOF-able by masked per-well replay, pure CPU (numba)**. Leakage is quarantined to an
  **overlap-only** post-processor `guarded_contact_override` (guard `if wid not in train_wells: continue`;
  same `hw_tr['TVT']`+`EGFDU` leak as Sunny). **→ The strongest next-round candidate: isolate the 4 forward
  models Sunny does NOT ship (beam / ANCC-PF / Z-PF / NCC) + selector for additional honest, potentially
  decorrelated novel-well signals.** Not launched this round (2-core box saturated by the lik-PF OOF; and
  the priority of the same-GR-matching-family variants is gated on this round's shared lik-PF OOF result).
- **TIER 3 — self-contained honest prototypes (`scratchpad_probes/`)**: `tw_align_proto.py` (typewell
  DTW warp, reads `data/rogii/train` directly, native mask = OOF, no external artifact — the cleanest
  standalone alignment probe); `bayesian_state_space_probe.py` (particle SMOOTHER w/ curvature state +
  posterior); `spectral_soft_alignment_probe.py`, `facies_token_alignment_probe.py` (DP sequence align);
  `ssl_gr_encoder_*` / `ssl_gr_embedding_probe.py` (SSL/ROCKET GR sequence encoders — in-repo notes report
  these as NEGATIVE-weight vs DWT so far). All honest, CPU.
- **NOT honest (excluded)**: `scratchpad_probes/dip_probe.py` feeds structural surfaces
  (`ANCC/ASTNU/ASTNL/EGFDU/EGFDL/BUDA`) as model features → train-only leakage (ceiling probe, not
  deployable). The `sp45_*` / `fleongg_*` working forks embed the same Lucifer stack + spatial plane/dense
  KNN imputers + overlap overrides (`_ov_tvt_from_contacts` = same leak) — no new honest model type.
