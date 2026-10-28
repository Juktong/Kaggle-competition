# Autonomous backlog status — 2026-07-22

Round following the `54878409` public result. Neutral technical language throughout.
State refreshed from Kaggle + artifacts (not state files): 2026-07-22 03:51 UTC, **today's quota 0/5**;
`54878409` COMPLETE public **7.953** > banked `54844628` **7.891**; git clean.

## The two findings that dominate this round

1. **Validation scale was wrong.** The gate that passed `54878409` bootstrapped **760 wells**; the
   competition scores **3 wells**. The corrected gate (`scripts/eval_three_well_gate.py`) bootstraps at
   3-well scale, and under it **every candidate fails** (`54878409` 3w-5th −1.26; the best-OOF
   `topk96_l75` is the *worst*, −1.95).

2. **Local truth space ≠ leaderboard space at fine scale.** The 3 test wells are duplicated in train
   (`train.TVT == test.TVT_input` on heel to 0.0000). RMSE vs train-copy TVT ranks `54878409` *better*
   than `54844628` (3.4961 vs 3.6772, matching OOF) yet public ranks it *worse* (7.953 vs 7.891). No row
   subset reconstructs the public 7.891 scale. Local accuracy predicts the leaderboard only for **large**
   (≳0.5) differences (naive 11.5 ≫ DWT ≫ struct == public 9.519→8.080→7.891), not the ~0.1 margins our
   candidates live in.

Together these mean: **no small-margin candidate can be validated locally**, and none is submittable on
OOF evidence. `54844628` (7.891) remains the honest slot as the only real leaderboard result.

## Infrastructure built (A, B, corrected gate)

- `scripts/eval_three_well_gate.py` — reusable 3-well gate (CLI + `three_well_gate()`).
- `scripts/build_aligned_frame.py` → `aligned_preds.npz` — all candidates on one row order.
- `scripts/corrected_gate_reaudit.py`, `scripts/row_split_audit.py`, `scripts/anti_harm_guard.py`,
  `scripts/three_well_blends.py`, `scripts/probe_queue.py`, `scripts/pf_variant_smoke.py`.

## Directions — results

| dir | direction | result | disposition |
|---|---|---|---|
| A | corrected 3-well gate | built; retro-flags `54878409` (3w-5th −1.26 vs 760-ref +0.05) | delivered |
| B | re-audit all candidates | **all FAIL** the 3-well gate; OOF rank ≠ 3-well robustness | delivered |
| C | public mismatch feature audit | truth-space gap; no test-available red flag on the 3 wells | delivered |
| D | submission policy | no large-N-OOF submissions; 3-well scale; kernels-only | delivered |
| 1 | anti-harm guard | harm predictor AUC **0.53** = chance; cannot lift 3w-5th | closed |
| 3 | row-split stability | random split corr 0.999, block split corr 0.10 — split geometry unknown | delivered |
| 4 | conservative blends | shrinkage scales tail with mean → 3w-5th never >0 | closed |
| 7 | top-K corrected revisit | best OOF, worst 3-well tail; stays closed | closed |
| 8 | final-slot package | honest slot = `54844628`; exclude `54878409` | delivered |
| 9 | probe queue | 3 new probes: no red flag (typical difficulty, stable anchor, struct not risk driver) | delivered |
| 6 | PF variant smoke | wider-emission PF **stronger standalone** (+0.31, corr 0.885) | medium smoke running |
| 5 | horizontal-neighbour GR sequence | smoke running (fast variant) | in progress |

## Submissions

**0 submissions this round.** No candidate passes the corrected gate; per policy, no "try it" submission.
Today's quota 0/5 remains available. Honest slot `54844628` (7.891) unchanged; `54878409` excluded.

## What continues automatically

- Medium PF-variant smoke (60 wells, 32 seeds) and the horizontal-neighbour GR sequence smoke are
  running detached; results append to `reports/pf_variant_smoke_2026-07-22.md` /
  `reports/horizontal_neighbor_gr_sequence_2026-07-22.md`.
- The one direction with a positive standalone signal (wider-emission PF) is flagged for a full 773-well
  run as knowledge-building, explicitly **not** expected to be submittable (its ~0.15 pipeline effect is
  below the transfer threshold established in direction C).
