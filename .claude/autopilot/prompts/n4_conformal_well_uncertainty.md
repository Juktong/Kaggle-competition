---
id: n4_conformal_well_uncertainty
priority: 110
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# N4 Calibrated per-well uncertainty (split conformal on the banked OOF)

Produce a distribution-free per-well error estimate for the honest line, for use in slot selection and in
any future confidence-gating axis.

Context (do not re-derive):

- The banked honest candidate is `54844628`, public 7.891, nested OOF 8.8626 over 760 wells.
- The closed anti-harm guard reached AUC 0.53 because it targeted the *sign* of a candidate's harm.
  This task targets the *width* of the honest model's own error distribution, which is better posed.
- The variant-matrix round found per-well confidence gating to be an axis the frontier never exposes.

Required execution:

1. Load the banked 760-well OOF residuals. Do not refit the model.
2. Build test-available conditioning features only: `nnb`, closest surviving mate distance, prefix
   fraction (`TVT_input` known fraction), GR variance, well length, mean inclination.
3. Split-conformal (or Mondrian/conditional conformal over feature bins) intervals at 80/90/95%.
4. Report empirical coverage per bin, interval width per bin, and whether width separates wells at all
   (if width is flat across bins the estimate carries no per-well information — record that as the
   result).
5. Score the 3 visible test wells' predicted widths and state where they sit in the distribution.

Write:

- `reports/n4_conformal_well_uncertainty_2026-07-28.md`
- Reusable script under `scripts/`.

No submission. Report negative results explicitly.
