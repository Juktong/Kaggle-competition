# ROGII — Hard-Won Lessons & Strategy (2026-07-08)

Consolidated understanding after a long multi-day push. Written so future sessions
do not repeat the same detours. **Read this before spending more effort or slots.**

## Working directives (persistent — read first)

Two standing instructions govern all work on this project (full text in the repo-root `CLAUDE.md`):

1. **Keep searching, systematically.** Not a one-shot attempt and never stop at "no method found":
   continuously propose candidate directions -> validate honestly (train masked-CV / OOF as the
   private-ranking proxy) -> record evidence -> drop unsupported hypotheses -> expand the search
   space. Prefer low-cost, honest, reproducible checks; scale up a promising small result before
   concluding; never treat an oracle (truth-selected) result as an achievable gain. If a candidate
   shows a clear reproducible honest OOF gain vs the DWT base (or a stable gain on a clear
   well-family via a guarded router) and passes the pre-submit audit, submit to Kaggle under the
   established conditions and record submission id / public score / commit / source / local gap.

2. **Neutral technical language.** Avoid emotional or strongly-directive words ("gamble", "dead",
   "give up", "ceiling"). Use: candidate direction, validation result, no stable improvement
   observed, insufficient current evidence, next search space, submittable conditions, risk points,
   locally applicable, needs further validation. Report a negative as "no stable OOF improvement
   observed on this attempt; moving to the next search space", not as a dead end.

## 0. TL;DR — the single most important thing

**Diagnose what actually moves the score BEFORE modeling.** Most of our wasted
effort came from optimizing an internal CV that does not predict the public board.
This competition has a split personality:

- **Public LB = a leakage/overlap game**, not a geology-model quality contest.
- **Private LB (final rank / prize) = honest-model quality on novel wells**, which
  we can only proxy with internal pseudo-hidden CV.
- **Our internal native-mask CV ≈ private-LB behavior; it is NOT ≈ public LB.**

## 1. The scoring mechanism (the crux we learned late)

- Code competition with hidden rerun. Downloadable `test/` has only 3 visible wells
  (000d7d20, 00bbac68, 00e12e8b); `sample_submission.csv` = 14,151 rows over those 3.
  At scoring, Kaggle swaps in the real hidden test wells; the notebook must
  dynamically discover wells. Static replay is rejected.
- **The 3 visible test wells are ALSO in `train/` with full ground-truth TVT** —
  a genuine answer leak. Metric = pooled RMSE over predicted toe-end rows.
- **The 7.10–7.30 public plateau is NOT a better model.** It is a decent
  correlation base + two board-specific layers: (a) a **guarded overlap/exact-match
  override** that reconstructs TVT for hidden wells that duplicate train wells, and
  (b) **gold visible-prefix calibration**. These help PUBLIC and are ~no-ops on
  PRIVATE (novel wells) → the plateau will shake down on private.
- **Overlap exploitation ceiling ≈ 7.27** (the teammate's affine-overlay line hit
  7.278/7.294; a naive exact-copy scored 11,551 — rejected). Our 7.182 stack
  already contains the overlap override, so stacking more overlap adds ~nothing.
- **Honest models land at board 8–14** — confirmed by every publicly-shared "real
  model" (8.099; DWT 9.251; 9.538; romantamrazov 9.956/10.811; pilkwang 12.049)
  AND by all of our from-scratch work (neural cross-attn **12.87**, domain-feature
  LightGBM/mycarta **14.09**, last_value/PF/router ~**14.7**). This is the "honest
  manifold."

## 2. What we tried and what it scored

| Approach | Internal CV | Board | Verdict |
| --- | --- | --- | --- |
| last_value baseline | 14.68 | — | floor |
| from-scratch router/PF/DTW/Viterbi | ~14.6–14.8 | — | all hit GR-aliasing wall; net ~baseline |
| feature-GBM (tortuosity/NCC/offset, ours) | ~16 | — | landed at baseline (missing per-row alignment + strong offset-well signal) |
| neural cross-attn aligner (ours) | 14.74 | **12.87** | first novel model on board; not competitive |
| mycarta domain-LightGBM fork | 14.78 | **14.09** | ran in fast/debug mode; honest, not competitive |
| our 7.182 physics-PF stack fork (pre-session) | — | **7.182** | our best; has overlap override |

Key negative results (do not re-try blindly):
- **GR↔typewell alignment is fundamentally aliased** (oscillatory, self-similar):
  PF/NCC/Viterbi/attention all rescue high-drift wells but lock onto wrong
  positions elsewhere; correct-vs-aliased large moves are indistinguishable at
  prediction time. Prefix hold-out does NOT predict hidden-suffix wins.
- **TVT is NOT ~−Z+c** (Z-projection RMSE 104 vs 15.7). Within a lateral the
  TVT-vs-Z slope ≈ 0 (mean +0.057) while global cross-well r = −0.96 → **TVT in the
  toe is set by formation dip in the bit azimuth (a cross-well structural quantity)**.
  → the #1 honest lever is an **offset-well multi-well structural/dip framework**,
  which we have not built well (our spatial KNN probe failed: wells too sparse,
  median neighbor ~1548 XY units — needs a real dip/structural surface, not KNN).
- Soft-DTW is a poor fit: wells UNDULATE (~24 direction reversals median) → the
  alignment is non-monotonic, so monotonic DTW is wrong.
- Neural scale-up (bigger/longer) OVERFIT (val 15.96 worse than the small 14.74);
  capacity is not the bottleneck. Add best-checkpoint restore + multi-cut
  augmentation if revisiting.

## 2b. Fork-run DISCIPLINE — smoke-test the fix on a tiny/cheap run first

**Never validate a fix by launching the full run.** These notebooks read
multi-GB feature tables (ravaghi `data/train.csv` = **7.4 GB**, ~1 h just to read)
and run optuna/PF for hours, so a bug at minute-80 costs an hour to surface. Each
DWT attempt burned ~1.4 h to hit the *next* error.

Instead, for every fork fix:
1. **Isolate the thing you fixed** into a minimal cell/kernel that exercises ONLY
   that code path (e.g. `load_trainer(one_model_dir)` + assert it has `.oof_preds`
   / `.models_`) — it mounts the dataset but does NOT read the 7.4 GB table, so it
   finishes in minutes.
