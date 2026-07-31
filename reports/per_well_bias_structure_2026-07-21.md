# Where the remaining error actually lives: per-well bias structure (2026-07-21)

Follow-on from direction 6's autocorrelation finding. This is the most consequential measurement of the
round: it locates the remaining error precisely, and it **downgrades proposal L1** (heel-residual bias
carry) before that proposal consumed a 2–4 h run.

Base: deployed honest slot `54844628`, 760 wells, 3,721,471 toe rows, OOF **8.8626**.
Scripts: `scripts/bias_carry_feasibility.py`, `scripts/bias_shape.py`.

## 1. The remaining error is a per-well offset, not noise

```
deployed RMSE                    8.8626
global mean shift (+0.383)       8.8544    gain +0.0083
ORACLE per-well bias removal     5.5784    gain +3.2843

per-well bias: std = 6.668 ft;  63.0% of wells |bias| > 2 ft;  31.6% > 5 ft
per-well bias = 60.3% of total residual variance
```

**60.3% of the remaining residual variance is a constant per-well TVT offset.** A global shift is worth
almost nothing (+0.0083), so this is genuinely per-well structure, not an overall calibration error.

This is the quantitative reason the group-anchored structural field was the largest historical win: it
is the only component that attacks the per-well offset directly, via its own heel anchor.

## 2. The bias carries within a well — measured as an upper bound

Measuring the bias on the first fraction *f* of a well's toe rows and carrying it into the remainder,
with the carry strength λ fit **nested by well**:

| f | corr(early bias, later bias) | nested λ | later-rows RMSE, no carry → with carry | gain |
|---|---|---|---|---|
| 0.10 | +0.377 | 1.267 | 9.2938 → 8.8335 | **+0.4603** |
| 0.20 | +0.497 | 1.232 | 9.6796 → 8.7667 | **+0.9128** |
| 0.30 | +0.587 | 1.299 | 10.0458 → 8.6199 | **+1.4260** |

These are far above the +0.10 gate — but they are **upper bounds, not deployable results**, because they
use toe-row truth, which does not exist at test time. They were computed to decide whether proposal L1
justified its run. λ > 1 throughout indicates the carry is real and that a naive unit carry would
under-correct.

## 3. Why L1 does not inherit those numbers

At test time, truth stops at the heel. Two measurements determine what survives:

```
toe-start level offset      std  4.72 ft
start->end drift (slope)    std 13.28 ft     <- dominant term
linear fit explains median R2 = 0.271 of within-well residual variance
corr(level, slope) = -0.350

corr(first- 50-row bias, whole-well bias) = +0.144
corr(first-100-row bias, whole-well bias) = +0.213   -> explains  5% of variance
corr(first-200-row bias, whole-well bias) = +0.281
corr(first-500-row bias, whole-well bias) = +0.415   -> explains 17% of variance
```

The per-well bias is dominated by **drift accumulated along the toe** (slope std 13.28 ft) rather than by
a level offset present from the start (std 4.72 ft). A bias estimated from the earliest rows — the
closest available analogue to what heel rows could provide — explains only **5%** of whole-well bias
variance at 100 rows, rising to 17% at 500 rows.

Two further points make the deployable version weaker still:

1. **The existing anchor already removes the heel-measurable component.** The structural field's anchor
   is `mean(r_true − r_pred)` over the target's own last 100 known heel rows, and the PF is initialized
   at the heel. A bias measured on held-out heel rows would therefore reflect mostly anchor estimation
   noise, not un-removed structural offset — it is zero by construction of the current pipeline.
2. **Heel rows are further from the far toe** than an early-toe segment is, so the correlation would sit
   below the +0.21 measured at 100 rows.

**Conclusion: L1 is downgraded from the top proposal to a low-expected-value one.** The mechanism it
targets is real and large, but the part of it that is observable at test time has already been captured
by the current anchoring. The feasibility test cost ~4 minutes and avoided a 2–4 h run plus the
subsequent integration work.

The negative correlation between level and slope (−0.350) is a mean-reversion signature — wells that
start high tend to drift down — but exploiting it would require knowing the toe-start level, which is
equally unavailable at test time.

## 4. What this implies for the remaining search

The dominant remaining error is **per-well structural drift along the toe**, which cannot be observed
from the model's own error because no truth exists past the heel. It can only be reduced by better
information about where the wellbore actually sits relative to the geology.

That is a direct argument for the proposals that add **decorrelated structural information**, and against
any further post-processing of existing predictions:

- **promoted** — L4 anisotropic / dip-aware structural kernel (attacks drift, not level)
- **promoted** — L3 separate conservative path for the 12.7% currently-ungated rows
- **promoted** — L5 a third decorrelated forward model
- **downgraded** — L1 heel-residual bias carry (this report)
- **unchanged** — L2 seed scaling (K=48 in progress), L6 multi-seed DWT averaging

It also retroactively explains the whole round: directions 2, 3, 4, 6 and 7 all attempted to recover a
per-well offset from signals that do not contain it.

## 5. Reproduction

```bash
cd /home/ubuntu/workstation/JoeProject/Kaggle-competition
python3 scripts/bias_carry_feasibility.py    # section 2 (upper bounds)
python3 scripts/bias_shape.py                # section 3 (level vs drift decomposition)
```
Artifacts: `decomp_features.npz`, `struct_oof_rowdist.npz` in
`/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/`; logs in `reports/logs/`.
