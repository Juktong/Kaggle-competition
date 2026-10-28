# ROGII submission ledger — 2026-07-21

Daily submissions used: **1 of 5**. Banked honest slot unchanged: `54844628`, public **7.891**.

## 2026-07-21 — `54878409` anisotropic structural field

| field | value |
|---|---|
| ref | **54878409** |
| public score | **7.953** (banked `54844628` = 7.891; lower is better) |
| outcome | **worse by 0.062** — OOF predicted +0.1802 better |
| kernel | `joezzzzz/rogii-struct-aniso-codex` v1 (kernels-only code submission) |
| commit | `2f35be1` |
| config | `A=50`, `W=0.25`, gate `nnb>=4 AND closest_surviving < 1000 ft` |
| local evidence at submission | nested (A,W) +0.1606; bootstrap(760-well) 5th +0.0490, 99% positive |
| why it was worth a slot | first candidate of the queue to meet the pre-registered gate on both conditions |
| post-mortem | `reports/mismatch_audit_54878409_2026-07-21.md` |

**Root cause of the miss:** the bootstrap resampled 760 wells (the sampling distribution of a 760-well
mean) while the competition evaluates **3 wells**. At the real scale the same effect is negative in
**42%** of draws. Per-well gain is median +0.000, std 1.301. The gate's stability condition therefore
never constrained the quantity that decides the outcome.

**Standing correction:** all future stability claims must bootstrap at the number of wells actually
scored. The visible-well check is not independent confirmation — it reuses train copies with a different
heel/toe split.

**Final-2 status unchanged:** `54844628` (7.891) remains the honest slot. The test set is 3 wells, so
public and private are row splits of the *same* wells and are strongly correlated (within-well residual
autocorrelation +0.9998 at lag 1), which makes the public result informative about private rather than
dismissable noise.

Daily submissions used 2026-07-21: **1 of 5**.
