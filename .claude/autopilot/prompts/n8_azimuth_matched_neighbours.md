---
id: n8_azimuth_matched_neighbours
priority: 170
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# N8 Azimuth-matched neighbour selection for the structural field

Add an azimuth-similarity filter to the deployed cross-well structural field's neighbour selection,
holding every other element fixed.

Context (do not re-derive):

- The structural field in `54844628` is the ONLY cross-well component with a confirmed honest gain
  (OOF 9.2987 -> 8.8626, +0.436). Gate `nnb>=4 AND closest surviving mate <1000 ft` (87% of rows),
  W=0.15, 150 ft duplicate guard, group key = round(max(typewell.TVT), 1).
- Our neighbour selection uses typewell-group + XY distance and **ignores azimuth**.
- `reports/n6_public_solution_audit_2026-07-28.md`: a public methodology repo selects offset-well priors
  from spatially-close **azimuth-matched** neighbours, on the reasoning that two wells at the same
  orientation but drilled in opposite directions encounter the formation in opposite sequence
  (updip vs downdip), so the local TVT-Z slope differs in sign.
- `reports/n2_increment_structural_field_2026-07-28.md` left a **byte-exact reimplementation** of the
  deployed builder (`scripts/n2_increment_structural_field.py`, reproduces the banked 8.8626 to -0.0000
  on the full 760-well split). Reuse it; do not rewrite the builder.
- N2 also measured that the deployed neighbourhood is effectively **single-well** (99.38% of the k=12
  contributing points share the nearest point's well). An azimuth filter that removes the single dominant
  neighbour may therefore do more harm than good — that is the risk this task tests.

Required execution:

1. Compute per-well signed drilling azimuth from X/Y (test-available).
2. In the existing builder, add an azimuth-similarity filter to the surviving-neighbour set. Sweep the
   tolerance (e.g. 15, 30, 45, 90 degrees, plus no-filter as the control). Hold gate, W, IDW kernel,
   anchor length and duplicate guard at deployed values.
3. Report how often the filter removes the nearest neighbour, and the resulting `nnb` distribution.
4. Nested OOF on the same 760-well split; report the delta vs 8.8626.
5. Run `scripts/eval_three_well_gate.py`. The 760-well figure is a reference only, never a gate.
6. Only if the 3-well gate passes: `scripts/rotation_candidate_audit.py`, then the submit gate.

Write:

- `reports/n8_azimuth_matched_neighbours_2026-07-28.md`
- Updates to the rotation status / candidate queue / submission decisions documents.
