---
id: n2_increment_structural_field
priority: 120
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# N2 Increment-target refinement of the deployed structural field

Change the interpolated quantity of the deployed cross-well structural field from the TVT **level** to the
heel-referenced **increment**, holding every other element fixed.

Context (do not re-derive):

- Banked evidence: the dominant remaining residual component is drift along the toe (slope std 13.28 ft),
  not initial level (std 4.72 ft).
- The deployed field in `54844628` interpolates the level and is the only cross-well component with a
  confirmed honest gain (OOF 9.2987 -> 8.8626, +0.436). Gate `nnb>=4 AND closest surviving mate <1000 ft`
  (87% of rows), W=0.15 fixed from nested OOF, 150 ft duplicate guard.
- `reports/new_direction_search_2026-07-28.md` M5 measured the NAIVE plane form of this idea and it
  fails: standalone 64.57 and 18.23 at W=0.15 vs a flat anchor of 15.98, 3-well P(gain>0) = 0.314.
  Do not re-attempt the ungated global plane. The point of this task is the increment target inside the
  deployed group-anchored + IDW + gated machinery.

Required execution:

1. In the existing structural-field builder, swap the interpolated quantity for the increment relative to
   the last known `TVT_input` row. Keep gate, group anchor, IDW kernel and W at their deployed values so
   the comparison isolates one factor.
2. Nested OOF on the same 760-well split. Report the delta vs 8.8626.
3. Run `scripts/eval_three_well_gate.py`. Report the 3-well bootstrap percentiles and P(gain>0). The
   760-well figure is a reference only, never a gate.
4. If and only if the 3-well gate passes, run the pre-submit audit
   (`scripts/rotation_candidate_audit.py`) and then the submit gate.
5. If the gate does not pass, record the measured margins and close or narrow the direction.

Write:

- `reports/n2_increment_structural_field_2026-07-28.md`
- Updates to the rotation status / candidate queue / submission decisions documents.
