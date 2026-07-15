# ROGII — V2: structural-surface predictability probe (2026-07-15)

Foundation gate for BIG N-A / N-B (the structural-label lever). Asks whether the train-only
structural surfaces can be turned into a *predicted* auxiliary feature that decorrelates from DWT.
Honest 5-fold well-OOF; DWT native-mask OOF as the private proxy. Neutral technical language.
Script: `scratchpad_probes/structural_surface_probe.py`. Baseline = DWT (internal OOF RMSE 10.393,
public 9.519, ref 54453597).

## 1. Setup & compliance

The 6 structural surfaces (ANCC/ASTNU/ASTNL/EGFDU/EGFDL/BUDA) are **train-only** — the TEST
horizontal wells carry only `{MD,X,Y,Z,GR,TVT_input}`. Here they are used **only as labels** to train
a surface predictor. Every feature fed to the predictor AND to the downstream TVT-residual model is
test-available (GR-window stats, trajectory X/Y/Z/MD, distance-from-cut, known-heel anchor, typewell
GR stats). Surfaces are never read at inference; the downstream model consumes the predictor's **OOF**
outputs (avoids train/test feature mismatch) — exactly the N-A deployment principle.

**Geometry.** Z and the surfaces share the ELEVATION frame (≈ −9200..−9850); TVT is a positive
stratigraphic coordinate (≈ 11236). The meaningful, Z-detrended structural quantity is
`surf − Z` = the signed bit-to-horizon offset (which formation the bit sits in). We predict that.

Dataset: 773 wells, toe rows subsampled ×1/10 → 378,751 rows, 22 test-available base features.

## 2. Results

### Stage 1 — foundation: is `surf − Z` OOF-predictable? (R² > 0 ?)

| surface | mean (ft) | std (ft) | OOF R² | OOF RMSE (ft) |
|---|---|---|---|---|
| ANCC  | 416.5 | 56.3 | **+0.709** | 30.39 |
| ASTNU | 243.1 | 64.3 | **+0.781** | 30.07 |
| ASTNL | 178.8 | 52.0 | **+0.698** | 28.54 |
| EGFDU |  85.7 | 43.6 | **+0.598** | 27.62 |
| EGFDL |  44.4 | 44.3 | **+0.592** | 28.31 |
| BUDA  | −80.6 | 45.6 | **+0.614** | 28.34 |

All six surfaces are OOF-predictable (R² +0.59 .. +0.78). **Foundation PASSES** (R² > 0). Note the
prediction RMSE (~28–30 ft) is *larger* than the per-well TVT drift being predicted (std ~5–16 ft).

### Stage 0/2/3 — nested blend of the predicted framework vs DWT (the decisive gate)

TVT-residual model (target = TVT − last-value); DWT OOF RMSE = 10.393. `blendW` = honest per-fold
nested optimal blend weight of the candidate against DWT (positive = independent info; negative = the
λ-disguise drift-amplification pattern public already rejected).

| model | features | OOF RMSE | corr(err,DWT) | blendW (mean; folds) | nested-blend RMSE |
|---|---|---|---|---|---|
| Stage 0 BASE-only | test-available only | 14.485 | 0.731 | **−0.021** (−.01,−.04,−.03,+.01,−.04) | 10.409 |
| **Stage 2 ORACLE** | BASE + **TRUE** surf−Z | 13.124 | **0.613** | **+0.216** (+.23,+.22,+.22,+.20,+.21) | **10.140** |
| Stage 3 ACHIEVABLE | BASE + **OOF-PRED** surf−Z | 14.391 | 0.735 | **−0.020** (−.01,−.05,−.03,+.02,−.04) | 10.417 |

- **Stage 0** (same-input sanity): blend-neutral/negative, as every prior same-input candidate — ✓.
- **Stage 2 ORACLE (diagnostic, NOT achievable):** the TRUE structural framework gives a **stable
  positive** blend weight **+0.216** (all 5 folds +0.20..+0.23), drops corr(err,DWT) 0.731→0.613, and
  improves nested CV **10.393 → 10.140** (−0.25). This is the **first positive oracle in the entire
  search** — every prior oracle (heatmap/Siamese/MTP, §8) only *tied* DWT. The structural surfaces are
  the one channel that genuinely carries information **independent of DWT**.
- **Stage 3 ACHIEVABLE (the real gate):** feeding the OOF-**predicted** surfaces collapses the signal
  back to the blend-neutral frontier — blendW **−0.020**, identical to BASE-only (−0.021). **V2 STOP
  condition met** (achievable blend weight ≤ 0).

