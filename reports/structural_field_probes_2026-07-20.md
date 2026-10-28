# ROGII — structural-field probes 1–3 (2026-07-20)

Session `6bf66c88`. Run after direction D missed its gate, to test whether the deployed structural
configuration (per-well gate `nnb≥4 & closest<1000 ft`, flat `W=0.15`, isotropic IDW, `min_sep=150`) can be
improved. Incumbent honest slot **54844628**: public **7.891**, honest OOF **8.8626**. All comparisons are
nested by well; the fixed-weight reference (8.8626) and the nested-refit reference (8.9517) are both shown
because a nested scalar refit is honest but slightly pessimistic. Neutral technical language.

## Probe 1 — row-level weight *schedules* (by row position / toe distance) — NEGATIVE
Struct-vs-base error does shift with row position (ratio 1.94 → 1.63 from heel to toe), but no schedule
exploits it:
| scheme | nested |
|---|---|
| **flat 0.15 (refit scalar)** | **8.9517** |
| grow with row_frac (heavier at toe) | 8.9915 |
| decay with toe MD distance | 8.9761 |
| decay with row_frac (heavier near heel) | 9.0904 |

## Probe 2 — per-ROW nearest-neighbour distance gate/weight — NEGATIVE
The deployed gate uses a *per-well* closest-mate distance; this probe saved the true **per-row** nearest
neighbour distance (`scripts/struct_oof_rowdist.py`, 760 wells / 3,721,471 rows; median 389 ft, p10 197,
p90 1105 — real within-well variation) and tested row-level gates and decays:
| scheme | nested |
|---|---|
| **A) per-well gate + flat (reference)** | **8.9517** |
| B) per-row gate `nn_dist<400 ft` | 9.1197 |
| B) per-row gate `nn_dist<600 ft` | 9.0605 |
| B) per-row gate `nn_dist<800 ft` | 9.0254 |
| B) per-row gate `nn_dist<1200 ft` | 9.0023 |
| C) per-row decayed `1/(1+nn/1000)` | 8.9723 |
| C) per-row decayed `1/(1+nn/500)` | 8.9757 |
| C) per-row decayed `exp(-nn/800)` | 8.9906 |

**Informative pattern:** the row gates improve monotonically as they loosen (400 → 1200 ft), i.e. excluding
rows *removes* useful contribution. Once the **well** qualifies, the field helps even at larger row-level
distances — so well-level gating is the right granularity and row-level restriction is counter-productive.

## Probe 3 — typewell-group local dip plane — NEGATIVE
Fitted `r ≈ a + b·x + c·y` by ridge over nearby group-mates (radius 1500 ft, ≥200 pts, strided along the
toe), integrating only the gradient `(b, c)` from the target's own heel anchor
(`scripts/probe3_dip_plane.py`, 760 wells / 3,721,471 rows):
| model | standalone RMSE | nested (deployed pipeline) |
|---|---|---|
| struct IDW | 26.002 | **8.9517** |
| dip plane | **184.944** | 9.3193 |
| struct + dip (2 non-negative coefficients) | — | 8.9703 (**dip adds −0.0187**) |
corr(dip, struct) = +0.145 · corr(dip, base) = +0.045.

**Mechanism:** the dip plane integrates a fitted gradient along the entire trajectory, so error accumulates
with no reference beyond the heel anchor. The IDW instead reads the neighbour field's **absolute level at
every point** and then anchors. That per-point absolute reference is what makes IDW robust; pure gradient
integration lacks it, which is why the dip field is an order of magnitude worse standalone and does not
contribute even as a second, partly-decorrelated term.

## Conclusion
Three structurally different variant classes — row-position schedules, row-level distance gating, and an
anisotropic dip-plane field — all fail to improve on the deployed configuration. Combined with the earlier
18-combination hyper-parameter sweep (all within 0.013), the deployed structural field sits at a **local
optimum** for this method family. Further gains should come from a *different* channel, not from re-tuning
this one. **No submission from probes 1–3.**
