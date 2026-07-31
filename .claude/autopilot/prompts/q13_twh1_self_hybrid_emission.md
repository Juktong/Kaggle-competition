---
id: q13_twh1_self_hybrid_emission
priority: 230
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q13 TWH=1 Typewell + Coverage-Gated Self Hybrid

Combine the two retained signals:

- `TWH=1` typewell local score from N3.
- coverage-gated self signal from N9.

Goal:

- Test whether the self signal can help only where typewell score is uncertain or prefix coverage is high.
- Avoid naive averaging.
- Use a small set of interpretable gates.

Required execution:

1. Build features from `TWH=1` typewell score, self coverage, self score, prefix length, and trajectory sanity.
2. Fit or hand-select gates only on training folds; evaluate on held-out-WELL folds.
3. Compare to:
   - typewell-only `TWH=1`;
   - self-only coverage-gated;
   - deployed honest;
   - flat-anchor.
4. If no nested gain, close and record why.
5. If stable and non-homogeneous, proceed to Kaggle smoke/full and possible submit.

Write `reports/q13_twh1_self_hybrid_emission_2026-07-29.md`.
