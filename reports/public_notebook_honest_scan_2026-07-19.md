# ROGII — public/local honest-component scan + new-family test (Directions F & G, 2026-07-19)

Session `1a07ce3e`. Find honest, replayable components of a DIFFERENT model family from {GBM, PF}, and test
whether any adds decorrelated signal beyond the DWT+PF blend. `$JOB/tmp/geom_blend.py`. Neutral language.

## Scan result (F)
A repo-wide scan (kaggle_kernel_*/, working/ forks, scratchpad_probes/, scripts/) surfaced ONE net-new honest
distinct-family set not previously blend-tested vs DWT: the **multi-hypothesis router candidate factory**
(`scripts/multi_hypothesis_router_cv.py`), honesty-enforced (`TRAIN_ONLY_TOKENS` guard, hidden_compatible=True),
with a precomputed OOF summary matrix (`experiments/full_data_router_candidate_matrix.csv`). Distinct families:
- **`piecewise_tail_slope_md/_Z`** — trajectory-only geometry: extrapolate the heel's TVT-vs-MD (or Z) linear
  slope across the toe, damped+clipped (max_move=12), GR-FREE. Honest.
- **`fault_step_recent_level`** — change-point: ramp a recent-vs-previous prefix-median level shift across the toe.
- `self_corr_prefix_shape` (GR self-analog, weak/rare), `recent_plateau_quantile` (order-stat, correlated).
Everything else was banked, not honest (spatial cKDTree imputes ANCC/FORMATIONS surfaces; Geology-label
classifiers; dip_probe reads toe truth), or same-family-as-assessed (typewell/NCC alignment = PF/beam; Conv1d
SSL = assessed). No FFT/wavelet/LSTM/Transformer exists in the repo.

## New-family blend test (G) — re-implemented faithfully (max_move=12, saturating tanh), 773-well OOF
| model | standalone RMSE | corr vs DWT | corr vs PF |
|---|---|---|---|
| DWT | 10.40 | 1.00 | 0.51 |
| PF | 11.00 | 0.51 | 1.00 |
| geom_MD | 17.22 | 0.676 | 0.385 |
| geom_Z | 17.13 | 0.677 | 0.390 |
| fault_step | 15.77 | 0.729 | 0.417 |

Nested 3-way blend: DWT+PF **9.2774** → +geomMD 9.2156 → +geomMD+geomZ+fault **9.2017 (gain +0.076)**, with
**NEGATIVE weights** (geomMD −0.006, geomZ −0.03, fault −0.072).

## Conclusion — does NOT clear the gate
- The geometry/fault candidates are **weak** (15.8–17.2 vs DWT 10.40 / blend 9.30) and **correlated with DWT**
  (0.68–0.73) — they are a re-expression of the heel's last-value/linear anchor, not a decorrelated axis (the
  earlier "corr 0.24" was an unfaithful loose-clip version).
- The +0.076 blend gain comes via **NEGATIVE weights** — the negative-weight λ-disguise / drift-amplification
  pattern the project has repeatedly found does NOT transfer to public ([[honest-frontier-state]] screen:
  reject negative-weight blends; publicly disproven +0.62). Constrained to w≥0, the geometry gets weight 0.
- **No submittable improvement.** Only the genuinely-decorrelated positive-weight PF broke the blend-neutral
  wall; these GR-free geometric/change-point rules land on the negative-weight frontier. Line closed.
- **G (new input channels):** the GR-free trajectory-geometry channel was the most promising untested axis and
  it is blend-neutral; no other honest channel (spatial=surfaces/overlap, Geology=label, spectral=absent)
  remains. Next genuinely-new axis would need data or a model class not yet present in the repo.
