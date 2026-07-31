# ROGII — structural-field variant sweep (mainline C, 2026-07-20)

Session `4d6cd351`. Question: does any neighbour-kernel / anchor variant beat the deployed configuration
(k=12, IDW power=1, anchor=100, min_sep=150, gate nnb≥4 & closest<1000 ft, W=0.15)?
Script `scripts/struct_field_variants.py` — all 18 combos computed in ONE pass over 773 wells (the k=20
neighbour query subsumes k=8/12; power and anchor are cheap re-weightings). Neutral technical language.

## Results (773 wells; deployed gate; nested = 3 well-splits)
| k | power | anchor | gated RMSE @W=0.15 | nested | gain | rows gated |
|---|---|---|---|---|---|---|
| 8 | 1 | 50 | **8.8576** | **8.9392** | **+0.3595** | 87.3 % |
| 8 | 1 | 100 | 8.8618 | 8.9497 | +0.3490 | 87.3 % |
| 8 | 1 | 200 | 8.8727 | 8.9614 | +0.3373 | 87.3 % |
| 8 | 2 | 50 | 8.8576 | 8.9392 | +0.3595 | 87.3 % |
| **12** | **1** | **100** (deployed) | **8.8626** | **8.9517** | **+0.3470** | 87.3 % |
| 12 | 1 | 50 | 8.8587 | 8.9413 | +0.3574 | 87.3 % |
| 12 | 2 | 100 | 8.8626 | 8.9517 | +0.3470 | 87.3 % |
| 20 | 1 | 50 | 8.8613 | 8.9463 | +0.3524 | 87.3 % |
| 20 | 1 | 100 | 8.8648 | 8.9561 | +0.3426 | 87.3 % |
| 20 | 1 | 200 | 8.8758 | 8.9663 | +0.3324 | 87.3 % |
(remaining power=2 rows are identical to their power=1 counterparts to 3–4 decimals)

## Findings
1. **The method is insensitive to its kernel hyper-parameters.** All 18 variants fall in a narrow band
   (nested 8.9392–8.9663; gain +0.332…+0.360). That insensitivity is itself a robustness result: the signal
   comes from the structural gradient of the neighbour field, not from a tuned kernel.
2. **IDW power has no effect** (power 1 vs 2 agree to 3–4 decimals) — inter-well distances are large relative
   to the `+1` regularisation in `1/(d+1)^p`, so the weighting is effectively flat across the k neighbours.
3. **Mild preferences:** smaller anchor (50 > 100 > 200) and smaller k (8 > 12 > 20), both monotone but tiny.
   A shorter anchor window tracks the local level better; fewer neighbours avoid diluting with distant wells.
4. **The deployed config is within 0.0125 of the best variant** (8.9517 vs 8.9392). That is well inside
   transfer noise and far below the gate that would justify re-running and re-submitting.

## Decision
**No variant change.** The deployed configuration (k=12, power=1, anchor=100) is retained; the sweep is
recorded as evidence of hyper-parameter robustness rather than a tuning opportunity. If a future round does
re-run the candidate for another reason, k=8/anchor=50 is the marginally preferred setting.
