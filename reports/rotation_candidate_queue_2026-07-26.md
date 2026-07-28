

## 2026-07-28 update (N4 conformal per-well uncertainty)

- **Closed: per-well confidence gating on test-available features.** CV R^2 0.074 on log(per-well OOF
  RMSE); conditional conformal intervals are wider than the unconditional one at matched coverage
  (13.76/13.97 vs 13.43). A gate built on `nnb` / closest-mate / prefix-fraction / GR-std / geometry would
  be close to random. Do not re-attempt without a materially different feature source.
- **Retained:** marginal conformal bound for the honest line — 90% of wells <= 13.43 ft, 95% <= 17.53 ft,
  coverage verified out-of-sample. Table at `rogii_sprint_shared/tmp/n4_well_uncertainty.csv`.
- **New constraint on all future validation:** for one fixed model, a random 3-well draw pools to
  5th 3.491 / median 6.708 / 95th 15.138. Quote this whenever a small margin is proposed.
- **New measured transfer gap:** OOF 4.756 on the 3 test wells vs public 7.891 = 1.659x. OOF-based bounds
  are not leaderboard bounds.
- Next runnable: **`n2_increment_structural_field`** (priority 120) — the only queued item with a
  submission path.