2. If the smoke test passes, only THEN wire the fix into the full pipeline and run
   the slow/full version.
3. Add a `FAST`/`nrows`/`max_wells` toggle so the full notebook itself can run a
   cheap end-to-end pass. (Caveat: if the pipeline uses precomputed full-size OOF,
   you cannot simply subsample the train table — the OOF length won't align; smoke
   test the *loading* separately instead.)

This turns "1 h per failed guess" into "minutes per validated step."

### 2c. DWT honest base — SOLVED (the full recipe, confirmed 2026-07-08)

The DWT 9.251 fork now RUNS end-to-end and submits. Internal native-mask CV
(optuna post-proc best) = **10.40** — our honest private proxy (its 9.251 is the
*public* board; honest models' internal CV ≈ private, so ~10.4 is the realistic
private-side number). **Submitted → public board = 9.519** (sub 54453597), which
nearly reproduces the origin DWT 9.251 — we are ~0.27 worse only because ravaghi
published 5/6 trainers (no catboost-3). This is now our banked honest base:
public 9.519 / internal-CV 10.40, far above our from-scratch best (neural 12.87). Every failure above was one of THREE unrelated breakages,
each caught cheaply by a smoke kernel before any 1 h full run:

1. **koolbox dependency** (`from koolbox import Trainer`, private wheel we never
   had). The ravaghi artifacts are pickled `koolbox.Trainer` objects. Fix = graft
   a self-contained **`CVTrainer`** class + register it under `sys.modules` for
   `koolbox`, `koolbox.trainer`, `koolbox.trainer.trainer` so joblib unpickles it.
   `load_trainer(dir)` globs `*.pkl` and returns the object. The pickled trainer's
   model list lives in attribute **`estimators`** (5 fold models), NOT `models_`;
   `_models_for_predict()` tries known aliases and adapts. `.oof_preds` (len =
   3,783,989 = len(train_df)) and `.overall_score` come straight off the pickle;
   `.predict(X_test)` averages the 5 fold models (handles `best_iteration_`).
   Patch both `train_lightgbm`/`train_catboost` fast-load branches to:
   `_tr=load_trainer(path); oof=_tr.oof_preds; test=_tr.predict(X_test)` — this
   sidesteps the raw-Booster-vs-sklearn `best_iteration`/`best_iteration_` API gap.
2. **Wrong artifacts mount path.** Current Kaggle layout is
   `/kaggle/input/{competitions|datasets}/{owner}/{slug}`. Competition data =
   `/kaggle/input/competitions/rogii-wellbore-geology-prediction` (correct as-is);
   ravaghi artifacts = `/kaggle/input/datasets/ravaghi/wellbore-geology-prediction-artifacts`
   (NOT `/kaggle/input/wellbore-geology-prediction-artifacts`). A wrong path makes
   the `.exists()` fast-load guard False → notebook silently **retrains from
   scratch** (rebuilds the 7.3 GB train.csv into output AND hits the GPU params →
   `LightGBMError: No OpenCL device found`). Robust fix = auto-detect: glob
   `"/kaggle/input/**/models/lightgbm-1"`, pick the root that has BOTH
   `models/lightgbm-1` and `data/train.csv`, assert it, then `CFG.artifacts_path=`.
3. **Missing `catboost-3` artifact.** Ravaghi published only `lightgbm-1/2/3` +
   `catboost-1/2` (5 dirs, no cb-3). The `for i in range(3)` catboost loop would
   request cb-3 → not found → retrain branch. Fix = guard each loop iteration with
   `if not (CFG.artifacts_path/"models"/name).exists(): continue` (load-only mode).
   Also **strip GPU params** defensively (`device_type="gpu"`, `task_type="GPU"`)
   so any accidental retrain runs on CPU instead of crashing.

The generic lesson: a "path fix" that flips a fast-load guard to False fails
SILENTLY into a slow retrain — it doesn't error at the guard, it errors ~80 min
later deep in training. Always assert the fast-load path is actually taken (print
`Loading` vs `Training`; assert the artifact dir exists right after setting the
path).

### 2d. Honest levers TESTED and KILLED (2026-07-09/10) — do not retry

Ran the two candidate honest levers locally (system python3.12 has full pandas/
numpy/scipy/lightgbm; native TVT_input mask = hidden split). Both failed the
"beat DWT 9.519" gate → **not submitted** (0 slots burned; retreated to DWT).

- **Offset-well STRUCTURAL SURFACES (ANCC/ASTNU/ASTNL/EGFDU/EGFDL/BUDA).** In the
  masked toe of TRAIN these are ~100% populated (X/Y/Z too; GR only 36%), and a
  leave-well-out LightGBM on them predicts raw toe TVT at RMSE ~46 vs naive
  projection 107. BUT the **TEST horizontal wells do NOT carry these columns**
  (test cols = `MD,X,Y,Z,GR,TVT_input` only) → the feature literally cannot be
  computed at inference. Dead. (This is also why DWT's 195 features are GR/typewell/
  geometry-based, never surfaces.) Probe: `scratchpad/dip_probe.py`.
- **GR↔typewell DIP ALIGNMENT** (segment-NCC anchor-bounded warp, the "real"
  geosteering move). Honest native-mask weighted RMSE = **16.23**, actually WORSE
  than the trivial last_value baseline **16.16** (win-rate 0.36; prefix-holdout
  router-gate still nets +0.02; no drift-quartile shows gain). DWT's 195 GR
  features already subsume this. Proto: `scratchpad/tw_align_proto.py`.

Bottom line: no cheap honest lever beats DWT 9.519. The only remaining honest
upside is either (a) recover the missing **catboost-3** to lift DWT 9.519→~9.251
(bounded, low-risk, ~0.27), or (b) a multi-day rebuild of a GR aligner good enough
to out-feature a tuned 195-feature ensemble (low odds). See memory
`dwt-honest-base-9519.md`.

### 2e. catboost-3 RECOVERED — but the 0.27 public gap was NOT real quality (2026-07-10)

