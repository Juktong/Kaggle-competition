---
id: q11_twh1_pf_seed_ranker
priority: 210
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q11 TWH=1 PF Seed / Path Ranker

The earlier DP formulations often failed because pointwise emissions could not generate good paths.
Test a different use of the same `TWH=1` signal: rank or select among existing PF/beam candidate paths
instead of generating paths from scratch.

Goal:

- Keep the PF motion model/path proposals.
- Use `TWH=1` scorer features to rank candidate paths, choose a path, or gate a small correction.
- Avoid repeating the failed pointwise-DP setup.

Required execution:

1. Identify stored PF/beam candidate outputs or regenerate a small set on masked train wells.
2. Score each candidate path using `TWH=1` local alignment summaries:
   - mean/quantile score;
   - prefix consistency;
   - range pressure;
   - jump/smoothness.
3. Validate with held-out-WELL split.
4. Compare against:
   - PF default path;
   - flat-anchor;
   - deployed honest;
   - any prior top-K ranker reports.
5. If the selector has positive nested evidence and non-homogeneous output potential, proceed to Kaggle smoke/full.
6. Submit only if the submit gate passes.

Write `reports/q11_twh1_pf_seed_ranker_2026-07-29.md`.
