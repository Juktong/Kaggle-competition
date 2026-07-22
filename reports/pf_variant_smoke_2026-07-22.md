# PF variant smoke (2026-07-22)

Direction 6. Do alternative PF parameterisations decorrelate from and/or strengthen the deployed PF?
Tool: `scripts/pf_variant_smoke.py`.

## Smoke (24 wells, 16 seeds)

```
deployed PF                RMSE 10.9232
v1 wider emission (gs×1.6) RMSE 10.6155   corr(err, base_err) = 0.885
v2 trim + process-noise    RMSE 10.8959   corr(err, base_err) = 0.936
blend base + 0.5·(v1−base) RMSE 10.4532   (+0.47 vs deployed PF)
blend base + 0.3·(v1−base) RMSE 10.5675   (+0.36)
```

## Finding

**Widening the GR emission width (gs × 1.6) makes the PF both stronger standalone (+0.31) and partly
decorrelated (corr 0.885).** The deployed PF clips the emission std `gs` to [10, 60]; widening it lets
the likelihood tolerate larger GR mismatches, which helps on wells where the narrow window over-commits.
This is the only direction this round with a positive standalone signal.

`v2` (trimmed aggregation + more process noise) is neither stronger nor decorrelated — closed.

## Scale and transfer

The PF is 0.5 of `base = 0.5·DWT + 0.5·PF`, and the structural blend dilutes further, so a +0.31 PF
improvement is ~**+0.15 at the full-pipeline level** — squarely in the small-margin regime that direction
C showed does **not** transfer to the leaderboard. So even a confirmed improvement here is not expected
to be submittable, and no submission is made from the smoke.

## Status

A medium smoke (60 wells, 32 seeds) is running to confirm the standalone signal holds at scale. If it
does, a full 773-well PF re-run at `gs×1.6` is the top knowledge-building item (hours of CPU), explicitly
flagged as below the transfer threshold rather than as a submission candidate.

*(Medium-smoke result appended when complete.)*
