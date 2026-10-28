---
id: q42_honest_line_error_taxonomy
priority: 610
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q42 Honest Line Error Taxonomy

The honest line remains valuable as slot-2 diversity. Find whether its failures cluster into actionable groups.

Required execution:

1. Use held-out train wells and existing predictions for 54844628-style honest line.
2. Segment errors by:
   - well geometry;
   - prefix length / known-contact coverage;
   - typewell distance/coverage;
   - GR morphology;
   - structural field neighbor count / closest mate;
   - toe/heel position;
   - sign and magnitude of residual.
3. Do not build a correction unless the sign is predictable out-of-fold. Q16 showed row-level sign was not predictable; this task should test coarser groups and explain if that changes.
4. Output 3-5 candidate group-level interventions, each with a smoke gate, or close the line.
5. Do not submit.

Write `reports/q42_honest_line_error_taxonomy_2026-07-30.md`.
