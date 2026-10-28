---
id: g33_multi_hypothesis_smoke
priority: 40
status: queued
requires_gpu: true
can_submit: true
max_submit_cost: 1
---

# G3.3 Multi-Hypothesis Trajectory Model

Test a top-K TVT/residual trajectory model instead of a single averaged trajectory.

Goal:

- Model ambiguous whole-well offsets and lithology ambiguity.
- Input known prefix, typewell GR summary, and trajectory features.
- Output top-K residual or TVT trajectories with probabilities.
- Use best-of-K / MTP-style loss for smoke validation.

Required execution:

1. Create a minimal train masked split.
2. Build a tiny model with K hypotheses.
3. Run a tiny GPU/CPU smoke:
   - training loop executes;
   - loss decreases;
   - top-K diversity is nonzero;
   - predictions pass basic trajectory sanity.
4. Compare against honest baseline and flat-anchor on masked split.
5. Expand only if there is a real signal.
6. Submit only if a full candidate passes the submit gate.

Write:

- `reports/g33_multi_hypothesis_smoke_2026-07-28.md`
- Any reusable smoke scripts.

If the task is too large for this rotation, produce a clear minimal next smoke rather than a broad plan.
