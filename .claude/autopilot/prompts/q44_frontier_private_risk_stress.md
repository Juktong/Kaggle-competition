---
id: q44_frontier_private_risk_stress
priority: 630
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q44 Frontier Private Risk Stress

We cannot see private score. Stress the frontier family under plausible private hidden-well regimes.

Required execution:

1. Read Q18/Q30/Q33 and final slot packages.
2. Define scenario axes:
   - H-visible vs H-hidden;
   - overlap/retrieval works vs fails;
   - public 3-well draw representative vs non-representative;
   - teammate 54922806 provenance available vs unavailable;
   - frontier public-derived dependency risk.
3. For each scenario, evaluate final slot pair:
   - 54922806 + 54844628;
   - 54968060 + 54844628;
   - other already submitted pairs if justified.
4. Output the conditions under which ownership-first should override score-first.
5. Do not submit.

Write `reports/q44_frontier_private_risk_stress_2026-07-30.md`.
