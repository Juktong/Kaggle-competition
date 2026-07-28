

## Round 15 — 2026-07-28 13:18 UTC (autopilot `n6_public_solution_audit`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. `can_submit=false`; no submission,
no data import, no code execution from any external repository.

**BLOCKER on the named target.** The task names `aaryan2203/rogii-wellbore-geology-prediction-argon`;
that repository **does not exist** (`gh api` 404; the user's 5 repos are all unrelated; `gh search repos
"rogii argon"` returns nothing). The name reached our queue from a stale/fabricated web-search snippet in
the `new_direction_search` round. Blocker recorded, and the task's stated intent was executed against the
highest-signal real target: **`mycarta/rogii-geosteering-toolkit`** (MIT, methodology notes rather than a
notebook dump).

**Their pipeline is not ahead of ours** — their own note records "OOF 10.5 and the public LB has clones
around 12" against our 8.8626 / 7.891 / 6.563. The repository is a source of formulations and
cross-checks, not of a stronger pipeline.

**The finding that pays for the audit — within-well TVT-Z decoupling.** They measure the global
TVT-vs-Z r = -0.96 as a BETWEEN-well structural signal, with the per-well **lateral-only slope +0.057**
(dZ ~70-125 ft across the eval zone vs dTVT ~5-13 ft). This independently explains two of our own
negatives from the same day:
  - `new_direction_search` M4: our geometry-only arm imposed slope -1 and scored 107.49 vs a flat anchor
    of 15.91. If the true within-lateral slope is ~0, -1 is close to the worst available choice.
  - N1's centring arm: centring the DP on c = -dZ/STEP presumes the formation is flat so TVT moves
    one-for-one against Z; on 40 wells it hurt (15.636 vs unbounded 12.518). Near-zero true slope means
    that centring systematically overcorrects. N1 recorded the effect; this supplies the mechanism.

**Three independent confirmations of our closed lines:** Catch22 well-level features made their model
+0.476 RMSE worse (matches our closed SSL/ROCKET line); they DROPPED the typewell-`Geology` classifier
(matches our M1 finding that `Geology` is absent from the test schema); and they rejected spatial
block-CV because validation wells are spatially interleaved with training — interpolation, not
extrapolation, which leans toward the H-visible branch of our final-slot framing.

**Three formulations queued** (absent from our ledger and cheap): `n8_azimuth_matched_neighbours` (170),
`n7_q3d_tortuosity_features` (180), `n9_self_correlation_prefix_template` (190).

Report: `reports/n6_public_solution_audit_2026-07-28.md`. Next queued: `n5_typewell_fingerprint_families` (160).
