# ROGII — next-direction backlog (2026-07-15)

Curated set of candidate directions worth testing, chosen to AVOID the forms already shown to have
no stable gain (see `reports/lessons_and_strategy_2026-07-08.md` §2,§7–§14 and
`direction_search_public_research_2026-07-14.md`). Baseline = honest DWT (public 9.519 / internal
native-mask CV ~10.40, ref 54453597). Neutral technical language; honest OOF/masked-CV as the
private proxy; public-hedge kept separate; no train-only field (structural surfaces, Geology) read
at test time.

## Evidence constraints that shape this backlog (do not re-test these forms)
- Every same-input model (matcher / MTP / geometry / ROCKET / **learned SSL contrastive encoder** /
  local GBM / loss-diversity) lands on the **blend-neutral frontier** (ρ≈σ_D/σ_M) or resolves to a
  **negative blend weight** = disguised drift-rescaling (λ, disproven on public +0.62). Reusable
  screen: reject any "OOF gain" whose nested blend weight vs DWT is negative.
- The path/interpretation **selection** problem is **not identifiable** from path/well features even
  with unlimited clean synthetic labels (synthetic selector 16.32 > best-cost 14.75).
- DWT is **domain-robust** (worst spatial block ≈ worst random fold) → internal CV is a sound proxy.
- **F SSL-branch preflight (2026-07-15):** a learned contrastive GR encoder on ROGII gives RMSE 15.95,
  corr 0.723, blend weight **−0.096** — same as ROCKET. Representation quality is NOT the limiter;
  the GR channel is saturated by DWT. → external-data **SSL** pretraining is not GPU-warranted. The
  only remaining external-data lever is **labeled facies** (different signal), gated below.

Therefore the backlog concentrates on: (i) **new labeled information** (train-only structural labels
used compliantly as predicted features, and external labeled facies), and (ii) **submission-strategy**
directions that improve the deliverable (private rank) without needing to beat the blend-neutral wall.

Priority (do first): **V1, V2, V3, S-A(V4)** are all low-cost CPU gates; run them before any GPU.
N-A depends on V1/V2; N-B and S-B are Kaggle-GPU and gated on those.

---

## BIG N-A — Predicted structural framework as features (facies markers + structural surfaces)
- **Hypothesis:** the train-only structural labels (typewell `Geology` facies; horizontal structural
  surfaces ANCC/ASTNU/ASTNL/EGFDU/EGFDL/BUDA) encode the very interpretation DWT gets wrong. Train
  predictors GR/trajectory→(facies, surfaces) on train, deploy via test-available inputs, and feed the
  PREDICTED framework as features/constraints to a TVT residual/blend.
- **Why not a repeat:** prior facies work (dir C) was *unsupervised* KMeans tokens for *alignment*;
  this is *supervised* marker/surface prediction used as *features*. SSL/ROCKET used label-free GR
  representations; this uses the actual geological labels.
- **Compliance:** Geology/surfaces are train-only → used ONLY to train predictors; at test the inputs
  are GR/trajectory (test-available) and the framework is a learned function of them (same principle
  as DWT, trained on train). Train the downstream residual model on the predictor's **OOF** outputs to
  avoid train/test feature mismatch. Never read Geology/surfaces at test.
- **Resource:** CPU probe first (V1 marker gate + V2 surface gate). A stronger multi-output predictor
  (NN) is a Kaggle-GPU smoke candidate ONLY if the CPU gates show positive-weight signal.
- **Min validation:** `marker_predictability_probe.py` (V1) + a surface-predictability probe (V2);
  then a combined predicted-framework residual model; 5-fold well-OOF + spatial-block check; report
  RMSE, corr(err,DWT), nested blend weight sign.
- **Pass:** predicted-framework residual gives a **positive** nested blend weight AND OOF improvement,
  stable across folds and spatial blocks. **Stop:** GR→marker accuracy ≈ chance OR blend weight ≤ 0.
  **Submit:** stable positive-weight OOF gain on full nested CV + pre-submit audit (no train-only field
  at test) + visible-well audit (V5).

