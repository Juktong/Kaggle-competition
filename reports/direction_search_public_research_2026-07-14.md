# ROGII — public-research-inspired direction search (2026-07-14)

Seven big directions (A–G) inspired by public geoscience/ML research. Each gets a minimal runnable
probe; scripts in `scratchpad_probes/`. Baseline = honest DWT (public 9.519 / internal native-mask
CV ~10.40, ref 54453597). Neutral technical language; honest OOF / masked-CV only; public-hedge kept
separate. Per-direction log: hypothesis / test-time-input compliance / script / validation design /
OOF numbers (RMSE, corr(err,DWT), blend weight or pooled) / submittable? / next.

Note on our recurring diagnostic: a candidate whose nested blend weight vs DWT is **negative** is a
disguised drift-rescaling (the λ mechanism already disproven on public, +0.62); such "gains" are
excluded, not submitted.

## Summary table (filled as probes complete)
| dir | probe | RMSE | DWT (same split) | corr(err,DWT) | blend w | submittable | next |
|---|---|---|---|---|---|---|---|

## A — Prediction-domain validation + robust selection  `scratchpad_probes/domain_validation_probe.py`
- **Hypothesis:** spatial/domain-blocked folds are a stricter private proxy than random GroupKFold; a robust/DRO-reweighted auxiliary may help the worst domain.
- **Test-time inputs:** compliant (XY centroid, GR/typewell/trajectory stats). No train-only fields.
- **Validation:** 6 spatial KMeans-XY blocks vs 6 random folds; adversarial block-vs-rest classifier; loss-diversity {l2,huber} + GroupDRO-lite reweighting, evaluated pooled AND worst-block; blend-weight sign check.
- **Results:** DWT worst spatial block **11.22** vs worst random fold **11.37** (spread 1.52 vs 1.62) — DWT is **domain-robust**, so the random-CV proxy (10.40) is validated. Adversarial AUC **0.927** (strong covariate shift by region: tw_gr_std/cut_md/incl/gr_heel) yet DWT error stable across it. Auxiliary: l2 blendW +0.061 pooled-blend 10.414 (no gain); huber & huber+DRO pooled-blend 10.343/10.340 but blend weight **negative (−0.18/−0.20)** = disguised drift-amplification (λ), worst-block 11.22→11.09 via that public-rejected mechanism.
- **Submittable:** No — no positive-weight (genuine) improvement; huber gain is the λ artifact. **Value = validation finding** (CV≈private is robust to spatial shift).
- **Next:** retain spatial-blocked worst-group metric as an additional guard when screening future candidates.

## B — Self-supervised / random-conv (ROCKET) GR representation → residual model  `scratchpad_probes/ssl_gr_embedding_probe.py`
- **Hypothesis:** a richer learned/random multi-scale GR representation captures shape DWT's 195 features miss → stronger or decorrelated residual.
- **Test-time inputs:** compliant (GR only). Not raw NCC/matcher.
- **Validation:** 48 ROCKET random-conv kernels, per-row PPV pooling → residual LightGBM, 5-fold well-OOF; RMSE, corr(err,DWT), nested blend weight sign.
- **Results:** RMSE **15.96** (weaker than DWT 10.40), corr(err,DWT) **0.721**, mean blend weight **−0.093 (negative)** → drift-amplification artifact, nested-blend 10.36.
- **Submittable:** No — weaker and the blend resolves to the public-rejected drift-rescaling (on blend-neutral frontier). Records blend-neutral evidence for a rich representation.
- **Next:** a full SSL encoder (TS2Vec/contrastive) is unlikely to escape the blend-neutral frontier given random-conv already sits on it; not prioritized without new information.