Trained the missing catboost-3 ourselves (kernel `joezzzzz/cb3-train`: single-GPU
`devices="0"` — the origin's `"0:1"` assumes 2 GPUs and errors on a 1-GPU kernel;
iterations cap 4000, 5-fold GroupKFold on `well`, ~16 min, individual OOF RMSE 10.55).
Saved as a `load_trainer`-compatible `CVTrainer` at `models/catboost-3/trainer.pkl`.
Main notebook v7 consumes it via `kernel_sources: ["joezzzzz/cb3-train"]` plus a new
`find_model_dir(name)` helper that globs each model dir under ANY `/kaggle/input`
root (ravaghi holds lgb1-3+cb1-2; the cb3-train output holds catboost-3). All 6
models load cleanly.

**Result: final optuna internal CV = 10.3987 vs 10.40 with 5 models — FLAT.** cb-3 is
highly correlated with the existing five, so it adds ~nothing to the honest proxy.
**Key finding:** the 0.27 public gap (origin 9.251 vs our 9.519) is NOT a real quality
difference — both sit at internal CV ~10.4; the 0.27 is public-split noise. Recovering
cb-3 therefore only lifts the PUBLIC vanity number, not the private proxy → **not
submitted** (gate = material CV gain; slots preserved). The 6-model notebook is banked
and ready if we ever want the marginal 5→6 variance reduction.

**Ensemble diversity — also tested and dead (2026-07-10).** The most GR-orthogonal
honest signal is a spatial-geology KNN on the `r=TVT+Z` field over `(X,Y)` of
neighbouring wells (`scratchpad_probes/tvt_spatial_probe.py`). Result: pooled RMSE
**178** vs last_value **15.65** — catastrophic; median neighbour distance ~1548 XY
units means the wells are too sparse for KNN, so it helps only ~18% of wells (those
with a close neighbour) and is unusable as a blend input. The only other orthogonal
candidate (the neural aligner, standalone CV 12.87) is far weaker than DWT 10.4 and
still ultimately GR-driven, so its blend weight/gain is negligible. Those honest levers (structural surfaces, GR dip alignment, catboost-3, spatial
diversity, neural diversity) all fail to move the private proxy.

### 2f. Post-proc "win" was CV-OVERFIT — DISPROVEN by public (2026-07-10)

A tempting lever, found by dumping DWT's OOF (kernel v9 saves `dwt_oof/ytrue/base/ids`;
train_df is TOE-only, 3.78M rows): DWT's `apply_pp` caps its residual scale `alpha≤1.0`,
but the OOF optimum is ~1.10 (DWT appears to under-predict drift), and heavy per-well
savgol (win=201) further cut OOF RMSE. Honest GroupKFold looked great: 10.3987 → 10.3445.

**Then public demolished it.** Three controlled submissions:

| config | public | CV |
|---|---|---|
| base: 5-model, smooth17, no λ (ref 54453597) | **9.519** | 10.40 |
| v12: 5-model, smooth201, λ1.10 | 9.839 | ~10.35 |
| v10: 6-model, smooth201, λ1.10 | 9.968 | 10.34 |
| v11: 6-model, smooth201, λ1.0 | 10.230 | ~10.39 |

Every local-CV "improvement" (cb-3, λ rescale, heavy smoothing) **improved held-out CV
but WORSENED real public**. The post-proc overfits train-well OOF idiosyncrasies and
does not transfer; λ only "helped" among the smooth201 variants by partly undoing the
over-shrinkage of heavy smoothing (coupled, not independent); cb-3 adds ~0.13 public
harm on top. **Definitive lesson for ROGII: held-out CV is MISLEADING for
post-processing / blend changes — the original DWT light post-proc (sg_smooth win=17,
no λ) is the robust optimum. Trust the honest PUBLIC score for post-proc, not CV.**
Everything reverted; the honest final is the 5-model DWT **9.519** (already banked,
ref 54453597). Net honest ceiling stays ~10.40 CV / 9.519 public; the stripped test set
provides no further honest signal we have found. See probe scripts
`scratchpad_probes/combo_*.py`.

## 3. Fork-ops reality (whack-a-mole — budget for it)

Competitive public notebooks are NOT portable. Each fork needs surgery:
- **GPU:** default P100 = compute sm_60, too old for Kaggle's preinstalled torch
  (`no kernel image`). Fix: `--accelerator NvidiaTeslaT4` / `machine_shape:
  NvidiaTeslaT4` (sm_75 works out of the box). LightGBM/CatBoost/numba are fine on
  P100 (torch is the only thing that breaks).
- **New-kernel 403:** when forking a pulled kernel, DELETE `id_no` from the
  metadata (it points to the origin kernel) — rebuild clean minimal metadata.
- **External module deps (crash on import):** koolbox (mycarta, takuya, kokinn,
  dualpipe, bern), hill_climbing/Climber (DWT). koolbox comes from the
  `phongnguyn23021656/koolbox-offline` dataset; Climber is a Caruana greedy
  ensemble (we wrote a self-contained stub — see scratch).
- **Hardcoded dataset paths:** DWT hardcodes `/kaggle/input/datasets/ravaghi/...`;
  real mount is `/kaggle/input/wellbore-geology-prediction-artifacts`.
- **Pretrained-artifact detection:** degnonguidi Pipeline B looks for models at
  `CFG.ARTIFACTS/models_B`; the fleongg models (`fleongg/rogii-claude-models-pub`:
  features.json + lgb0/1/2.pkl) sit at that dataset's ROOT, so B never finds them
  and **trains from scratch → ~11h feature build → DeadKernelError**. This killed
  the Degnonguidi 7.159 fork **8 times**; a glob patch did not resolve it →
  **ABANDONED degnonguidi** (heavy dual-pipeline, not worth more 11h runs).
- **Unsafe train→test TVT_input row copy** (`hw_te['TVT_input']=hw_tr[...].values`)
  in 7153/takuya/dualpipe/bern — public-only overlap trick; trivially removable but
  those notebooks are non-portable for other reasons (koolbox + heavy PF).
