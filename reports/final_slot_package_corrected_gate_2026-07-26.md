

## Sensitivity addendum — the scored scale's own variance (N4, 2026-07-28)

`reports/n4_conformal_well_uncertainty_2026-07-28.md` measured, for the deployed honest line held FIXED,
the pooled row-weighted RMSE of a random 3-well draw:

```
5th 3.491   25th 5.040   median 6.708   75th 8.990   95th 15.138
```

The scored quantity itself spans more than 4x between its 5th and 95th percentiles for an unchanged model.
Two consequences for this package:

1. The public gaps that separate the frontier family from the honest line (6.563 vs 7.891, i.e. 1.33) are
   comfortably larger than the config-variance floor (~0.115) but are **not** large relative to 3-well
   draw variance. The *ranking* used here is still the best available evidence — it is measured on the
   same 3 wells for every candidate, so draw variance is common-mode and cancels — but no absolute
   private score should be inferred from it.
2. The recommendation is unchanged: `54922806` + `54844628` under score-first, diversity-first and
   provenance-first. Draw variance strengthens the diversity argument, since it raises the value of
   holding two members that fail independently.

Also measured: OOF on the 3 test wells 4.756 vs public 7.891 = **1.659x**. OOF-derived bounds are not
leaderboard bounds and must not be quoted as such in this package.
