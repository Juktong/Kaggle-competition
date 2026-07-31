# New-direction queue (B2) — 2026-07-25

Executable directions, each with input / output / smoke / full / submit-criterion. Framed by this
session's findings: the frontier 6.5 is overlap-driven (H-visible); our `54844628` is the H-hidden
hedge; the 3-well public LB does not resolve sub-0.11 deltas; local truth-space ≠ leaderboard at fine
scale. So a direction is worth pursuing only if it is (a) structurally distinct and (b) plausibly
H-hidden-robust, not if it merely nudges local OOF.

## Directions

| # | direction | input → output | smoke | full | submit criterion |
|---|---|---|---|---|---|
| D1 | **overlap-OFF frontier ⊕ 54844628 ensemble** (H-hidden hedge) | A2 overlap-OFF output + our 54844628 → weighted/median blend | local diff + decorrelation of the two on the 3 wells (no GPU) | build blend kernel if decorrelated | submit only if the blend is materially different AND has an H-hidden robustness argument the components lack |
| D2 | **honest prefix-only calibration** (no train-duplicate lookup) | 54844628 + per-well known-heel self-calibration (the frontier's *legitimate* half, without overlap override) | local: apply a cut-based heel recalibration to 54844628 on train wells, OOF | Kaggle if local shows a stable gain | 3-well-gate + H-hidden robustness |
| D3 | **frontier PF/beam as a decorrelated component for our base** | frontier's PF (overlap-OFF) vs our DWT+PF → correlation of errors on train wells | local error-correlation smoke (reuse A2 full PF output where available) | only if corr materially < 1 | must decorrelate AND improve a 3-well-scale metric |
| D4 | **robust final-selection meta-model** under H-visible/H-hidden uncertainty | candidate set {overlap-ON 6.5, overlap-OFF frontier, 54844628} → a selection rule that hedges both hypotheses | local: simulate both hypotheses' scoring, pick the min-regret pair | no new submission; informs the final-slot package | n/a (selection, not a new submission) |
| D5 | **stratigraphic-correlation / DTW alignment of horizontal GR to neighbour horizontals** | test GR sequence + neighbour horizontal-well GR → aligned TVT transfer | already smoked (2026-07-22, hnbr) — bounded by GR-shape weakness | only with a materially better alignment cost | must decorrelate from PF/struct |

## Priority

- **D1 first** (depends on A2 full; no extra GPU for the local analysis) — it is the natural H-hidden
  hedge and directly uses the A2 output.
- **D4** is a paper/selection exercise that improves the final-slot package without a submission.
- D2/D3 are Kaggle-cost directions gated on a local signal first.
- D5 is bounded-low by prior evidence; only revisited if a new alignment idea appears.

## Discipline

Every direction: local/smoke before full; full before submit; submit only if non-homogeneous + 3-well-gate
+ H-hidden argument + quota. No direction displaces `54844628` as the fully-owned H-hidden hedge unless it
passes those bars.
