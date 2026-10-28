---
id: q23_frontier_stage_localizer
priority: 330
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q23 Frontier Stage Localizer

Map frontier post-SP45 stage effects by well/row to identify a non-duplicate conditional variant.

Goal:

- Move beyond global ON/OFF switches.
- Identify whether stage effects are beneficial only on specific rows/wells.
- Use local evidence and public score response, not proxy alone.

Required execution:

1. Read Q14, G2.1, A3/A4/A5, and `55064411` score if available.
2. Build per-stage diff maps:
   - learned-trajectory blend;
   - prefix calibration;
   - model-package correction;
   - bimodal hedge;
   - clipping/range handling.
3. For each stage, compute row/well features predicting when the stage helps or hurts on visible/local proxy.
4. Propose at most one conditional stage variant.
5. Kaggle smoke/full only if variant is non-homogeneous and structurally justified.

Write `reports/q23_frontier_stage_localizer_2026-07-29.md`.
