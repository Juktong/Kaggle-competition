
## 2026-07-28 update (new direction search)

Implementation round complete. Six new directions queued at 110–160, each with a CPU-only smoke and no
quota cost:

| pri | id | submission path | smallest smoke |
|---|---|---|---|
| 110 | `n4_conformal_well_uncertainty` | none (decision support) | split conformal on the banked 760-well OOF; check coverage per feature bin |
| 120 | `n2_increment_structural_field` | **yes** (gate required) | swap the deployed field's target level -> heel-referenced increment, gate/W fixed |
| 130 | `n1_geometry_bounded_alignment` | none | per-row admissible band on the G3.2 DP from `dZ`/`dH`, sweep the dip bound |
| 140 | `n3_multiscale_gr_matching` | none | 4-level DWT, scorer AUC per level vs G3.2's 0.7242 |
| 150 | `n6_public_solution_audit` | none | method diff of a second public solution vs our ledger (methods only, no external data) |
| 160 | `n5_typewell_fingerprint_families` | none | 30-min time-box: GR-vs-TVT curve match, does it beat the deployed spatial gate |

Closed this round: **single-dip geometric reparametrization** (oracle 7.65 vs honest 80.29 vs flat 15.91),
**train-only PNG images as an input modality** (no test PNGs), **exact typewell grouping** (0/3 test wells
match). Not queued with reasons: RL geosteering (no action space), azimuthal-GR dip inversion (single
scalar GR only).
