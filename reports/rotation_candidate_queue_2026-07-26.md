

## 2026-07-28 update (N2 increment structural field)

- **Closed: re-referencing the structural field's increment.** The deployed field is already heel-anchored
  and level-invariant, so the intended level->increment swap is a no-op; the two constructions that DO
  differ both fail the 3-well gate on the full 760-well split (`iso` -0.1003 pooled, 5th -1.7148;
  `increment` -1.6840 pooled, 5th -5.5224).
- **Corrected:** `new_direction_search` described the deployed field as interpolating the TVT level. It
  interpolates the increment and takes the level from the target's own known heel.
- **New anchor fact:** the deployed neighbourhood is effectively single-well — 99.38% of the k=12
  contributing points come from the same well as the nearest point, and the nearest well essentially never
  changes along a lateral. Any future cross-well idea should assume a single dominant neighbour.
- **Retained:** a byte-exact reimplementation of the deployed structural field
  (`scripts/n2_increment_structural_field.py`), reproducing the banked 8.8626 to -0.0000 on the full split.
  Reusable for any future variant of this component.
- Next runnable: **`n1_geometry_bounded_alignment`** (priority 130).