## F — External public well-log data / pretrained model — compliance audit  (audit only, no experiment)
- **Hypothesis:** public well-log corpora (FORCE-2020, Volve/Equinor) or well-log foundation-model weights could pretrain a facies/token/SSL encoder used only on comp inputs.
- **Compliance audit:** the live Kaggle rules page is JS/auth-gated (not machine-fetchable here) — exact external-data clause **must be verified manually** before use. Verifiable constraints from our own artifacts: the ROGII submission notebook runs with **`enable_internet:false`** (offline) → any external data/weights must be added as a **Kaggle dataset**, not fetched at runtime. Candidate public resources (licenses to confirm): FORCE-2020 lithofacies (Norwegian North Sea, open), Volve/Equinor logs (Equinor open data license), public well-log benchmarks; WLFM-style pretrained weights (availability/license uncertain).
- **Risk points:** (1) exact ROGII external-data rule unverified; (2) offline runtime → dataset-only; (3) **domain gap** — FORCE/Volve are different basins/tools/curves than ROGII (GR + typewell only), transfer uncertain; (4) license/attribution must be checked per source.
- **Submittable:** No experiment run — gated on manual rule verification + a compliant, offline-loadable, domain-relevant resource. Deliverable = this resource/risk list.
- **Next:** if Joe confirms the external-data rule allows it, start with FORCE-2020 GR-only facies pretraining as a diagnostic encoder (not a direct predictor), validated on real OOF.

## E — Multi-resolution spectral/trend alignment, top-K  `scratchpad_probes/spectral_soft_alignment_probe.py`
- **Hypothesis:** aligning in a multi-scale trend/band space (3 smoothing scales + local slope) is more robust to cycle-skipping than raw-GR NCC; oracle best-of-K may beat DWT (raw-GR oracle only tied).
- **Test-time inputs:** compliant (GR + typewell GR). Non-monotonic paths allowed via smoothness DP.
- **Validation (130 wells):** cost = squared multi-scale feature distance; DP top-8 diverse paths; oracle best-of-K vs DWT.
- **Results:** DWT **9.73**, best-cost path 27.67, **ORACLE best-of-8 = 16.05** — worse than DWT AND worse than the raw-GR oracle (~ties). The multi-scale feature emission matches worse than raw-GR.
- **Submittable:** No — oracle ceiling does not beat DWT (fails acceptance). Do not scale this emission.
- **Next:** none for this representation; the raw-GR oracle-tie was already the stronger alignment.

