---
id: q14_frontier_bimodal_hedge_weight_scan
priority: 240
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q14 Frontier Bimodal Hedge Weight Scan

The lite frontier audit corrected a prior claim: the bimodal hedge is the largest post-SP45 effect
(about +2 ft on 4301 rows), not inert. Audit whether a bounded weight scan can produce a useful,
non-duplicate frontier variant.

Goal:

- Isolate the bimodal hedge's effect.
- Test small bounded weights around the current setting.
- Avoid near-duplicate submissions.

Required execution:

1. Read `reports/frontier_variant_matrix_lite_2026-07-28.md` and `reports/g21_sp45_only_2026-07-26.md`.
2. Build a small static matrix of bimodal hedge weights and related clamps.
3. Audit outputs against `54922806`, `54968060`, and `54990075`:
   - RMSE diff;
   - per-well distribution;
   - range/slope/jump sanity;
   - whether the output is materially non-homogeneous.
4. If one variant has clear information value, run Kaggle smoke/full.
5. Submit at most one candidate and only if it passes the submit gate.

Write `reports/q14_frontier_bimodal_hedge_weight_scan_2026-07-29.md`.
