# ROGII — Final-2 submission strategy (honest vs public-hedge)

Last updated 2026-07-14. Competition allows **2 final submissions**; the private LB (novel wells)
decides the prize. This doc keeps the two categories **strictly separated** and records the
public/private risk of each. It is a strategy ledger, not a model — do not merge the hedge into
the honest baseline.

## Category A — HONEST / private-relevant (primary final slot)

| model | public | ref | private relevance | risk |
|---|---|---|---|---|
| **DWT 5-model fork** | **9.519** | 54453597 | internal native-mask CV **10.40** ≈ private behavior | low — no overlap override; honest RMSE on novel wells |

- This is a pure honest model (GR + typewell + trajectory ensemble; **no** exact-match override,
  **no** train-only fields). Its public score IS a clean honest-RMSE sample, so public≈private for
  this model. It is the primary slot for the private ranking.
- Clean source = `DWT_backup_preCb3.ipynb` / kernel `joezzzzz/rogii-dwt-honest-codex`. The current
  kernel version on Kaggle is v13 (a LAM isolation experiment); the banked honest submission is the
  earlier **ref 54453597** (v6), which stays selectable regardless of later kernel versions.
- Extensive candidate search (heatmap/Siamese/MTP/offset-meta/routing/loss-diversity/geometry) has
  not produced a candidate with a stable honest OOF improvement over 9.519 (see lessons doc §7–§11):
  same-input candidates lie on the blend-neutral frontier (they behave as "DWT + noise").

## Category B — PUBLIC-HEDGE / overlap (secondary final slot) — NOT an honest model

These score ~7.2 on public **only because of a guarded exact-match/overlap override** that
reconstructs TVT for hidden test wells that DUPLICATE train wells, plus gold visible-prefix
calibration. The 7.2 is **not** model quality. On **novel** private wells the override is largely a
no-op, so each of these collapses toward its (weaker, unmeasured) honest base. Use ONLY as a hedge
for the scenario where the private set contains train-duplicate wells.

| hedge | public | ref | mechanism note | downside profile |
|---|---|---|---|---|
| Plane Top2 Gate Safe | 7.212 | 54289934 | gated/"safe" override | bounded — lower catastrophic risk |
| Hongwei bounded ruler allw50 | 7.220 | 54331645 | posterior-bounded overlay | bounded |
| HMM PF prefix-calibrated | 7.231 | 54387277 | PF + dynamic overlay | medium |
| Top1 smoother w0.15 | 7.283 | 54272931 | Top1 overlay, smoothed | medium |
| Top1 final projected | 7.268 | 54272932 | high-risk projection | higher |
| raw Hongwei overlay | 7.278 | 54331650 | raw low-corr overlay | higher |
| Amged 7.091 base | 7.732 | 54447950 | weaker exact-repro overlay | weaker public, simpler |

**Overlap exploitation ceiling ≈ 7.27** (teammate affine-overlay 7.278/7.294; naive exact-copy
scored 11,551 and was rejected). Stacking more overlap adds ~nothing beyond this.

## Recommended final-2 (textbook best-CV + best-public hedge)

1. **DWT 9.519 (ref 54453597)** — honest primary; wins if private ≈ honest (no/low overlap).
2. **Plane Top2 Gate Safe 7.212 (ref 54289934)** — public-hedge; wins if private contains
   train-duplicate wells (overlap-lenient private). "Gate Safe" = bounded override → limits
   catastrophic downside if the override misfires on novel wells.

Rationale: the two slots hedge the two scenarios for how the hidden private set is composed. You
only need ONE slot to be good. Risk points: if the hedge's honest base is materially weaker than
DWT and private overlap is low, the hedge underperforms DWT on private — acceptable, because DWT
covers that scenario. Do not spend a final slot on a second honest model (no candidate beats 9.519)
nor on two overlap plays (they are correlated and share the same private-collapse risk).

## Open items / next validation
- (optional) Source-review the 7.212 kernel to quantify its override guard + honest base quality,
  refining the downside estimate. Deferred — does not change the recommended pair.
- Selection is locked in at the deadline (2026-08-05); both refs above are on the board and
  selectable now.
