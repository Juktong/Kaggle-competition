---
id: frontier_variant_matrix_lite
priority: 50
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Frontier Variant Matrix Lite

Run only low-cost, non-duplicate frontier variants around `54968060`.

Context:

- SP45-only scored `54990075 = 6.690`, worse than `54968060 = 6.643`.
- Post-SP45 stages are useful on public.
- Train-copy proxy is unreliable within the frontier family.

Allowed axes:

- post-SP45 stage weights;
- prefix calibration strength;
- model-package blend weights;
- bimodal hedge strength;
- uncertainty/range clipping;
- per-well confidence gating.

Rules:

- Do not rerun plain frontier.
- Do not submit near-duplicates.
- Start with static diff and batch smoke/local proxy only.
- Promote at most 1-2 variants to full, and only if they have structural information value.
- Submit only if the gate passes.

Write:

- `reports/frontier_variant_matrix_lite_2026-07-28.md`
- Updates to queue, status, and submission decisions.
