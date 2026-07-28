

## Round 16 — 2026-07-28 13:33 UTC (autopilot `n5_typewell_fingerprint_families`)

Live refresh: quota **0/5**, no Kaggle kernel running, branch in sync. `can_submit=false`; no submission.
Time-boxed to 30 minutes; completed in ~2 minutes of compute.

**The fingerprint adds nothing over the spatial gate already in production — direction closed** (the
task's own step 3). No router was built, as instructed.

Correlating each test typewell's GR-vs-TVT curve against all 773 train typewells on the overlapping TVT
range gives a sharply **bimodal** distribution: a block at exactly 1.0000 and a bulk near 0 (p50 between
-0.05 and +0.19). Typewells are either the same curve or unrelated — no middle ground for a similarity
ranking to exploit. All top-5 matches per test well are already in the deployed **surviving**-neighbour
set (5/5 for every well), and the deployed gate already passes on all three (same-group 13/40/13, closest
mate 292/295/354 ft).

**The deciding test.** The deployed group key `round(max(typewell.TVT), 1)` is truncation-sensitive by
construction, so the worry was that wells sharing an underlying typewell but truncated differently get
different keys. Measured directly, the near-identical set and the same-group set are **identical in both
directions** for all three test wells (13/13, 40/40, 13/13; zero fingerprint-only, zero group-only).

**Correction to M3.** M3 hashed whole files and reported 0/3 test wells matching, concluding grouping was
capped. The hashes measure **file** identity, not **curve** identity — files are truncated to different
TVT ranges. On the overlap there are 13/40/13 near-identical train typewells per test well, so typewell
sharing is **common, not rare**. M3 is amended in place; its conclusion (direction not worth developing)
survives for a different reason than it stated.

**Positive byproduct:** the deployed group key is validated as a lossless proxy for typewell-curve
identity on the scored wells. This bears on the queued `n8_azimuth_matched_neighbours` — the neighbour SET
is correctly identified, so grouping is not the weak link there; any gain must come from the weighting,
not the membership.

Report: `reports/n5_typewell_fingerprint_families_2026-07-28.md`. Next queued:
`n8_azimuth_matched_neighbours` (170).