## BIG N-B — Multi-task DWT-family retrain with structural-auxiliary heads (Kaggle GPU)
- **Hypothesis:** retraining a DWT-class model with auxiliary heads predicting facies/surfaces (train
  labels as auxiliary *targets* during training; main target TVT) regularizes toward structure-aware
  features and may reduce the whole-well offset error.
- **Why not a repeat:** prior retrain (cb3) was same-target seed diversity → correlated/flat; this is a
  different training *objective* (multi-task structural auxiliary).
- **Compliance:** auxiliary labels used only during training; the deployed model consumes test
  GR/trajectory. Compliant.
- **Resource:** **Kaggle GPU** (retrain a DWT-family model / a GR-sequence NN with aux heads).
  GATED on N-A/V1/V2 showing usable facies/surface signal. Two-level: smoke (subset + 1 fold, confirm
  pipeline + aux-head learns) → full run.
- **Min validation:** add auxiliary targets to a CatBoost-GPU or a GR-sequence NN; dump OOF; check
  standalone strength, corr(err,DWT), and positive-weight blend / replacement vs DWT.
- **Pass:** multi-task model reaches ~DWT strength with decorrelated errors (positive blend) OR beats
  DWT standalone on honest CV. **Stop:** correlated/weaker (blend-neutral). **Submit:** stable honest
  OOF improvement + audit.

## BIG S-A — Decision-theoretic final-2 optimization under private-composition uncertainty
- **Hypothesis:** the deliverable (private rank) can be improved by choosing the final-2 pair that
  maximizes expected rank under a distribution over private composition (overlap fraction f), using
  conformal uncertainty (calibrated, dir B1) + honest-model diversity, rather than the default
  DWT 9.519 + one overlap hedge.
- **Why not a repeat:** the final-strategy doc *characterized* the hedge; this *optimizes* the pair
  quantitatively under a scenario model, and evaluates a diverse-honest 2nd slot vs an overlap hedge.
- **Compliance:** selection over already-submitted refs; no new prediction / no leakage.
- **Resource:** CPU (simulation/analysis).
- **Min validation:** model each candidate's private score S_i(f) = honest_base_i + overlap_benefit_i(f);
  simulate f∈[0,1]; pick the final-2 pair maximizing E[rank] / minimizing worst-case; compare to the
  current default. Uses V4 (honest-model diversity) as input.
- **Pass:** identifies a better or robust-optimal pair (or confirms the default is robust-optimal).
  **Stop:** n/a (always yields a decision). **Submit:** if it recommends re-submitting a better hedge,
  submit under hedge rules (labeled public, kept separate from honest).

## BIG S-B — External LABELED facies corpus (FORCE 2020) to strengthen the facies predictor
- **Hypothesis:** IF the facies-predictor branch (N-A/V1) shows signal but is limited by ROGII's facies
  label quantity/diversity, external labeled GR-facies data (FORCE 2020: GR present, labels CC-BY-4.0,
  logs NLOD 2.0, on Zenodo/GitHub) can pretrain a stronger GR→facies encoder transferred to ROGII.
- **Why not a repeat:** F's SSL branch (unsupervised) is preflight-negative; this is *supervised*
  external facies labels — a different signal.
- **Compliance:** (a) ROGII external-data clause **needs manual confirmation** (standard Kaggle
  code-comp clause allows freely/publicly-available external data + pretrained models unless the Host
  prohibits; the ROGII-specific clause is JS-gated, unverified); (b) offline runtime → FORCE data or a
  pretrained encoder must be attached as a **Kaggle Dataset**; (c) **domain gap** (North Sea vertical
  wells vs ROGII horizontal + typewell) — transfer uncertain; (d) NLOD/CC-BY citation + forum
  disclosure required.
- **Resource:** **Kaggle GPU** smoke (pretrain a GR→lithofacies encoder on FORCE, transfer to ROGII).
  GATED on: manual rule confirmation + N-A/V1 facies signal positive.
- **Min validation:** FORCE GR→lithofacies encoder → transfer embeddings/logits to ROGII toe rows →
  residual blend check (positive weight?).
- **Pass:** positive-weight blend on ROGII honest OOF. **Stop:** rule prohibits OR N-A facies signal ≤0
  OR transfer blend ≤0. **Submit:** stable OOF gain + audit + external-data disclosure.

---

