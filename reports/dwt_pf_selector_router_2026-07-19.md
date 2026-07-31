# ROGII — DWT+PF selector / router with asymmetric confidence (Direction B, 2026-07-19)

Sprint session `3f11942e`→`4d6cd351`. Question: can a per-row/per-well selector beat the fixed 0.5 DWT+PF
blend (honest OOF **9.2969**, submission 54804893)? Neutral technical language.

## 1. Why this was worth retrying
Earlier router work (session `1a07ce3e`) found no test-available feature predicting **which** of DWT/PF is
better, and a nested router that was worse than the fixed blend. But every feature tested there was
**symmetric** (|PF−DWT| disagreement, GR roughness, curvature, heel-drift) — such features flag *hardness*,
not *direction*. This sprint tested the untested **asymmetric, model-specific confidence** class:
**(i) GBM per-model disagreement** and **(ii) PF seed-spread uncertainty**.

## 2. GBM disagreement — REFUTED at full power
From Direction A's full 773-well table (3,783,989 rows): `gbm_disagree` = per-row std of the
lightgbm-1/2/3 OOF predictions. Correlation with `(|err_DWT| − |err_PF|)` = **+0.0300**. Every other
test-available feature is also ≤ |0.061|. Knowing the GBM ensemble disagrees does **not** indicate that the PF
should be preferred. Hypothesis (i) is not supported.

## 3. PF seed-spread uncertainty — promising in pooled form, does NOT survive nesting
A dedicated OOF harness (`scripts/pf_uncertainty_oof.py`) re-implements the PF ensemble loop to retain, per
row, the **likelihood-weighted standard deviation across seeds** (`unc`) and, per well, the seed
log-likelihood dispersion (`likdisp`). Tiny smoke PASS (3 wells, NS=4: unc mean 1.78, range [0.001, 8.06]).

**Partial result (96 wells / 494,033 rows, NS=24):**
- corr(`pf_unc`, eD−eP) = **+0.169** — sign opposite to the naive hypothesis: where the PF is *less* certain,
  the PF is nonetheless the better model, because corr(`pf_unc`, **eD**) = **+0.302** exceeds
  corr(`pf_unc`, eP) = +0.138. PF uncertainty is mostly a hardness signal that happens to hurt DWT more.
- Fitted optimal PF weight **a\*** varies strongly across `pf_unc` deciles — **spread 0.587** (d7 ≈ 0.29 →
  d9 ≈ 0.88; in the top decile DWT = 20.58 while PF = 9.30), versus a roughly constant 0.42–0.51 for every
  previously-tested symmetric feature. On its face this is the first candidate routing signal in the project.

**Nested test (5 well-splits, same rows) — the signal does not generalise:**
| method | RMSE |
|---|---|
| fixed 0.5 (no fitting) | **10.2625** |
| nested global-a (refit one weight) | 10.3607 |
| nested `pf_unc` decile router | 10.3161 |

The router **loses to the un-fitted fixed 0.5 by 0.054**, with per-seed swings of −0.04…+0.17. Notably even
refitting a *single global weight* is worse than 0.5 here, i.e. at 96 wells **any** fitting overfits, so the
pooled a\*-spread was fitting optimism rather than a generalising signal.

## 4. Status
- Hypothesis (i) GBM disagreement: **refuted at full power**.
- Hypothesis (ii) PF uncertainty: **not supported at 96 wells**; the full 773-well PF-uncertainty OOF is still
  running (detached, checkpointed, `rogii_sprint_shared/tmp/pf_unc.npz`) so the nested test can be repeated at
  full power, where fitting is better conditioned (the full-set global refit *does* help: a = 0.44 → 9.2775
  vs 0.5 → 9.2969). That re-test is the one open item in B.
- **No selector candidate produced; the honest slot 54804893 is unchanged and the fixed 0.5 blend remains the
  deployable optimum for the DWT/PF mixture.**

## 5. Reusable products
- `scripts/pf_uncertainty_oof.py` — PF OOF retaining per-row seed-spread + per-well likelihood dispersion
  (checkpointed/resumable; the only source of PF confidence in the project).
- `scripts/dwt_pf_error_decomposition.py` + `decomp_features.npz` — 3.78 M-row feature table used by B and
  reusable by any future selector/ranker work.
