---
id: q40_transition_model_search
priority: 590
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q40 Transition Model Search

Q17 closed the emission-AUC lever. The still-open lever is the transition model in the DP/path line.

Goal: test transition priors that could improve path quality without relying on pointwise emission metrics.

Required execution:

1. Read Q10, Q13, Q17 and the current DP implementation.
2. Identify transition parameters/features already in code:
   - smoothness penalty;
   - jump penalty;
   - TVT monotonicity / slope constraints;
   - curvature constraints;
   - trajectory-derived priors;
   - well/group-specific drift priors.
3. Run cheap by-well validation sweeps first, not Kaggle.
4. Required gates:
   - nested by-well gain over the relevant baseline;
   - helps more than 50% of wells OR has a justified hedge/selector;
   - 3-well bootstrap 5th percentile positive;
   - not a near duplicate of an existing submitted artifact.
5. If a candidate passes, prepare a smoke-tested Kaggle path and submit only after the audit.

Write `reports/q40_transition_model_search_2026-07-30.md`.