- **Runtime:** heavy PF/beam dual-pipelines run hours and risk the 9h limit /
  DeadKernel; prefer CPU-light notebooks (DWT) that use pretrained artifacts.

## 4. Strategic conclusion

- **Podium (5.26) / top-10 (6.30) is NOT reachable** with any public artifact or
  our from-scratch work — it uses a materially stronger structural/inverse model
  or private-invisible tricks not shared publicly.
- **Realistic public ceiling ≈ 7.08–7.13 (top-100)** via land-a-7.159 + blend, but
  **most of that reverts on private**.
- **For the FINAL/private ranking (the goal): build/land the strongest HONEST model
  and validate it on internal CV.** When the overlap-chasers shake down on private,
  a genuinely strong honest model (internal CV → 8–10) can rank durably well.
- The #1 honest lever = **offset-well structural/dip framework** (cross-well
  formation dip in the bit azimuth). Secondary honest levers: Q-3D tortuosity
  (−0.107 in mycarta), multi-scale NCC, self-correlation, PF/state-space engine.

## 5. Current assets / final-submission plan

Kaggle lets you pick **2 final submissions** — pick for PRIVATE robustness:
1. **The strongest honest model** — currently landing the **DWT 9.251** fork (clean,
   CPU, no overlap, honest → its board ≈ its private). If it runs, it is far better
   than our from-scratch ~14. Then improve it with the offset-well lever.
2. **A hedge** — the 7.182 stack (decent base + overlap; in case private is less
   overlap-punishing than expected). Do NOT pick two overlap-heavy notebooks.

## 6. If starting over (the efficient path)

1. Run the "what moves the score" diagnostic FIRST (public=overlap, private=honest,
   internal CV=private proxy). Decide public-chase vs private-durable up front.
2. For private: fork ONE clean honest base (DWT-class), get it running, measure its
   internal CV, then add the offset-well structural framework. Don't grind
   from-scratch alignment (aliasing wall) or heavy non-portable stacks.
3. Reserve slots; every submission is a planned experiment. Two finals = 1 honest
   + 1 hedge.

## 7. Deep honest-lever audit (2026-07-11) — error structure + geosteering, all rigorously tested

Worked entirely off the dumped DWT OOF `combo_state.npz` (oof/yt/base/well/ridx/cut,
773 wells) + the full local 773-well train set (`data/rogii/train`, all columns). Every
claim below is honest 5-fold GroupKFold nested-CV, not in-sample.

**Error structure (the map of where DWT loses).**
- Pooled toe RMSE = 10.3987 (= our "CV 10.40"). RMSE is dominated by the far-toe: 59% of
  rows sit at distance-from-anchor >2000 ft with RMSE 12.3; everything <500 ft is ~0 error.
- DWT's within-well error is **99.9% low-frequency (smooth), 0.1% noise** — not per-point
  jitter; each well's whole toe is systematically offset (a structural mis-pick).
- Oracle ceilings (perfect corrector): remove per-well **mean offset** → RMSE **6.30**
  (63% of SS); per-well **affine-in-distance** → **4.44** (82%). So most of the error is
  "recoverable structure" *in the oracle sense* (i.e. if you knew the truth).

**Residual-scale λ — a fragile distribution bet, not a robust lever.**
- Per-well far-field optimal scale: mean **1.003**, median 1.015, IQR [0.58, 1.44]; only 51%
  of wells want >1. The pooled optimum 1.096 is an RMSE-weighted artifact of a few high-drift
  wells. Honest nested-CV gain of global λ (and distance-gated λ, which adds nothing) is only
  **−0.047** (10.399→10.351).
- Correction to §2f: the three 2026-07-10 submissions that "disproved λ" all also changed
  savgol 17→201 and/or added cb3 — **confounded**. v11 (λ=1.0, smooth201) alone scored 10.230,
  so the public villain was heavy smoothing, not λ. The clean isolation (5-model, LAM=1.09,
  original smooth17, kernel v13) scored **public 10.138 vs base 9.519 = +0.62 WORSE** — so even
  cleanly isolated, λ genuinely HURTS real test. Native-mask CV said −0.047, public said +0.62:
  a huge divergence that DEFINITIVELY confirms "held-out CV is misleading for post-proc" here.
  Honest final = base 9.519, no λ, no extra post-proc. Do not retry residual scaling.

**Geosteering / typewell structural matching — rigorously DEAD (do not retry).**
- Built a real matcher: DP alignment of horizontal GR onto the typewell GR-vs-TVT profile,
  windowed-NCC emission, smoothness penalty, heel-TVT start pin, per-well confidence gate.
- Foundation is sound: horizontal GR matches typewell GR @ true TVT with **median corr 0.82**
  (98.7% of wells >0.5). So the signal physically exists.
- Yet honest nested-CV blend weight = **0 in all 5 folds and every confidence gate**. Reason:
  matcher error is **0.65–0.68 correlated** with DWT and 1.7× weaker (16–18 vs 10.3) — DWT's
  195 GR features already extract the typewell signal; the explicit matcher is a weaker
  re-derivation with no independent information. Closed-form: it would need strength ~13 (not
  17) to help at that correlation — unreachable by a hand-rolled matcher vs a tuned ensemble.
- **Test typewell carries only TVT + GR** (Geology and all structural surfaces are
  train-stripped). So there is **no independent input signal at test** beyond
  GR + typewell-GR + trajectory, all of which DWT consumes. This is an **information ceiling**.

**Verdict.** Post-processing DWT's own output can only tweak calibration (fragile, ~0.5%
coin-flip); no independent estimator built from the available inputs decorrelates enough to
help a blend. The honest frontier for this data IS the 5-model DWT **9.519 / CV 10.40**
(banked ref 54453597). Final-2 unchanged: DWT 9.519 (honest) + an overlap hedge.

## 8. Multi-hypothesis / selection lines (2026-07-11) — Joe's 3 ideas, all locally validated

All three got a genuine implementation + honest well-split validation on the local 773-well
train set vs the DWT OOF. NONE submitted to Kaggle (validate-first, by directive). The key
diagnostic for each is the ORACLE test: is a beat-DWT hypothesis even reachable?

