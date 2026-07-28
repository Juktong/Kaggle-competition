
## 2026-07-28 update (frontier variant matrix lite)

- **Static diff completed at zero cost** from the existing full-run intermediates. Corrected a published
  error: the **bimodal hedge is the largest post-SP45 effect** (+2.0 ft on all 4,301 rows of `00e12e8b`),
  not zero as A5 recorded. G1.3's ~0.047 becomes a joint bound over two stages.
- **No variant promoted** — prefix-aggressive would re-confirm G3.5; bimodal fires on 1 of 3 wells so any
  public delta sits under the ~0.115 noise floor. 0 quota.
- Concrete next variant if revisited: lower `skip_separation` so the bimodal hedge also fires on
  `00bbac68` (separation 3.594 ft) — a multi-well effect would be resolvable.
- Next runnable: **`new_direction_search`** (priority 90).

