---
id: q12_coverage_gated_self_template
priority: 220
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q12 Coverage-Gated Self-Correlation Template

N9 found a useful but conditional signal: self-correlation AUC is `0.7174` on prefix-covered states, but
`0.4548` on uncovered states. Test only the coverage-gated version.

Goal:

- Use self-correlation only where prefix coverage is sufficient.
- Explicitly disable interpolation across uncovered states.
- Combine with typewell or deployed honest only through a validation-backed gate.

Required execution:

1. Read `reports/n9_self_correlation_prefix_template_2026-07-28.md`.
2. Define prefix-coverage metrics available at test time.
3. Build a coverage-gated self-emission or correction:
   - active only on covered states/wells;
   - fallback to typewell/deployed honest elsewhere.
4. Validate on held-out-WELL split.
5. Measure whether this improves any well family without worsening uncovered wells.
6. If stable, prepare Kaggle smoke/full and submit only through the gate.

Write `reports/q12_coverage_gated_self_template_2026-07-29.md`.