| Line | idea | ORACLE ceiling | achievable | blend w* | verdict |
|---|---|---|---|---|---|
| 1 | misfit heatmap + top-K paths + learned selector | 10.29 (ties DWT 10.42) | selector 13.70 | ≈0 | capped |
| 2 | Siamese/CNN scorer + DP top-K | 10.20 (>DWT 9.70; beat NCC 10.38) | best-cost 15.8 | needs oracle | capped |
| 3 | MTP multi-hypothesis GRU (K heads, WTA loss) | 10.24 (ties DWT 10.00) | soft 15.5 / hard 16.4 | ≈0 | capped |

**Unifying result (triply confirmed across independent method families).** In every line the
ORACLE ceiling merely *ties* DWT — no alternative hypothesis systematically beats it — and
selection-from-inputs *fails* (all achievable selectors land 13–16 vs their ~10.2 oracle). Only
the *oracle* blend (which requires knowing the truth) captures the ~10% prize (8.7–9.1). So the
entire problem reduces to **selecting the correct stratigraphic interpretation**, and the
discriminating information is **not in the test-available inputs** (GR + typewell-GR +
trajectory) — which is precisely why DWT's dominant error is a whole-well toe offset (it picked
one interpretation and can't verify it). This is the same **information ceiling** as §7.

Notable sub-findings: (2) Joe's hunch was right — a learned scorer *does* beat raw NCC (oracle
10.38→10.20) — but not enough to clear DWT; the Siamese pos/neg window-similarity gap is only
~0.07, i.e. typewell GR at the true TVT vs ±6–45 ft off is genuinely near-identical
(cycle-skipping / repeated lithology). (3) the MTP heads collapse under selection (hard-select
16.4 is *worse* than the soft average 15.5), and corr-with-DWT rises with training (0.69→0.77).

**One untried selection lever (speculative):** known-tail validation — train MTP/paths from an
*earlier* anchor, leave a gap of the KNOWN section as a holdout, score each hypothesis on that
known-but-held-out tail (truth available there even at test), and use tail-fit to route. Only
worth it if known-tail accuracy predicts toe accuracy (uncertain — the toe is further
extrapolation). Verdict stands: honest final = DWT 9.519; the frontier for these inputs is real.

## 9. Round 2026-07-11(b) — offset-correction + per-family routing (local OOF)

Working notebook restored to the clean DWT 9.519 config (LAM removed; identical to
DWT_backup_preCb3, matches banked ref 54453597). Two low-cost local candidates, both
validated on honest 5-fold GroupKFold OOF over the 773-well DWT OOF:

- **Per-well offset-correction meta-model (Area 5/1).** Target = DWT per-well residual
  offset (mean over toe; the dominant error, std 7.9). Features: test-available only
  (well morphology, toe/heel GR stats, heel↔typewell matchability, prefix length,
  trajectory inclination/undulation, matcher-derived offset/confidence, DWT drift shape).
  Result: **OOF R² = −0.15** (corr 0.02); affine target also negative. Applying the
  correction *raises* pooled RMSE 10.40→10.91 (shrink ×0.25 still 10.43). No stable
  improvement observed. Read: the per-well offset is the interpretation-selection quantity
  and is not encoded in aggregate test-available features (consistent with §7–§8).
- **Guarded DWT+matcher router by well-family (Area 2).** Honest per-quintile OOF blend
  weight across heel-match / prefix-frac / drift-absmax / z-reversals / gr-toe-std /
  max-dist: **w̄ ≈ 0 in every family**. Globally only 13% of wells beat DWT by >1 RMSE and
  they are not family-identifiable. No guarded-router opportunity observed with this matcher.

