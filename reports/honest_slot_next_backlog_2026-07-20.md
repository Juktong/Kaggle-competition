# ROGII — honest-slot next backlog (2026-07-20)

Session `e5b89aa5`. Written because D/E/F did not clear the submission gate this round. Incumbent honest slot
**54844628** (DWT+PF + gated structural field): public **7.891**, honest OOF **8.8626**. Neutral technical
language.

## Where this round left each direction
| dir | status | quantified outcome |
|---|---|---|
| **D top-K path ranker** | quantified partial-positive, **no submission** | hard max-likelihood selection is consistently worse than averaging; the usable form is **shrinkage of the ranker pick toward the weighted mean (λ≈0.5)**; gain **grows with training data**: 128 wells losing → 256 **+0.038** → 384 **+0.053**. Oracle headroom remains −1.10 (≈95 % unclaimed). Full 773-well dump still running detached. |
| **E CNN/Siamese GR scorer** | signal present, **gate not met** | val_auc 0.605 → 0.657 over 6 epochs and still rising, but weak discrimination; the PF's existing GR likelihood already performs this matching. No GPU spent (correctly surfaced in 51 s of CPU). |
| **F MTP multi-hypothesis** | **deliberately deferred** | it needs the *same* path-selector that D shows is the hard part (min-of-K only pays off if a selector can pick among the K), plus GPU that this box lacks. Sequencing it after D's verdict avoids repeating a known-hard problem. |
| **Probe 1 row-level structural weighting** | **DONE — negative** | all row-level schedules lose to the flat per-well weight under the same nested procedure: flat 8.9517 · toe-weighted 8.9915 · MD-decay 8.9761 · heel-weighted 9.0904. Struct/base error ratio does improve toward the toe (1.94 → 1.63) but too little to exploit. |

## Started this round
- **Probe 1 (row-level structural weighting)** — executed to completion, negative (above).
  Script: `scripts/probe_rowlevel_struct_weight.py`.

## OUTCOMES (session `6bf66c88`) — D full verdict + probes 1–3
- **D FULL VERDICT (773 wells): +0.0939, DOES NOT meet the +0.10 gate.** deployed 8.8682 → best
  ranker[lgbm] shrink λ=0.5 **8.7742**; bootstrap mean +0.0920, **5th pct +0.0073**, 96 % positive.
  Gain scaled monotonically (128 losing → 256 +0.038 → 384 +0.053 → 773 +0.0939) and the mechanism is
  confirmed (hard pick loses to averaging; shrinkage toward the mean roughly doubles the hard-pick gain),
  but the lower bound is not stably positive. **No submission.** Detail:
  `topk_path_ranker_followup_2026-07-20.md`.
- **Probe 1 (row-position weight schedules): NEGATIVE.**
- **Probe 2 (per-ROW nearest-neighbour distance gate/decay): NEGATIVE** — and informative: row gates improve
  as they loosen, so well-level is the correct gating granularity.
- **Probe 3 (typewell-group local dip plane): NEGATIVE** — gradient integration accumulates error; IDW's
  per-point absolute level is what makes it robust. Detail: `structural_field_probes_2026-07-20.md`.
- Net: the deployed structural configuration is a **local optimum** for this method family; further gains
  need a different channel, not re-tuning.

## Next probes (ordered by expected value / cost)
0. ~~Per-row neighbour distance~~ — **DONE, negative (Probe 2)**. Superseded item retained below for context.
1. ~~**Per-row neighbour distance for the structural field.**~~ The current gate uses a *per-well* closest-mate
   distance; the field's local reliability should depend on each row's own distance to the nearest
   neighbour point. Probe 1 showed row-position schedules fail, but row-level *distance* was not tested
   (it needs the struct producer to also save per-row `min(dd)`), which is a ~20 min re-run of
   `scripts/struct_oof_produce.py` with one extra saved array. **Highest-value remaining structural item.**
2. ~~**Typewell-group local affine / dip plane.**~~ — **DONE, negative (Probe 3)**. The deployed field is isotropic IDW; a locally-fitted
   plane `r ≈ a + b·x + c·y` over group-mates uses the dip direction the IDW ignores. Sketch and smoke test
   already written up in `external_pipeline_oof_scan_2026-07-19.md` §4 (#2).
3. ~~**Finish D at full scale.**~~ — **DONE: +0.0939, gate not met.** Remaining D lever: **K=48 seeds**
   (every scale increase raised the gain) plus a listwise ranker target and a stricter bootstrap requirement.
4b. **Finish D at full scale (original text).** The dump completes on its own; the decision rule is recorded in
   `topk_path_ranker_followup_2026-07-20.md`: build the inference path only if the full-scale shrinkage gain
   reaches **≥ +0.10** with a stably positive well-bootstrap.
4. **Residual correction by group + trajectory features.** Model the *residual* of the current blend against
   group id and trajectory geometry (a small GBM), nested by well — cheap, reuses `decomp_features.npz`.
5. **E continuation on Kaggle GPU** — larger encoder / more pairs / more epochs to see where val_auc
   saturates; or a mini-DP test showing the learned cost beats NCC even at AUC ≈ 0.66.

## Standing gate (unchanged)
honest OOF materially < 8.8626 · bootstrap stably positive · stress not materially worse · leakage audit
pass · format audit pass · diff-vs-54844628 explainable · inference build proportionate to the gain.
