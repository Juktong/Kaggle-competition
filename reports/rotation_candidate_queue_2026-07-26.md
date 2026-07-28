

## 2026-07-28 update (N3 multi-scale GR matching)

- **Closed: coarse-to-fine wavelet decomposition as the fix for the GR-scorer line.** No level exceeds
  G3.2's 0.7242; the raw band is best (0.7160) and AUC falls monotonically with coarser approximation
  (0.6573 at 16 ft). NCC is at chance in all 9 bands, so shape matching is not a scale problem.
- **Banked positive: typewell window TWH=1 (3 ft).** Held-out-WELL AUC 0.7655 +/- 0.0030 (5 seeds) vs
  0.7300 +/- 0.0028 at G3.2's TWH=8 — +0.0355, 8.7x seed noise. A **no-training** level score reaches
  0.7352, above G3.2's trained 0.7242. Available to any future alignment work.
- **New standing protocol rule:** scorer comparisons must split by WELL, not by pair. G3.2's pair split
  ranked the windows wrongly (chose TWH=32; the well split chooses TWH=1) and understated absolute AUC.
- Next runnable: **`n6_public_solution_audit`** (priority 150), then `n5` (160).
