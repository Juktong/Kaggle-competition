---
id: q21_pf_path_soft_combiner
priority: 310
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q21 PF Path Soft Combiner

Q11 showed oracle best-of-96 PF paths beats deployed honest, but hard selection loses to PF mean.
Test a soft combiner instead of selector.

Goal:

- Convert PF candidate paths into a weighted average/median/trimmed mixture.
- Use uncertainty features only to adjust weights, not pick one path.
- Preserve PF mean robustness while capturing part of oracle headroom.

Required execution:

1. Read Q11 and stored 773x96 PF path artifacts.
2. Build soft weighting families:
   - temperature-weighted prior;
   - TWH1-score softmax;
   - clipped top-m average;
   - per-row robust median/Huber combination;
   - confidence-gated interpolation between PF mean and top weighted path.
3. Validate with nested held-out-WELL split.
4. Report oracle headroom converted, tail risk, 3-well bootstrap, and non-homogeneity.
5. If stable and materially closer to deployed honest, prepare Kaggle smoke/full.
6. Submit only through the gate.

Write `reports/q21_pf_path_soft_combiner_2026-07-29.md`.
