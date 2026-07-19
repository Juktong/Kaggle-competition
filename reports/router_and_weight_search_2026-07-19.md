# ROGII — router + weight search (Directions C & D, 2026-07-19)

Session `1a07ce3e`. Can a test-available router or a re-tuned weight beat the fixed 0.5 DWT+PF blend?
`$JOB/tmp/c_router_probe.py`, `bd_stress.py`; `scripts/router_feasibility.py`. Neutral technical language.

## D. Weight sweep (full 773-well OOF, pooled RMSE)
W=0.00 (DWT) 10.399 · 0.40 9.289 · **0.44 (fitted) 9.2775** · 0.45 9.278 · **0.50 (current) 9.297** ·
0.55 9.346 · 0.60 9.425 · 1.00 (PF) 10.995. The optimum is flat at W≈0.44 (9.2775), only **0.019 below** the
current 0.5 (9.297). This is within public-transfer noise, and W=0.5 is already public-verified (8.080). →
**No resubmission**: 0.5 is near-optimal and robust; a W=0.44 kernel would not reliably beat 8.080 on public.

## C. Router / selector (expanded test-available features)
Extended beyond the prior heel-drift probe: per-well (heel_drift, z_span, n_eval, gr_std, heel_zrange) and
per-row (|PF−DWT| disagreement, toe-row position, GR roughness, Z curvature).
- **No feature predicts WHICH model is better.** Per-row corr with (|errDWT|−|errPF|): |PF−DWT| disagreement
  +0.049, row-position +0.017, GR roughness −0.011, Z curvature +0.002 (all noise). Per-well feature corr with
  PF-advantage / optimal-weight all |r|<0.08.
- **Disagreement predicts HARDNESS, not direction** (corr with |errDWT| = 0.565): where PF and DWT disagree
  most (Q4), BOTH are bad (DWT 16.5 / PF 17.9) and the blend helps most (14.1) — but neither model is
  systematically better there, so 50/50 averaging is already optimal.
- **Nested routers are NOT better than the fixed blend:** drift-tercile router 9.272 (≈ global fitted 0.44,
  +0.025 vs 0.5 = just the global weight); disagreement-decile nested router **9.3191 — WORSE than fixed 0.5
  by 0.022** (it overfits the degenerate low-disagreement decile). Per-group optimal weights are ≈0.42–0.51
  (constant → no routing signal).

## Conclusion
The **fixed W≈0.44–0.5 DWT+PF blend is the deployable optimum.** The DWT/PF complementarity is real but
**oracle-only** (defined by truth-based hardness), not detectable from test-available features → no deployable
router improves on it. No submission from C or D.
