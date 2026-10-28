---
id: q56_pf_backward_smoothing
priority: 627
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q56 PF Backward Smoothing (forward-filter backward-simulate)

THE MODELLING GAP. `run_particle_filter` is a SINGLE FORWARD PASS. But **the entire toe GR log is
observable at prediction time** — we predict TVT for rows whose GR we can already see. A forward-only
filter therefore discards genuinely available information. That is a real gap, not a tuning knob.

Forward-filter backward-simulate (FFBSi) re-weights earlier particles using LATER observations. It is an
averaging/smoothing operation over the existing trellis, not a directional prior, so Q40's compounding
warning does not apply to it.

Required execution:

1. Patch the DEPLOYED PF source (`SUNNY_CODE` in cell 108 of `kaggle_kernel_henry_v10_sunny80_blend`, the
   one `scripts/pf_forward_oof.py` execs) — NOT `scripts/pf_honest_forward.py`. Q36 recorded that mistake:
   the standalone conservative PF is not what feeds the honest line.
2. Retain the particle trellis and add a backward smoothing pass; keep a flag whose OFF state reproduces
   the current forward-only output BYTE-FOR-BYTE, and report that degeneracy check.
3. **SMOKE FIRST (Directive 4)** on <= 12 wells: confirm the flag activates, the trellis alignment holds,
   and the reporting path reaches the gate.
4. Score INSIDE THE BLEND (`0.5*dwt + 0.5*pf_new`), reusing the deployed `dwt` column unchanged and
   asserting row alignment, exactly as `scripts/q36_gr_sigma_in_blend_oof.py` does.
5. GATE: nested by-well gain > 0 AND helps > 50% of wells AND 3-well 5th > 0.
6. Do not submit.

COST AND EXPECTATION. Higher than q54/q55 — hours on 2 cores, since the trellis must be retained. Note the
PF enters the honest blend at weight 0.5, so any gain HALVES before it reaches the line; state the
blend-level effect, not the standalone PF effect (Q36 recorded that framing error too).

Write `reports/q56_pf_backward_smoothing_<date>.md`.