### Stage 4 — partial-oracle precision sweep (how accurate must surfaces be to help?)

Interpolate predicted → true `surf − Z` (`α=0` = achievable predictor; `α=1` = oracle); the added
accuracy above `α=0` is genuine true-surface information, not extractable from the base features.

| α (pred→true) | surf-RMSE (ft) | blendW (mean) | corr(err,DWT) | nested-blend RMSE |
|---|---|---|---|---|
| 0.00 (achievable predictor) | 28.8 | −0.020 | 0.735 | 10.417 |
| 0.25 | 21.6 | −0.017 | 0.712 | 10.411 |
| 0.50 | 14.4 | **+0.095** | 0.682 | 10.355 |
| 0.75 |  7.2 | +0.170 | 0.653 | 10.248 |
| 0.90 |  2.9 | +0.210 | 0.625 | 10.162 |
| 1.00 (oracle) |  0.0 | +0.214 | 0.612 | 10.143 |

**Crossover:** the blend weight turns positive only around **surf-RMSE ≈ 14–20 ft** — roughly **2×
more accurate than the achievable OOF predictor (~29 ft)** — and that accuracy must come from genuine
true-surface information (α > 0), not from the base features. Even the α=0.25 point (25% true info,
surf-RMSE 21.6 ft) is still ≈ zero. A test-available predictor sits at α=0 (all accuracy is
BASE-derived, hence redundant with BASE) regardless of its nominal RMSE, so it cannot cross the
threshold. This is the quantitative form of the redundancy argument in §3.

## 3. Interpretation — why the oracle signal is unreachable

A surface predictor produces `pred_surf = h(BASE)`, a deterministic function of the test-available
features. Therefore `BASE + pred_surf` carries **no information beyond `BASE`** — it is redundant, and
in the OOF limit must match the BASE-only model. Stage 3 (−0.020) ≈ Stage 0 (−0.021) confirms this
empirically. The oracle's independent signal (+0.216) lives entirely in the part of the true surfaces
that is **orthogonal to the base features** — i.e. the train-only structural detail that is *not* a
function of GR/trajectory/position — which is exactly what a test well cannot supply (surfaces are
train-stripped). The Stage-4 sweep corroborates: the blend weight only rises once genuine true-surface
information is injected (α > 0), not from improving prediction accuracy on the same inputs.

**Consequence:** a stronger surface predictor — including a Kaggle-GPU NN — cannot recover the signal,
because any predictor built on the current test-available inputs is still a function of `BASE`. The
same argument closes **N-B** (multi-task DWT-family retrain with auxiliary structural heads): the
auxiliary head predicts surfaces from the same test-available representation, so it can only inject the
DWT-visible part of the structure. **No structural-label GPU direction is warranted on this evidence.**

## 4. Verdict

- **Foundation:** PASS (surfaces OOF-predictable, R² 0.59–0.78).
- **Independent structural signal exists:** YES — oracle blend weight **+0.216** (10.39→10.14), stable
  across folds. This is a genuinely new, positive finding (the first oracle to *beat* rather than tie
  DWT), and it identifies the structural framework as the one information channel DWT does not saturate.
- **Achievable from test-available inputs:** NO — predicted surfaces are blend-neutral (−0.020 = base),
  because any predictor is a function of inputs DWT already consumes. **V2 STOP.**
- **GPU (N-A / N-B):** **not warranted.** The limiter is *label availability* (surfaces are train-only),
  not model capacity; a bigger model on the same inputs lands on the same blend-neutral frontier.
- **New ledger category:** *oracle-positive but achievable-negative* — the independent signal provably
  exists in train-only labels yet is not a function of any test-available input, so it is unreachable by
  any model on the current input set. This sharpens the "information ceiling" into a **label-availability
  ceiling**.
- **Honest base unchanged** = DWT 9.519 (ref 54453597). The evidence-supported deliverable lever is
  S-A (`reports/final2_decision_optimization_2026-07-15.md`), not a new honest model.

## 5. Reproduce
```
python3 scratchpad_probes/structural_surface_probe.py   # ~5 min CPU, 2 cores; needs the DWT OOF
                                                         # combo_state.npz (well/ridx/oof/yt/base/cut)
```
Requires the cached DWT native-mask OOF (`combo_state.npz`) and the local `data/rogii/train` well CSVs.
