

## Round 12 — 2026-07-28 11:48 UTC (autopilot `n2_increment_structural_field`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. **No submission** — the 3-well gate
fails for every variant, so the task's submit step never triggers.

**The task's premise turned out to be wrong, and that is the round's main finding.** Reading the builder
behind `54844628` (`struct_oof_produce.py`), the anchor is `mean(r_true - r_pred)` over the target's own
last 100 known heel rows, so

    pred = ( r_pred - mean(r_pred over heel) ) + mean(r_true over heel) - Z

The level of `r_pred` cancels **exactly**: the deployed field is already heel-anchored and
level-invariant, i.e. **already an increment estimator**. A literal level->increment swap is a no-op. That
"interpolates the level" description came from our own `new_direction_search` round earlier the same day
and is corrected here.

Preflight was clean at both scales: the reimplementation reproduces the banked `struct_oof.npz` to
`max|d| = 0.00000000`, and on the **full 760-well split** it reproduces the banked pooled **8.8626** to
`-0.0000`. A tree-caching optimisation was verified byte-identical before the long run.

**The mechanism that could have made a reformulation matter does not occur.** Full split: the
nearest-point well identity switches on **0.0021** of consecutive row pairs (median 0.0001), and
**99.38%** of the k=12 contributing points share the nearest point's well (p10 0.9929). The neighbourhood
is effectively single-well — these are parallel laterals on a pad — so there is no cross-well level mixing
to remove.

Two variants measured on the full split, both failing the 3-well gate (20,000 draws):

```
struct_increment_iso  (one-factor: identical selection/weights, level -> within-well increment)
    pooled 8.9629  (-0.1003)  5th -1.7148  median 3-well draw -0.0001  P(gain>0) 0.4602  GATE FAIL
struct_increment      (per-well increment averaged across all surviving wells)
    pooled 10.5466 (-1.6840)  5th -5.5224  median 3-well draw -1.4046  P(gain>0) 0.1938  GATE FAIL
```

Smoke (38 wells) and full agree in sign and magnitude (-0.18 -> -0.10; -1.90 -> -1.68).

**Mechanistic explanation, worth keeping.** The deployed anchor subtracts *the same estimator's own value*
at the heel, so the reference cancels exactly and the increment is self-consistent. Both variants
substitute a *different* reference at the heel, which does not cancel and reintroduces a per-well level
error; the damage scales with how far the new reference sits from the original. The deployed construction
is not merely equivalent to an increment estimator — it is the **correctly referenced** one.

Direction closed. Report: `reports/n2_increment_structural_field_2026-07-28.md`. Scripts:
`scripts/n2_increment_structural_field.py`, `scripts/n2_eval_increment.py`. Next queued:
`n1_geometry_bounded_alignment` (130).