## SMALL V1 — Marker-predictability gate (foundation for N-A / S-B)  `scratchpad_probes/marker_predictability_probe.py`
- **Hypothesis:** can GR-window features predict the typewell formation label at all? (near-chance =
  GR can't identify formation = the cycle-skipping problem in supervised form). Then: do the
  predicted-marker probability features give a positive-weight honest OOF blend vs DWT?
- **Compliance:** Geology trains the classifier; test inputs are GR only. Compute: **CPU probe**.
- **Validation:** GR-window→formation, GroupKFold-by-well accuracy vs majority; then predicted-marker
  probs → residual GBM on horizontal toe rows, 5-fold well-OOF, blend weight sign.
- **Result (2026-07-15):** typewell rows 1.04M, 43 formations, majority 0.282. GR→formation OOF
  accuracy **0.486** (> chance, so GR partially identifies formation), BUT predicted-marker residual
  RMSE 15.87, corr(err,DWT) 0.724, blend weight **−0.095 (negative)**. → the facies signal GR carries
  is already in DWT; predicted-marker features add **no independent info**. **V1 STOP condition met.**
- **Pass:** accuracy ≫ 0.28 AND blend weight > 0 → N-A facies branch has foundation. **Stop:**
  accuracy ≈ chance OR blend weight ≤ 0.

## SMALL V2 — Structural-surface predictability probe (foundation for N-A)
- **Hypothesis:** can GR/trajectory predict the horizontal structural surfaces (ANCC/ASTNU/… TVT
  depths) out-of-fold, and do predicted surfaces give a positive-weight blend? Surfaces are the
  structural framework; if partially predictable and decorrelated, they help.
- **Why not a repeat:** structural surfaces were previously only checked as *raw* targets (leave-well
  RMSE ~46, and they are test-stripped); here they are a *predicted* auxiliary feature, deployed via
  test-available GR/trajectory.
- **Compliance:** surfaces train the predictor; test inputs are GR/trajectory. Compute: **CPU probe**.
- **Validation script:** for each surface, GR+trajectory→surface residual (surface − last-known),
  5-fold well-OOF R²; stack predicted surfaces as features into a TVT residual model; blend weight sign.
- **Pass:** any surface OOF R² > 0 AND predicted-surface blend weight > 0. **Stop:** R² ≤ 0 or blend ≤0
  (surface-prediction ≈ TVT-prediction → blend-neutral).
- **Result (2026-07-15):** target = `surf − Z` (Z-detrended structural offset; Z & surfaces share the
  elevation frame). Foundation PASSES — all 6 surfaces OOF-predictable from test-available inputs
  (R² +0.59 .. +0.78, RMSE ~28–30 ft). Decisive nested blend vs DWT (10.393): **ORACLE** (TRUE `surf−Z`
  as features) gives a stable **POSITIVE** blend weight **+0.216** (folds +0.20..+0.23; nested-blend
  10.393→**10.140**; corr(err,DWT) 0.613) — the **first positive oracle in the whole search**: the
  structural framework genuinely carries information independent of DWT. **ACHIEVABLE** (OOF-PREDICTED
  `surf−Z`) gives blend weight **−0.020** = base-only (−0.021), corr 0.735, nested-blend 10.417 →
  blend-neutral. A surface predictor is a function of the test-available inputs, so predicted surfaces
  are redundant with the base model (Stage3 ≈ Stage0); the oracle's independent signal lives in the
  train-only surface residual, not reconstructable from test inputs. **V2 STOP condition met**
  (achievable blend weight ≤ 0); a stronger (GPU) predictor on the same inputs cannot recover it.
  Script `scratchpad_probes/structural_surface_probe.py`; report
  `reports/v2_structural_surface_probe_2026-07-15.md`.

## SMALL V3 — Stratified blend audit (is blend-neutral uniform, or is there an exploitable stratum?)
- **Hypothesis:** the blend-neutral property was measured pooled; a specific stratum (e.g. near-toe ×
  low-conformal-uncertainty, or high heel-match wells) might admit a stable positive-weight blend with
  an existing decorrelated OOF (geometry/matcher).
- **Why not a repeat:** prior routing used *well-family* quintiles (single feature); this jointly
  stratifies by (distance-segment × conformal-uncertainty band) at the *row* level.
- **Compliance:** uses existing test-available-derived OOFs. Compute: **CPU probe** (re-slice cached OOFs).
- **Validation:** partition toe rows by distance×uncertainty; per-cell nested blend weight of
  DWT+geometry (and DWT+matcher); flag any cell with stable positive weight + local RMSE gain.
- **Pass:** ≥1 cell with stable positive blend weight and honest local RMSE reduction. **Stop:** all
  cells w ≤ 0 (blend-neutral is uniform).

## SMALL V4 — Submission-level honest-model diversity (input to S-A)
- **Hypothesis:** even if honest models can't be *blended* (blend-neutral), a diverse 2nd honest final
  slot could hedge DWT's per-well variance at the *submission* level (private rank uses the better of
  the 2 selected). Quantify max-of-two vs single among existing honest OOFs.
