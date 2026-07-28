

---

## AMENDMENT (same day, from N1) — the "DP beats the flat anchor" claim does not survive nesting

This report recorded "its DP beats the flat-anchor baseline (12.527 vs 13.103, interior optimum at
lam=60)". That comparison selected `lam` on the same 12 eval wells it reported.

`reports/n1_geometry_bounded_alignment_2026-07-28.md` re-ran the same DP on **40 eval wells** (a strict
superset) with the `lam` choice **nested** — chosen on one half of the wells, scored on the disjoint half:

```
POOLED HELD-OUT: DP 13.644   flat-anchor 12.722   -> does NOT beat flat
per-well: DP beats flat on 37.5% of held-out wells (n=40)
```

**What stands:** the learned scorer carries real signal — AUC **0.7242** vs NCC **0.5010** on held-out
pairs is a clean comparison and is unaffected.

**What is withdrawn:** "the DP beats the flat anchor". Under nested hyper-parameter selection it does
not. The gap in this line is in the *transition model*, not the emission.
