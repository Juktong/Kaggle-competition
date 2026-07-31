# Typewell Particle-Filter Candidate — 2026-07-01

## Decision

Add a hidden-compatible **typewell particle-filter (PF)** candidate to the
full-data router matrix. On the full 773 wells, always-on PF does **not** beat
`last_value` and the unconditional-prior router correctly rejects it (falls back
to last_value everywhere, same as before). However, a probe shows that **gating
PF by its own move magnitude recovers a small out-of-fold improvement**
(14.6782 vs 14.6844), which is the concrete next lever. This is a local-CV result
only. **No Kaggle submission is triggered by this round.** Official submission
still waits for a candidate that is plausibly competitive with the current best
leaderboard score (7.182) and passes audit — not merely one that edges the naive
last_value CV baseline.

This answers the open question from `Q20260701-05`: *"Add richer router features
and train a real candidate-family router; require full-data weighted RMSE
improvement and near-zero catastrophic rate before packaging a notebook."*

## Why This Candidate

Prior candidate families were all within-well extrapolations (`last_value`,
`damped_tail_linear_*`, `piecewise_tail_slope_*`, `recent_plateau_quantile`,
`fault_step_recent_level`) or self-correlation. The only mechanism touching the
paired **typewell** (`gr_shift` / `ncc_shift`) collapsed it into a single global
scalar offset, discarding the geological structure in the typewell GR↔TVT curve.

The competition is well-wise TVT sequence reconstruction: the hidden toe-end TVT
should be read by aligning the horizontal-well GR against the paired typewell
GR↔TVT reference. So the highest-value gap was a candidate that actually uses the
typewell *shape*.

## What Was Tried And Rejected First: Alignment-Then-Gate

A segment-NCC "dip alignment" of well GR to the typewell was prototyped on real
train wells (native `TVT_input` mask). Findings:

- The typewell shape carries real signal (naive warp rescued the worst wells by
  4–14 RMSE), but naive greedy warping runs away (up to +100 RMSE, ~92%
  catastrophic) because oscillatory GR aliases and per-segment offsets accumulate.
- A heavily regularized, anchor-relative, penalized version reached **0%
  catastrophic but only break-even** (net pooled RMSE ≈ baseline).
- Critically, **the prefix hold-out signal does not predict hidden-suffix wins**
  (heel-side prefix behaves differently from the hidden toe), so simple gating
  cannot turn the weak signal into a net gain.

Conclusion: the whole *align-then-gate* family tops out at break-even. The blocker
is not alignment quality but the inability to tell, at prediction time, which
wells the alignment got right. This reproduces the project's earlier "local signal
but not stable enough" finding with a genuinely typewell-based method.

## PF Design

A minimal 1-D bootstrap particle filter that sidesteps the gating problem by
carrying uncertainty internally.

- **State** `(tvt, dip)`.
- **Motion**: `dip` random-walks (bounded, `dip_persist`) with rare fault jumps;
  `tvt += dip·ΔMD + κ·(anchor − tvt) + noise`. The Ornstein-Uhlenbeck pull `κ`
  toward the anchor makes the estimate revert to `last_value` when GR is
  uninformative — a safe default rather than an external gate.
- **Observation**: typewell GR likelihood `exp(−½((GR_hw − GR_tw(tvt))/σ)²)`.
  GR-missing rows carry no update, so the cloud spreads along the motion prior.
- **Calibration (prefix only, hidden-compatible)**: `σ_gr` from the prefix
  GR-vs-typewell residual (robust MAD, floored); `dip0` from the prefix tail
  slope, shrunk hard toward 0.
- Estimate = weighted particle mean; systematic resample when ESS < half.

Hidden compatibility: uses only `MD`, `GR`, known-prefix `TVT_input`, and the
typewell `TVT/GR`. No train-only formation columns, no visible well IDs, no fixed
row counts. Deterministic (seeded).

## Prototype Evidence (real train wells, native mask)

Ornstein-Uhlenbeck mean-reversion is the key stabilizer. Sweeping `κ`:

| κ | pooled RMSE (PF vs base) | mean per-well Δ | win rate | catastrophic |
| --- | --- | --- | --- | --- |
| 0.005 | 15.61 vs 15.38 | +0.61 | 0.35 | 0.092 |
| 0.01 | 15.28 vs 15.38 | +0.11 | 0.45 | 0.025 |
| **0.02** | **14.30 vs 14.54** | **−0.12** | **0.50** | **0.000** |
| 0.03 | 14.46 vs 14.54 | −0.05 | 0.50 | 0.000 |

