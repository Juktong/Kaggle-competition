
## Round 10 — 2026-07-28 09:03 UTC (autopilot `new_direction_search`)

Live refresh: quota **0/5**, no Kaggle kernels running, branch in sync. `can_submit=false` for this task,
so no submission was possible or attempted.

Five cheap measurements were run before listing any direction, and three of them changed a ranking:

- **M1 test-available inventory.** `test/*__horizontal_well.csv` = `MD,X,Y,Z,GR,TVT_input`;
  `test/*__typewell.csv` = `TVT,GR`. Establishes by direct check that **`Geology` is absent from the test
  typewell schema** — train-only supervision, not a test input.
- **M2 images ruled out.** 773 train PNGs, **0 test PNGs**. The image is a render of the CSVs; the only
  non-CSV content is the well/typewell name in the title, unavailable at prediction time.
- **M3 typewell grouping capped.** 773 wells -> 752 distinct typewell files (group sizes {1:739, 2:12,
  10:1}); **none of the 3 test wells matches any train typewell byte-identically.**
- **M4 single-dip geometric reparametrization CLOSED on evidence.** `dTVT = -dZ + tan(delta)*dH` with
  `dZ`/`dH` exact at every row. Oracle whole-well dip reaches **7.65** row-weighted RMSE vs a flat anchor
  of **15.91**, but every honest estimator of that one parameter is far worse: prefix-fit **80.29**,
  recency-fit **39.57**. Fifth independent instance of large-oracle / no-achievable-margin.
- **M5 naive dip-field fails.** Ungated neighbour plane: 64.57 standalone, 18.23 at W=0.15, vs flat 15.98;
  3-well bootstrap P(gain>0) = **0.314**. This does not contradict the deployed field's +0.436 (which is
  group-anchored, IDW-weighted and gated); it isolates the refined form that remains open.

Six directions queued at priorities **110–160**: N4 conformal per-well uncertainty, N2 increment-target
structural field (the only one with a submission path), N1 geometry-bounded alignment DP, N3 multi-scale
GR matching, N6 second public-solution audit, N5 time-boxed typewell fingerprint. Four directions
explicitly **not** queued with reasons: train-only images, RL geosteering, azimuthal-GR dip inversion,
standalone semantic-segmentation correlation.

Report: `reports/new_direction_search_2026-07-28.md`. Scripts: `scripts/nds_geometry_reparam_probe.py`,
`scripts/nds_dipfield_probe.py`. Next queued: `status_summary_for_user` (100).
