---
id: g35_honest_prefix_calibration
priority: 10
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# G3.5 Honest Prefix Calibration

Improve the fully-owned honest hedge `54844628` without using train-copy lookup or private-incompatible features.

Goal:

- Preserve the fully-owned / OOF-validated value of `54844628`.
- Test low-risk prefix calibration, formation/contact anchoring, trajectory features, and bounded correction.
- Use honest masked split / OOF / bootstrap before any Kaggle work.

Required execution:

1. Static audit the current `54844628` source, output, and validation scripts.
2. Design one or more bounded prefix calibration variants.
3. Run a fast local smoke on a small masked split.
4. If smoke is coherent, run a wider honest masked split.
5. Compare against the `54844628` baseline:
   - OOF RMSE;
   - by-well improvement/regression;
   - bootstrap/stability;
   - trajectory smoothness and range sanity.
6. If a variant is stable and non-homogeneous, prepare Kaggle smoke/full.
7. Submit only if the submit gate passes and the report explains final-slot value.

Write:

- `reports/g35_honest_prefix_calibration_2026-07-28.md`
- Updates to rotation status, candidate queue, submission decisions, and ledger.

If no stable improvement appears, close the task on evidence and move to the next queued prompt.
