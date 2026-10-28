---
id: q16_honest_twh1_residual_router
priority: 260
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q16 Honest TWH=1 Residual Router

Try to improve the fully-owned honest `54844628` line by using `TWH=1` and coverage/self features only
as a bounded residual router, not as a full replacement.

Goal:

- Preserve the independent honest slot value.
- Apply corrections only in high-confidence regions.
- Avoid train-copy lookup and private-incompatible features.

Required execution:

1. Reproduce the deployed honest baseline exactly.
2. Build row/well features from:
   - `TWH=1` score;
   - self coverage/self score;
   - prefix length;
   - conformal uncertainty/marginal error band;
   - structural-field neighbour diagnostics.
3. Test bounded residual corrections and hard gates on nested held-out-WELL split.
4. Require bootstrap stability and no large tail regression.
5. If stable, prepare Kaggle smoke/full and submit only through the gate.

Write `reports/q16_honest_twh1_residual_router_2026-07-29.md`.
