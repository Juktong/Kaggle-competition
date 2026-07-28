

## 2026-07-28 update (N6 public-solution audit)

- **Blocker:** the queued target `aaryan2203/rogii-wellbore-geology-prediction-argon` does not exist (404;
  the name came from a stale web-search snippet). Audited `mycarta/rogii-geosteering-toolkit` (MIT)
  instead — same intent, real target.
- **Newly queued from the audit:**
  - `n8_azimuth_matched_neighbours` (170) — azimuth-similarity filter on the structural field's neighbour
    selection; the only cross-well component with a confirmed honest gain, and N2 left a byte-exact
    reimplementation to modify. **The one queued item with a submission path.**
  - `n7_q3d_tortuosity_features` (180) — Q-3D tortuosity (Jing et al. 2022) was their largest single-group
    ablation gain (-0.107 RMSE) and is fully test-available from MD/X/Y/Z. Gate it against N4's CV R^2
    0.074 bar before touching the model.
  - `n9_self_correlation_prefix_template` (190) — the lateral's own known zone as the matching template;
    removes the cross-instrument level offset, which is the cue N3 showed dominates.
- **Confirmed closed by an independent party:** Catch22/AEON well-level features (+0.476 worse for them),
  typewell-`Geology` classifier (they dropped it; we measured `Geology` absent from the test schema).
- **Do not re-attempt** from their stack: G11 three-thirds TVT-vs-MD fit (covered by M4), G13/G14
  landing-state and well-length features (N4 measured CV R^2 0.074 for this feature class), G15 vintage
  `seq_id` features (leakage-adjacent, needs a rules check first).
- Next runnable: **`n5_typewell_fingerprint_families`** (priority 160, time-boxed 30 min).
