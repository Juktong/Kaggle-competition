---
id: q25_submission_ensemble_nonhomogeneous
priority: 350
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q25 Submission Ensemble Non-Homogeneous Candidate

Test whether any ensemble of existing scored outputs has final-slot information value.

Goal:

- Combine existing submissions only where error correlation or family diversity supports it.
- Avoid naive averaging already shown weak.
- Focus on non-homogeneous candidates that could be useful as slot 2 or diagnostic.

Candidates:

- frontier overlap-ON/OFF variants;
- hedge-OFF if scored;
- honest `54844628`;
- PF mean/path soft combiner if Q21 creates one.

Required execution:

1. Build pairwise diff/correlation table over available outputs.
2. Test robust blends:
   - trimmed mean;
   - per-well family switch with non-public features;
   - convex blend with nested OOF only;
   - uncertainty-bounded hedge between frontier and honest.
3. Reject if near-duplicate or if local gain is proxy-only.
4. Submit at most one candidate if it passes all gates.

Write `reports/q25_submission_ensemble_nonhomogeneous_2026-07-29.md`.