The benefit is **concentrated on high-drift wells** (the RMSE-dominant ones): on
a 240-well sample the top rescues were −4 to −34 RMSE on wells whose toe drifts
far from the anchor, while low-drift wells barely move. This is why PF belongs in
the framework as a **routed** candidate, not an always-on replacement.

## Integrated Subset Result (120 wells, native + 0.50 splits)

Run through the real `full_data_router_matrix.py` with PF integrated:

| method | pooled RMSE | vs baseline | win | catastrophic |
| --- | --- | --- | --- | --- |
| `last_value` (baseline) | 14.2987 | — | — | 0.000 |
| `typewell_particle_filter` (always-on) | 14.1243 | −0.175 | 0.471 | 0.008 |
| `learned_prior_router` (selects PF 34×) | 14.2578 | −0.041 | — | 0.004 |

On this subset the router selected `typewell_particle_filter` on 34/240 splits and
netted an improvement. **This subset was optimistic and did not survive full data
(see below)** — it happened to be richer in high-drift wells. The full-data result
is the authoritative one.

## Next-Round Lever: Route PF By Its Own Move Magnitude

The current holdout-based router leaves gains on the table (always-on PF 14.124 <
routed 14.258). Feature analysis on the subset matrix shows why: standard
predict-time features (GR coverage, prefix fraction, holdout delta) show
near-zero separation of PF wins vs losses (|corr| < 0.08). But **PF's own move
magnitude does separate them**:

| PF split group (by `pred_move_abs_p90`) | pooled RMSE vs base | win | catastrophic |
| --- | --- | --- | --- |
| low-move half (barely moved) | +0.109 | 0.41 | 0.000 |
| high-move half (committed a large move) | −0.379 | 0.53 | 0.017 |

When PF commits to a large move it is usually right (high-drift rescue); when it
barely moves it is noise around `last_value` and mildly hurts. `pred_move_abs_p90`
has the strongest delta correlation of any feature (−0.117). The next round should
route PF by move magnitude (feature already in the matrix) — or train a small
learned router on PF move/uncertainty features — validated out-of-fold, rather
than by prefix holdout. Plumbing the PF diagnostics (`pf_post_std`,
`pf_mean_abs_dev`) into the matrix is a prerequisite for the learned variant.

## Full-Data Result (773 wells, 1546 splits, N=300) — authoritative

| method / router | pooled RMSE | vs baseline | catastrophic |
| --- | --- | --- | --- |
| `last_value` (baseline) | 14.6844 | — | 0.000 |
| `typewell_particle_filter` (always-on) | 14.7336 | **+0.049 (worse)** | 0.008 |
| `learned_prior_router` (unconditional prior) | 14.6844 | 0.000 (rejects PF) | 0.000 |
| **`oof_move_gated_pf`** (probe) | **14.6782** | **−0.0062** | 0.008 |

On the full distribution, always-on PF is slightly worse than `last_value`
(mean per-split delta +0.078), so the unconditional-prior router rejects it and
returns the baseline exactly — no regression, no improvement. The
`move_gated_router_probe.py` diagnostic (reads the saved matrix, no PF rerun)
learns a move-magnitude threshold out-of-fold on the training folds and applies it
to the held-out fold: it selects PF on 384/1546 splits (25%) and recovers a small
but real improvement (−0.0062), with catastrophic rate 0.008.

This is the first thing to beat `last_value` on the full-data router in this
project, but it is tiny in absolute terms. Honest caveat: our CV baseline is the
naive `last_value` (pooled 14.68); the leaderboard 7.182 comes from a tuned public
PF stack, so a hundredths-of-a-point CV gain over `last_value` is **not** evidence
of a leaderboard-competitive model.

## Submission Policy

Unchanged. This is local pseudo-hidden CV evidence. No official Kaggle submission
is made this round. Packaging a notebook waits until the full-data router shows a
stable improvement without worst-split regression, ideally after the
move-magnitude routing round.

## Outputs

- `scripts/multi_hypothesis_router_cv.py` — `typewell_particle_filter_candidate`
- `scripts/full_data_router_matrix.py` — PF router-eligible + `--pf-*` params
- `scripts/move_gated_router_probe.py` — OOF move-gated router diagnostic
- `experiments/full_data_router_*` — regenerated with PF
- `experiments/move_gated_router_probe.csv` — probe summary
- `reports/full_data_router_matrix_report.md` — regenerated
- `reports/move_gated_router_probe.md` — probe report
