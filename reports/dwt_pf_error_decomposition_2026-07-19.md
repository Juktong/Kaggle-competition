# ROGII — DWT+PF error decomposition (Direction A, 2026-07-19)

Sprint session `3f11942e`→`4d6cd351`. Purpose: characterise the error structure of the honest slot
**54804893 (DWT+PF 0.5/0.5, OOF 9.2969)** and produce the feature table that Direction B's selector consumes.
Script `scripts/dwt_pf_error_decomposition.py`; output `decomp_features.npz` (3,783,989 rows × 15 features +
well id, 65 MB, float32). Neutral technical language.

## 1. Pipeline validation
Pooled toe RMSE reproduces the known values exactly → the aligned table is correct:
`DWT 10.3987 · PF 10.9952 · BLEND(0.5) 9.2969`.

## 2. Who wins, per row (3.78 M toe rows)
| winner | share |
|---|---|
| PF closest | **46.2 %** |
| DWT closest | 37.7 % |
| blend closest (beats both) | 16.2 % |

- **both fail (|err| > 10 ft for BOTH models): 8.6 % of rows** — a genuine hard tail neither model covers;
  this is where any new decorrelated model would have to contribute.
- PF wins more rows than DWT, yet DWT has the lower pooled RMSE (10.40 vs 11.00) → PF's losses are larger in
  magnitude (heavier tail), DWT's are more uniform. The blend exploits exactly this asymmetry.

## 3. Error vs toe distance (distance from the last known heel row, MD)
| quartile | n | DWT | PF | BLEND | PF-win rate |
|---|---|---|---|---|---|
| Q1 (nearest) | 945,793 | 5.16 | 5.47 | **4.60** | 51.7 % |
| Q2 | 945,770 | 8.90 | 9.85 | **8.11** | 54.1 % |
| Q3 | 946,029 | 11.60 | 12.15 | **10.27** | 55.4 % |
| Q4 (farthest) | 946,397 | 13.86 | 14.45 | **12.38** | 57.6 % |

- Error grows monotonically with toe distance for both models (extrapolation decay), and **the blend beats
  BOTH models in every quartile** — the blend's advantage is structural, not concentrated in one segment.
- PF's win-rate rises mildly with distance (51.7 → 57.6 %), i.e. the PF's sequential tracking degrades more
  gracefully far from the heel than the GBM's regression, but not enough to justify distance-based routing
  (see §4 and Direction C/B).

## 4. Directional feature screen (the input to B) — all features are non-directional at full power
Correlation of each **test-available** feature with `(|err_DWT| − |err_PF|)` (positive ⇒ PF is the better
model at that row). A usable router needs a feature that predicts *which* model to trust:

| feature | corr | | feature | corr |
|---|---|---|---|---|
| heel_drift | +0.0613 | | gr_missing | +0.0170 |
| n_eval | +0.0602 | | row_frac | +0.0166 |
| toe_dist_md | +0.0410 | | tw_pressure* | +0.0034 |
| **gbm_disagree** | **+0.0300** | | curvature | +0.0017 |
| gr_rough | −0.0109 | | z_span | −0.0061 |
| tw_range | −0.0117 | | | |

- **Max |corr| = 0.061** across 3.78 M rows. Notably **`gbm_disagree` (per-row std of lightgbm-1/2/3, the
  asymmetric "GBM confidence" proxy) is only +0.030** → the GBM-disagreement hypothesis is **not supported**:
  knowing the GBM ensemble disagrees does not tell you to prefer the PF.
- This confirms and extends the earlier router negative to a larger, explicitly *asymmetric* feature set.
  The one asymmetric feature still outstanding is **PF seed-spread uncertainty (`pf_unc`)**, measured by the
  full PF-uncertainty OOF run (Direction B).
- *`tw_pressure` is derived from the truth (distance of the true TVT to the typewell range edge) → it is
  **diagnostic only and must never enter a deployable selector**. It is retained in the table for error
  analysis and is excluded from all selector inputs.

## 5. What this means for the sprint
1. The blend's advantage is broad (all toe-distance quartiles, both winner-classes) — consistent with the
   variance-reduction mechanism, not a segment-specific effect.
2. **Row-level routing between DWT and PF has no signal in any test-available feature measured so far**
   (|corr| ≤ 0.061), so a selector that picks a model per row is not supportable from these inputs.
3. The addressable headroom is the **8.6 % both-fail tail** — a genuinely different model (Directions C/D/E/F)
   would need to cover those rows; improving the DWT/PF mixture alone cannot.

Feature table for downstream use: `decomp_features.npz` (keys: dwt, pf, blend, truth, row_frac, toe_dist_md,
gr_rough, curvature, gbm_disagree, heel_drift, n_eval, gr_missing, tw_range, tw_pressure*, z_span, well).
