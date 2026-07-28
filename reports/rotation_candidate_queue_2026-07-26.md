

## 2026-07-28 update (N1 geometry-bounded alignment)

- **Closed: the geometry-derived admissible band.** It binds 83-91% of transitions (not inert), but on 40
  eval wells every geometry-aware arm is worse than the unbounded control, and nested selection never
  picks one. Pooled held-out DP 13.644 vs flat-anchor 12.722.
- **Amended: G3.2's "DP beats the flat anchor".** That comparison selected lam on the wells it reported;
  with nesting on 40 wells it does not beat flat. The scorer's AUC 0.7242 vs NCC 0.5010 stands.
- **New standing caution:** the 12-well eval set used by G3.1/G3.2/N1 is small enough that a 20-config
  sweep produced an apparent 25% gain (9.412) that vanished on 40 wells. Any future alignment result must
  be nested and reported on >=40 wells.
- **Retained:** the geometric bound gives stability at weak regularisation (unbounded diverges to 42.359
  at lam=1; bounded stays 14-16). Useful if a future formulation needs a weak regulariser.
- Next runnable: **`n3_multiscale_gr_matching`** (priority 140).