Cumulative read of the local post-processing space (correcting/blending DWT's OOF): λ, offset,
affine, per-family routing all show no stable OOF improvement — because DWT's dominant error is
a per-well level/interpretation error not predictable from available aggregate signals. **Next
search space:** DWT-family model diversity (Area 1/3) — new sub-models within DWT's strong 195-
feature set (different loss/weighting/residual target) trained on Kaggle, validated on internal
CV via the climber before any submission. Higher cost, uncertain payoff, but the untapped space.
Artifacts: build_feats.py, well_feats.csv, experiment_c.py in $CLAUDE_JOB_DIR/tmp.

## 10. Round 2026-07-11(c) — ensemble diversity from the same inputs (local OOF)

- **From-scratch tabular drift GBM (Area 3), 16 engineered test-available features, honest
  5-fold OOF.** RMSE 11.40 (weaker than DWT 10.40) and **corr(err,DWT)=0.906**; nested blend
  10.40 (no change). Quantified structural point: a *stronger* same-input model converges toward
  DWT (corr→0.9), while the decorrelated candidates (matcher 0.65, MTP 0.77) are decorrelated only
  because they are weaker. No strong-and-decorrelated point on this frontier.
- **Loss diversity (Area 1), same features, {l2, huber, mae, quantile}.** Only Huber shows a
  nested-OOF blend gain (10.40→10.35, ≈−0.05); l2/mae/quantile flat; the 4-way lstsq stack (10.378)
  is worse than Huber-alone (overfits correlated predictors). **Robustness check flagged it as a
  residual-rescaling artifact, not diversity:** the blend weight is *negative* (w̄≈−0.10) and stays
  negative across 3 fold-seeds AND without the DWT-drift feature (w̄=−0.094). Mechanism: Huber's
  robust loss under-predicts tail drift, so the negative-weight blend (~1.1·DWT − 0.1·Huber)
  amplifies DWT's drift — i.e. the same λ≈1.09 residual-scaling that was cleanly disproven on public
  (§7: clean λ scored public 10.138, +0.62 vs 9.519). Set aside on risk-reward; also dis-justifies a
  Kaggle DWT-family Huber retrain (would recreate the rescaling at larger magnitude).

Round read: the "second honest model from the same inputs" space is characterized — candidates are
either correlated (~0.9, flat blend) or differ only via a disguised drift-rescaling that public
already rejected. **Next search space:** honest-base review (Area 6) — assess whether any genuinely
*honest* (non-overlap) public method scores below 9.519 (our notes reference an 8.099-class "real
model"), via local honest validation and an explicit overlap-vs-honest classification, without
chasing the public board. Artifacts: local_gbm.py, robust_check.py, lgbm_feats.npz in scratch.

## 11. Round 2026-07-11(d) — known-tail routing + the blend-neutral frontier

- **Known-tail leak-free routing (Directive dir.1).** Held out a slice of the KNOWN region
  (rows before the cut; truth available at test) as a leak-free validation tail; ran the matcher
  there and asked whether known-tail reliability predicts toe reliability. Result:
  corr(known-tail RMSE, toe RMSE)=0.19; corr(known-tail skill, DWT−matcher toe advantage)=**0.03**.
  Top-25% known-tail-skill wells: matcher-beats-DWT only 17%→20%, matcher still 13.5 vs DWT 8.0.
  Near-cut reliability does not transfer to the far toe (consistent with the older "prefix hold-out
  doesn't predict hidden-suffix" note). No stable routing signal observed.
- **Geometry-only drift GBM (new information channel, no GR).** RMSE 14.15, corr(err,DWT)=**0.717**
  — genuinely more decorrelated than the GR-GBM (0.906), i.e. position/geometry is a different
  channel — but too weak; nested blend 10.41 (flat).
- **The blend-neutral frontier (quantitative characterization).** Across ALL same-input candidates
  the error-correlation sits almost exactly on ρ ≈ σ_DWT/σ_candidate (matcher 17.0/0.61 vs 0.65;
  MTP 15.5/0.67 vs 0.77; geom 14.15/0.735 vs 0.717; GR-GBM 11.4/0.912 vs 0.906). That is precisely
  the w*=0 condition (σ_D²=ρσ_Dσ_M). It means every candidate behaves as **"DWT + independent
  noise"** — it carries no information independent of DWT, so no blend improves regardless of the
  candidate's strength. This is the quantitative signature that DWT is at the information frontier
  for the available test-time inputs.

Implication: a blend-based improvement requires a model built on information DWT does NOT use.
The only such candidate space is **transductive cross-test-well structure** (jointly using the
whole test batch's known heels + trajectories), which (a) introduces genuinely new inference-time
information and (b) cannot be validated on the 3 visible local test wells; the train wells are
spatially sparse (median neighbour ~1548 units; earlier spatial-KNN RMSE 178). Artifacts:
known_tail.py, known_tail.csv, geom_gbm.py in scratch.

## 12. Round 2026-07-14 — transductive cross-well field + final-2 strategy

- **Transductive cross-well structural field (test-time-visible inputs only; no leakage).** Built a
  KDTree structural field from OTHER wells' visible logs (other-fold full TVT as train reference +
  held-out well's own known heel), queried at each held-out toe point; validated honestly with
  train-as-pseudo-batch GroupKFold. Nearest field sample is median **380 units** away. Result:
  geometry-only OOF 15.94 (corr 0.663); geometry+field 16.22 (corr 0.666) — the field adds nothing;
  field-only 17.08 with nested-blend −0.028 (noise). Both on the blend-neutral line. The spatial
  field is uninformative for the far toe (structure changes over the ~380-unit sampling gap). This
  is the honest, locally-validatable version of the transductive idea — no stable improvement observed.
- **Final-2 strategy** documented separately in `reports/final_submission_strategy.md`: honest
  primary = DWT 9.519 (ref 54453597); public-hedge = Plane Top2 Gate Safe 7.212 (ref 54289934),
  kept strictly separate and labeled as overlap/public (not honest). Both refs banked & selectable.

Input-channel coverage note: the complete test-available input set is {horizontal GR, typewell
GR/TVT, trajectory X/Y/Z/MD, known-heel TVT, cross-well spatial}. Every channel has now been tested
as a model or blend candidate; each is either already extracted by DWT (→ blend-neutral) or
uninformative (spatial). Geology / structural surfaces are train-only (unavailable at test).

- **Uncertainty / risk-flag (item 6).** Tested whether a test-available signal ranks per-well DWT
  error: model disagreement (DWT vs matcher) corr 0.16; drift magnitude corr 0.21 (best), Spearman
  0.20; heel-match −0.06. Top-quintile-by-drift wells average error 10.0 vs overall 8.0. So a usable
  per-well confidence/risk flag exists (mainly = far-reach/high-drift wells), but it only identifies
  higher-error wells — it does not reduce error and is not actionable for RMSE on its own. Retain as
  a diagnostic; could weight a per-well guard only if a genuinely better alternative model existed
  for those wells (none observed so far).

## 13. Round 2026-07-14(b) — 5 small + 5 big directions, each with a minimal viable probe

All honest OOF / no-leakage; category and test-time availability noted. None submitted (none met the
submittable bar). Scripts: probes_A/B/C/D.py in scratch.

### Small directions (local, low-cost)
| # | hypothesis | inputs test-time? | validation | result | submittable | risk |
|---|---|---|---|---|---|---|
| S1 | DWT residual SHAPE (offset/slope/curv) predictable from visible feats | yes | 5-fold OOF R² | R² −0.10 / −0.13 / −0.09 (all neg) | no | — |
| S2 | monotonic/smoothness constraint on DWT drift | yes (no-leak) | all-well RMSE | isotonic 11.01 (worse), savgol31 10.397 (flat) | no | undulating wells break monotonicity |
| S3 | trajectory-cluster (dogleg/MD-len/heel-geom) routing DWT+matcher | yes | per-cluster honest OOF blend | w̄=0 in all 5 clusters | no | — |
| S4 | public-hedge downside audit vs honest DWT | hedge=public/overlap | visible(overlap) wells + format audit | hedge 1.46 vs DWT 7.23 on overlap wells; format/finite/range OK | (hedge only) | novel-well downside NOT locally measurable |
| S5 | heel-continuity re-centering correction | yes (no-leak) | corr(rate-mismatch, offset) | 0.686 (DWT continues heel) but mismatch↔offset corr −0.06 | no | mismatch uninformative about error |

### Big directions (new frameworks / feasibility probes)
| # | hypothesis | inputs test-time? | validation | result | submittable | risk |
|---|---|---|---|---|---|---|
| B1 | conformal calibrated intervals for final-selection/risk | yes | per-distance-bin coverage | 90%→90.0%, 50%→50.0%, half-width 11.3 — **calibration works** | (diagnostic) | not an RMSE gain; irreducible width large |
| B2 | retrieval-based analog well library (GR-similarity, no-leak) | yes | OOF blend | RMSE 16.7, corr 0.715, blend weight **negative** (−0.08..−0.14) = λ-disguise drift-amplification | no | public-rejected mechanism |
| B3 | mixture-of-experts {DWT,anchor,matcher}+reject, gated | yes | nested-CV pooled RMSE | oracle best-of-3 available ~8% (per-well), gate 76.5% acc, but gated pooled 10.57 > DWT 10.40 | no | asymmetric misroute cost dominates pooled |
| B4 | counterfactual failure-classifier (predict DWT-fail wells) | yes | OOF AUC | AUC 0.573 (weak) | (diagnostic) | too weak to route on |
| B6 | physics dip-REVERSION residual process (heel-calibrated) | yes (no-leak) | OOF blend | best L=200, RMSE 16.0, corr 0.692, blend 10.42 (flat/worse) | no | sits on blend-neutral line |

Round read: two working diagnostics (B1 conformal calibration; B4 weak failure signal) and one hedge
characterization (S4 quantifies the overlap benefit + documents the unmeasurable novel-well downside).
No direction produced a stable honest RMSE improvement over DWT 9.519; every model/blend candidate
again landed on the blend-neutral frontier or resolved to the public-rejected drift-rescaling artifact
(negative blend weight). B1's calibrated-uncertainty framework is retained for the final-selection/risk
layer (see final_submission_strategy.md), not as an RMSE lever.

## 14. Round 2026-07-14(c) — 7 public-research-inspired directions (A–G)

Full write-up in `reports/direction_search_public_research_2026-07-14.md`; scripts in
`scratchpad_probes/` (domain_validation_probe, ssl_gr_embedding_probe, facies_token_alignment_probe,
bayesian_state_space_probe, spectral_soft_alignment_probe, synthetic_selector_probe). All honest OOF /
masked-CV; none submitted (none met the submittable bar). Directions: A prediction-domain/adversarial
validation + GroupDRO; B ROCKET random-conv representation; C facies-token alignment; D Bayesian
particle-smoother posterior; E multi-scale spectral alignment; F external-data compliance audit;
G synthetic-selector.

Two reusable findings: (1) **DWT is domain-robust** — worst spatial-block RMSE (11.22) ≈ worst
random-fold (11.37) despite adversarial covariate-shift AUC 0.927, so the internal native-mask CV
(~10.40) is a sound private proxy. (2) **The path/interpretation-selection problem is not identifiable
from the current features even with unlimited clean synthetic labels** (synthetic selector 16.32 >
best-cost 14.75) — this makes all prior selector/router/MoE negatives intrinsic, not tuning issues.
Every model/blend candidate again landed on the blend-neutral frontier or the negative-blend-weight
drift-rescaling (λ-disguise, public-rejected). Reusable screen: reject any "OOF gain" whose nested
blend weight vs DWT is negative. No GPU full-run justified (all probes CPU-bound); the only
GPU-worthy avenue (external-data SSL encoder, dir F) is gated on manual Kaggle-rule verification +
a domain-relevant offline resource. honest final base unchanged = DWT 9.519 (ref 54453597).

## 15. Round 2026-07-15 — Direction F (external data / SSL-facies encoder), compliance + preflight

Full write-up: `reports/external_data_ssl_direction_2026-07-15.md`; preflight script
`scratchpad_probes/ssl_gr_encoder_preflight.py`.
- **Compliance:** standard Kaggle framework allows freely/publicly-available external data + pretrained
  models in code comps unless Host-prohibited; the **ROGII-specific clause needs manual confirmation**
  (rules page JS/auth-gated). Submission runs offline (`enable_internet:false`) → external data must be a
  public Kaggle Dataset. FORCE-2020 (GR present; NLOD-2.0 / CC-BY-4.0; Zenodo/GitHub) is the clean,
  offline-packageable candidate; Volve is CC-BY-NC-SA (compliance-risky); WLFM/ViT-MAE weights unconfirmed.
- **Decisive local preflight:** a *learned* self-supervised contrastive GR encoder (InfoNCE) on ROGII GR
  gives residual RMSE 15.95 / corr(err,DWT) 0.723 / **nested blend weight −0.096** — essentially identical
  to the untrained ROCKET random-conv probe (15.96 / 0.721 / −0.093). **GR-representation quality is
  irrelevant**: random or learned, the embedding-residual lands on the blend-neutral frontier with a
  negative (λ-disguise) blend weight. The bottleneck is informational (GR is one channel DWT saturates),
  not representational.
- **Verdict:** external-data + Kaggle-GPU is **not warranted now** — the smoke's local-acceptance criterion
  (positive-weight blend) is already failed by the ROGII-only encoder, and external data only changes the
  training corpus, not the informational limit. Smoke design + kernel-metadata template are documented for
  readiness (gated). No GPU run, no submission. Reusable rule reinforced: reject any residual/blend whose
  nested blend weight vs DWT is negative (drift-amplification, public-rejected). honest base unchanged = 9.519.

## 15. Next search space (2026-07-15) — see `reports/next_direction_backlog_2026-07-15.md`

F external-data **SSL-branch preflight** (learned contrastive GR encoder on ROGII): RMSE 15.95, corr
0.723, blend weight **−0.096** — same negative-weight pattern as ROCKET. Representation quality is not
the limiter; the GR channel is saturated by DWT → external-data **SSL** pretraining is not
GPU-warranted. The remaining external lever is **labeled facies** (different signal), gated on a
GR→facies foundation check. New backlog (9 candidates): BIG N-A predicted structural framework
(supervised facies markers + structural surfaces as predicted features, compliant), N-B multi-task
DWT-family retrain with structural-auxiliary heads (Kaggle GPU, gated), S-A decision-theoretic final-2
optimization (CPU, improves the deliverable), S-B external FORCE-2020 labeled-facies encoder (Kaggle
GPU, gated on rule + N-A); SMALL V1 marker-predictability gate, V2 structural-surface predictability,
V3 stratified blend audit, V4 submission-level honest-model diversity, V5 visible-well pre-submit audit
tool. Recommended first: V1+V2 (labeled-info foundation), V4→S-A (deliverable), V5 (audit tool). No GPU
until V1/V2 show positive labeled-info signal and (for S-B) the external-data rule is manually confirmed.
Scripts: scratchpad_probes/ssl_gr_encoder_preflight.py, marker_predictability_probe.py.

## 16. Round 2026-07-15(b) — V2 structural surfaces (oracle-positive, achievable-negative) + S-A + V5

Full write-ups: `reports/v2_structural_surface_probe_2026-07-15.md`,
`reports/final2_decision_optimization_2026-07-15.md`. Scripts:
`scratchpad_probes/structural_surface_probe.py`, `scripts/final2_decision_analysis.py`,
`scripts/visible_well_audit.py`. No process/GPU running this round (CPU-only box, 2 cores); no Kaggle
submission (no achievable honest OOF improvement met the submittable bar).

- **V2 — structural-surface predictability (the last untested branch of N-A).** Treated the 6 train-only
  surfaces (ANCC/ASTNU/ASTNL/EGFDU/EGFDL/BUDA) as *predicted* auxiliary features, compliantly: surfaces
  train the predictor; all predictor + downstream features are test-available (GR windows, trajectory,
  distance-from-cut, known-heel anchor, typewell GR); downstream TVT-residual model consumes the
  predictor's OOF. Target = `surf − Z` (Z-detrended structural offset; Z & surfaces share the elevation
  frame, TVT does not). Results (773 wells, 5-fold well-OOF, DWT OOF 10.393):
  - **Foundation PASSES** — all 6 surfaces OOF-predictable, R² **+0.59 .. +0.78** (RMSE ~28–30 ft).
  - **ORACLE (true surf−Z as features, diagnostic/not achievable): blend weight +0.216**, stable across
    all 5 folds (+0.20..+0.23), corr(err,DWT) 0.731→0.613, nested CV **10.393→10.140 (−0.25)**. This is
    the **first oracle in the entire search to BEAT rather than tie DWT** (§8 oracles only tied) — the
    structural framework is the one channel carrying information DWT does not already hold.
  - **ACHIEVABLE (OOF-predicted surf−Z): blend weight −0.020** = base-only (−0.021), corr 0.735 →
    blend-neutral. **V2 STOP.** A partial-oracle precision sweep shows the weight turns positive only
    around surf-RMSE **≈14–20 ft** (≈2× better than the achievable ~29 ft) AND only when the accuracy
    comes from genuine true-surface info, not the base features.
  - **Why:** a surface predictor is a deterministic function `h(BASE)` of the test-available inputs, so
    `BASE + pred_surf` is redundant with `BASE` (Stage3 ≈ Stage0). The oracle's independent signal is
    the train-only surface residual orthogonal to the inputs — unreachable at test. **This closes N-A
    (predicted-framework features) AND N-B (auxiliary structural heads) for GPU:** N-B's auxiliary head
    is likewise a function of test-available inputs → blend-neutral by the same argument. **No
    structural-label GPU direction is warranted.**
  - **New reusable ledger category — *oracle-positive but achievable-negative*:** the independent signal
    provably exists (in train-only labels) yet is not a function of any test-available input, so no model
    on the current input set (any capacity) can capture it. This upgrades the "information ceiling" to a
    precise **label-availability ceiling** — the one channel with genuine independent info (structure) is
    train-only and not reconstructable from the test inputs DWT already saturates.

- **S-A — decision-theoretic final-2 optimization** (`scripts/final2_decision_analysis.py`). Modeled each
  submission's pooled private RMSE `= sqrt(f·r_overlap² + (1−f)·r_novel²)` under a prior on the private
  overlap fraction `f`, with Kaggle's **best-of-2** private rule → `final(pair,f)=min` over the pair.
  Findings: under best-of-2 a hedge is a **free option** (never hurts), so `{DWT, Gate-Safe hedge}`
  weakly dominates `{DWT, honest2}` (honest2 is blend-neutral, adds ~0) and `{hedge, hedge}` (worst-case
  worse). A **guarded honest+overlap submission built on the DWT base (B4′)** — DWT on novel wells +
  exact-match override only on detected train-duplicates — dominates the separate weak-base hedge at
  every `f`; pairing it with pure DWT makes the DWT slot a safety net that absorbs B4′'s false-positive
  risk, so **`{B4′, DWT}` weakly dominates the current `{DWT, hedge}` pair pointwise** (max advantage
  ~1.28 RMSE at intermediate `f`). **Recommendation:** keep `{DWT 9.519 (54453597), Gate-Safe 7.212
  (54289934)}` if no new work; **build B4′** (gated on within-comp override compliance + V5 audit +
  detector precision) and switch slot-2 to `{B4′, DWT}` — the evidence-supported deliverable lever.

- **V5 — visible-well pre-submit audit tool** (`scripts/visible_well_audit.py`, reusable mandatory gate).
  Checks format/row-order vs sample_submission, finiteness, sane range, diff-vs-DWT, and RMSE on the 3
  visible test wells (which are in train with truth). Validated end-to-end: the DWT OOF scores **pooled
  7.23** on the 3 visible wells (000d7d20 3.63 / 00bbac68 9.04 / 00e12e8b 6.78 — these wells are
  easier-than-average vs the 10.40 full CV, useful calibration); hard checks correctly FAIL (exit 1) on
  a NaN/out-of-range submission. Usage: `python3 scripts/visible_well_audit.py --candidate sub.csv
  [--baseline dwt_sub.csv]`.

**Round read.** V2 is the most informative negative to date: it *localizes* the honest-frontier limit to
**label availability** (structure is the one independent channel, and it is train-only), not model
capacity or representation — reinforcing that no GPU model on the current test-available inputs clears the
blend-neutral wall. Effort now concentrates on the **deliverable (S-A / B4′)** rather than a new honest
model. Honest base unchanged = DWT **9.519** (ref 54453597). Next untested CPU probe: V3 stratified blend
audit.
