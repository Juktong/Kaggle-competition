---
id: q27_public_research_sequence_models
priority: 370
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q27 Public Research: Sequence Models And Alignment Learning

Research methods that could improve the TWH1 learned alignment signal without repeating closed DP failures.

Scope:

- differentiable DTW / soft-DTW;
- CTC/monotonic alignment;
- contrastive sequence learning;
- transformer/CNN local alignment;
- pair-to-trajectory calibration;
- sequence-level losses that penalize directional drift.

Required execution:

1. Search public papers/repos if available.
2. Keep only approaches that address Q13's key failure: pointwise metric improves while trajectory worsens.
3. Propose small smoke tests with held-out-WELL validation.
4. Queue 1-3 executable tasks if warranted.
5. Do not launch training unless a queued follow-up explicitly does it.

Write `reports/q27_public_research_sequence_models_2026-07-29.md`.
