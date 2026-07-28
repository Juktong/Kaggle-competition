

## Round 13 — 2026-07-28 12:48 UTC (autopilot `n1_geometry_bounded_alignment`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. `can_submit=false`; no submission.

**Negative result, plus an amendment to a same-day claim.**

The constraint is genuinely non-parametric: `dTVT = -dZ + tan(delta)*dH` with `dZ`/`dH` exact from X/Y/Z,
giving a hard admissible interval per DP transition. Measured LOCAL dip over the DP's 10-row step (80
wells, 51,514 transitions): |dip| p50 1.97 deg, p90 3.59, p95 5.43, p99 27.05 — so 4 deg admits 92.1% of
true transitions, 8 deg 96.4%. (`new_direction_search` M4's +/-3.7 deg was WHOLE-WELL dip; the local
distribution the DP needs is wider.)

The effect was decomposed into **centring** (regulariser referenced to -dZ, i.e. penalise dip not TVT
movement) and **bounding** (the hard interval), sharing one emission matrix and one penalty scale.

Two harness defects were caught by the smoke and fixed before any result was read: the penalty had been
normalised by band width (making a narrow band up to 60x more regularised — not a one-factor change), and
the binding metric compared against an already-penalised optimum, reporting an impossible 0.0%.

**12 wells suggested a large win** — `bounded 8 deg` at lam=2 reached **9.412** vs G3.2's 12.527.
**40 wells (strict superset) removed it** — the same config gives **15.569**, the best arm becomes the
**unbounded control** (12.518), and every geometry-aware arm is worse. The 9.412 was a minimum selected
over 20 configurations on 12 wells: the project's recorded failure mode.

**Nested validation decided it.** Config chosen on 20 wells, scored on the disjoint 20, both ways:
pooled held-out **DP 13.644 vs flat-anchor 12.722 — does not beat flat**; beats flat on 37.5% of wells.
Nested selection never picks a geometry-aware arm.

**Amendment to G3.2 (recorded earlier the same day).** Its "DP beats the flat anchor, 12.527 vs 13.103"
also selected lam on the wells it reported. With nesting on 40 wells the DP does not beat flat. What
stands from G3.2 is the scorer's held-out pair AUC 0.7242 vs NCC 0.5010; what is withdrawn is the DP
claim. `reports/g32_learned_alignment_smoke_2026-07-28.md` is amended in place.

**The one thing the band buys:** stability, not accuracy. At lam=1 the unbounded DP diverges (42.359)
while bounded arms stay at 14-16 across the whole grid. It removes the catastrophic tail without moving
the optimum.

Task step 5 ("do not scale up unless the band clearly improves on 12.527") is not met — no scale-up.
Report: `reports/n1_geometry_bounded_alignment_2026-07-28.md`. Next queued: `n3_multiscale_gr_matching` (140).