- **Compliance:** analysis over honest OOFs. Compute: **CPU probe**.
- **Validation:** per-well, max-of-two internal CV among {DWT, geometry-GBM, matcher, (future) N-A};
  compare to DWT alone; also estimate per-well error correlation.
- **Pass:** max-of-two internal CV < DWT by a meaningful, stable margin → a diverse 2nd honest slot has
  value. **Stop:** ≈ DWT (correlation too high, as expected ~0.9).

## SMALL V5 — Visible-well pre-submit audit tool (reusable gate)  `scratchpad_probes/visible_well_audit.py`
- **Hypothesis (tooling):** the 3 visible test wells are in train with truth; a reusable script that
  scores any candidate's submission.csv on those wells vs truth (and format/finite/range/diff-vs-DWT)
  is a fast real-test sanity gate before any Kaggle submit.
- **Compliance:** audit tool. Compute: **CPU**.
- **Validation:** report candidate RMSE on the 3 visible wells, divergence vs DWT, format checks.
- **Pass:** used as a mandatory pre-submit gate for every future candidate. **Stop:** n/a (tooling).

---

## Explicitly de-prioritized given accumulated evidence (not in this backlog)
- **Standalone GPU sequence model (transformer/TCN) on GR only:** prior sequence NN (MTP GRU 15.5 /
  corr 0.77; cross-attn 12.87) + the SSL/ROCKET negative-weight preflights indicate another GR-only
  deep model lands on the blend-neutral/negative-weight frontier. Not prioritized without a new
  information channel (which N-A/N-B/S-B provide via labels).
- Any cross-well retrieval / spatial-field / KNN (all negative), any post-proc on DWT OOF
  (λ-disguise), any raw-GR alignment variant (oracle-tie), any feature-based path selector
  (non-identifiable). Not re-tried.

## Recommended first 2–3 to execute
1. **V1** (marker gate — running) + **V2** (surface gate): decide whether N-A / S-B (the labeled-info
   levers, the only new-information avenue) have any foundation, at CPU cost.
2. **V4 → S-A**: decision-theoretic final-2 optimization — improves the actual deliverable (private
   rank) regardless of the blend-neutral wall, at CPU cost.
3. **V5**: build the visible-well pre-submit audit tool (reused by every future candidate).
GPU (N-B / S-B) only after V1/V2 show positive labeled-info signal AND (for S-B) the external-data
rule is manually confirmed.

## Addendum (2026-07-15 session) — three additional candidates not covered above
- **B1' Real second honest PIPELINE OOF + measured-ρ blend.** Never measured a *real full pipeline's*
  error-correlation with DWT (prior "diversity" tests were same-input toys at ρ≈0.7–0.9). Re-run one
  honest public fork (e.g. romantamrazov 9.956, the 9.538 training kernel) to dump its train OOF; gate
  first with a cheap ρ-proxy on the 3 visible wells (SMALL). Pass = ρ<0.85 + positive nested blend
  weight + no worst-block regression. Kaggle GPU for the fork OOF; CPU for the ρ-proxy gate.
- **B3' Transductive structure from the FULL HIDDEN TEST batch (submission-time).** Genuinely new
  inference-time info: at scoring all hidden test wells are present; if the hidden test is spatially
  dense (pads), the batch jointly constrains a structural field the per-well model misses. Probe =
  (a) simulate a dense-batch field on the densest TRAIN clusters → beat DWT there? (b) ONE
  non-submitting Kaggle diagnostic logging hidden-test well count + nn-distance distribution.
