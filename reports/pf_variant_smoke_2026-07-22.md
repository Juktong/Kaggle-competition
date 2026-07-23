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

## Medium smoke result (60 wells, 32 seeds — completed 2026-07-22 04:54; recorded 2026-07-23)

```
deployed PF                RMSE 10.8517
v1 wider emission (gs×1.6) RMSE 10.8171   corr(err, base_err) = 0.8755
v2 trim + process-noise    RMSE 10.8682   corr = 0.9290
blend base + 0.5·(v1−base) RMSE 10.4897   (+0.3619 vs deployed PF)
blend base + 0.3·(v1−base) RMSE 10.5527   (+0.2989)
```

**The standalone advantage did not hold at scale:** +0.31 on 24 wells shrank to **+0.035** on 60 wells —
within noise. What remains is a *blend* gain (+0.36 at the PF-component level) driven by partial
decorrelation (corr 0.876), which after the 0.5-weight base and structural dilution is ~0.18 at pipeline
level — inside the small-margin regime that direction C showed does not transfer to the leaderboard.

## Disposition (2026-07-23)

Closed as **no standalone improvement; blend-level gain below the transfer threshold.** The full
773-well re-run is de-prioritised: its expected value was contingent on the standalone signal, which the
medium smoke removed. A note on process: the previous status line ("medium smoke running") went stale
after the session's background waiter was killed — the smoke had in fact completed; this section records
the actual result.