## C — Latent facies/stratigraphic TOKEN sequence alignment  `scratchpad_probes/facies_token_alignment_probe.py`
- **Hypothesis:** tokenizing GR into facies states (MiniBatchKMeans on [GR, grad, rolling-std, smooth]) before alignment is more robust to repeated lithology than raw-GR NCC; token-oracle may beat DWT.
- **Test-time inputs:** compliant (GR + typewell GR). Compute: **CPU probe**.
- **Validation (130 wells):** 12-token facies; emission = token mismatch + soft centroid distance; DP top-8; oracle best-of-K vs DWT.
- **Results:** DWT **9.734**, ORACLE best-of-8 (token) **10.547** — does not beat DWT (comparable to the raw-GR oracle tie; much better than the spectral emission's 16.05).
- **Submittable:** No — oracle ceiling does not beat DWT. Tokenization neither beats nor materially decorrelates vs raw-GR alignment.
- **Next:** none; token alignment sits at the same oracle-tie as raw GR.

## G — Synthetic geomodel / domain-randomized selector  `scratchpad_probes/synthetic_selector_probe.py`
- **Hypothesis:** the selection bottleneck (which candidate path is truth-like) can be learned from UNLIMITED synthetic wells with known truth, then transfer to real.
- **Test-time inputs:** compliant at apply time (path-features from GR/typewell). Compute: **CPU probe**.
- **Validation:** generate synthetic stratigraphy + trajectory (dip/curv/jump/noise) → K DP candidate paths + truth label; train LightGBM selector on synthetic; (G1) synthetic held-out selection; (G2) transfer to 60 real wells.
- **Results:** G1 synthetic held-out — selector-path **16.32** is *worse* than best-cost **14.75** (oracle 8.41): the selector does **not** beat best-cost even on clean synthetic data. Decisive finding: the truth-path is **not identifiable from path-features even with unlimited clean labels** — the selection problem is intrinsic, not a data-quantity problem. (G2 real numbers RMSE~688 are an artifact of a crude real-path generator, not valid; G1 is the finding.)
- **Submittable:** No. Explains prior selector/router/MoE failures (line1 selector, B3 gate) as intrinsic non-identifiability.
- **Next:** none for feature-based path selection; would need a fundamentally different discriminating signal (not available in current features).

## D — Bayesian/state-space structural POSTERIOR (particle smoother)  `scratchpad_probes/bayesian_state_space_probe.py`
- **Hypothesis:** a particle-smoother posterior (state = TVT/dip/curvature/jump; obs = GR-vs-typewell + trajectory smoothness) provides posterior mean + calibrated uncertainty carrying info DWT misses; uncertainty may beat the B4 failure classifier.
- **Test-time inputs:** compliant (GR + typewell + known-heel TVT + trajectory). Compute: **CPU probe** (160 particles).
- **Validation (120 wells):** posterior-mean RMSE / corr / blend-weight sign vs DWT; posterior-std AUC for predicting above-median DWT error vs B4 (0.573).
- **Results:** DWT **9.703**, PF-posterior-mean **31.59** (diverges under long-toe GR aliasing), corr(err,DWT) 0.316, blend weight ≈0 (−0.003); posterior-uncertainty failure AUC **0.546 < B4 0.573**.
- **Submittable:** No — posterior mean far weaker; uncertainty not better than the simpler B4 flag.
- **Next:** a stronger observation model would just re-derive the same GR-aliased signal; not prioritized.

## Round summary table
| dir | probe | key metric | DWT (same split) | corr(err,DWT) | blend w | submittable | GPU assessment |
|---|---|---|---|---|---|---|---|
| A | domain-blocked validation + DRO | worst-block 11.22 (≈random 11.37); adv-AUC 0.927 | 10.40 | l2 0.897 | l2 +0.06 / huber −0.18 | no (huber=λ artifact) | CPU probe |
| B | ROCKET random-conv repr → residual | RMSE 15.96 | 10.40 | 0.721 | −0.093 | no | CPU probe (GPU SSL not worth vs blend-neutral) |
| C | facies-token alignment oracle | oracle 10.55 | 9.73 | — | — | no (ties DWT) | CPU probe |
| D | Bayesian PF posterior | mean 31.59; unc-AUC 0.546 | 9.70 | 0.316 | −0.003 | no | CPU probe |
| E | spectral/trend alignment oracle | oracle 16.05 | 9.73 | — | — | no (worse) | CPU probe |
| F | external-data compliance audit | offline runtime; rule unverified; domain gap | — | — | — | no (audit only) | Kaggle GPU candidate IF rule allows + domain-relevant |
| G | synthetic-selector | synth sel 16.32 > best-cost 14.75 | — | — | — | no (selection non-identifiable) | CPU probe |

## Round conclusion (2026-07-14 public-research directions)
No direction produced a stable honest OOF/masked-CV improvement over DWT 9.519; no Kaggle submission
made (none met the submittable bar). Two reusable findings this round: (1) **DWT is domain-robust** —
worst spatial-block RMSE ≈ worst random-fold, so the internal CV (~10.40) is a sound private proxy
despite strong regional covariate shift (adv-AUC 0.927); (2) **the path/interpretation-selection
problem is not identifiable from current features even with unlimited clean synthetic labels** (G1),
which explains all prior selector/router/MoE negatives as intrinsic, not tuning. Every model/blend
candidate again resolved to the blend-neutral frontier or the negative-weight drift-rescaling
(λ-disguise) mechanism already disproven on public. Retained diagnostics: B1 conformal calibration
(prior round) for the final-selection/risk layer. No GPU full-run is currently justified — all probes
are CPU-bound (DP/PF/sklearn); the only GPU-worthy direction (F external-data SSL encoder) is gated on
manual rule verification + a domain-relevant offline resource. Moving to the next search space.