- **B4' Single-submission GUARDED honest+overlap.** One slot that is DWT-honest by default and applies
  the exact-match override ONLY on hidden wells detected as high-confidence train duplicates — dominates
  the pure-honest slot on private if duplicates exist, without the pure-hedge novel-well downside. CPU +
  notebook; gated on the same host-rule confirmation as the hedge. Complements the separate-hedge plan.

---

## Update 2026-07-15 (after V1) — revised priorities
- **V1 outcome:** GR→formation is learnable (0.486 vs 0.282) but the predicted-marker features give a
  **negative** blend weight → the facies signal is already inside DWT. This **de-prioritizes the facies
  branch of N-A and all of S-B** (external labeled facies): the limiter is not label quantity but that
  facies is a GR-derived signal DWT already captures. Do not spend GPU on external facies unless V2
  (structural surfaces, a different signal) or a genuinely new signal shows positive-weight evidence.
- **Remaining actionable, evidence-supported priorities:**
  1. **V2** structural-surface predictability (the untested branch of N-A; surfaces are continuous
     structural depths, richer than categorical facies — check OOF R² + blend-weight sign). CPU.
  2. **V4 → S-A** decision-theoretic final-2 optimization — improves the deliverable (private rank)
     independent of the blend-neutral wall. CPU.
  3. **V5** visible-well pre-submit audit tool. CPU.
  4. **V3** stratified blend audit. CPU.
- **N-B / S-B (Kaggle GPU):** now gated specifically on **V2** showing a positive-weight structural
  signal (the facies route is closed by V1). If V2 is also negative, no GPU direction remains supported
  and the honest base stays DWT 9.519; effort shifts to S-A (submission strategy) as the deliverable
  lever.

## Update 2026-07-15 (after V2) — structural route closed on achievable evidence; effort → S-A
- **V2 outcome:** structural surfaces (`surf − Z`) are OOF-predictable (R² 0.59–0.78) and — as an
  **ORACLE** (true surfaces) — give the first stable **POSITIVE** nested blend weight (**+0.216**,
  10.39→10.14): the structural framework is the one channel carrying information DWT does not already
  hold. BUT the **ACHIEVABLE** path (OOF-PREDICTED surfaces from test-available inputs) is blend-neutral
  (**−0.020** ≈ base-only −0.021): any surface predictor is a function of the test-available inputs DWT
  already consumes, so predicted surfaces add nothing independent (Stage3 ≈ Stage0). The oracle signal
  lives in the train-only surface residual, unreachable at test.
- **Consequence for N-A / N-B:** both structural branches were gated on V2 showing an *achievable*
  positive-weight signal; V2's achievable weight is ≤ 0, so **N-A (predicted-framework features) and
  N-B (multi-task auxiliary structural heads) are NOT GPU-warranted** — N-B's auxiliary head is likewise
  a function of test-available inputs, predicted blend-neutral by the same redundancy argument. The
  facies branch was already closed by V1. → **no structural-label GPU direction is currently supported.**
- **Reusable finding:** an *oracle-positive but achievable-negative* result is a new ledger category —
  the independent signal provably exists (in train-only labels) yet is not a function of any
  test-available input, so no model on the current input set (however large) can capture it. This
  sharpens the "information ceiling": it is a *label-availability* ceiling, not a model-capacity one.
- **Remaining evidence-supported priorities (all CPU / deliverable):**
  1. **S-A** final-2 decision optimization — DONE (`reports/final2_decision_optimization_2026-07-15.md`):
     keep {DWT 9.519, Gate-Safe hedge 7.212} now; build B4′ (guarded honest+overlap on the DWT base) →
     {B4′, DWT} weakly dominates at every overlap fraction (gated on within-comp override compliance +
     V5 audit + detector precision).
  2. **V5** visible-well pre-submit audit tool — DONE (`scripts/visible_well_audit.py`); mandatory gate.
  3. **V3** stratified blend audit (CPU) — remaining untested small probe.
- Honest final base unchanged = DWT 9.519 (ref 54453597). The deliverable lever is now **S-A (build
  B4′)**, not a new honest model.
