---
id: q49_transition_prior_smoke_from_research
priority: 680
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q49 Transition Prior Smoke From Research

This task should execute the best concrete transition/path idea produced by Q40 or Q43. If Q40/Q43 found none, close.

Required execution:

1. Read Q40 and Q43 outputs.
2. Select exactly one highest-value transition/path smoke.
3. Implement the smallest local validation possible.
4. Gate:
   - nested by-well gain;
   - positive 3-well 5th percentile;
   - helps >50% wells or has a justified selector;
   - non-duplicate;
   - expected public effect >0.115 if submitting.
5. Submit only if all gates pass after smoke and full audit.

Write `reports/q49_transition_prior_smoke_from_research_2026-07-30.md`.
