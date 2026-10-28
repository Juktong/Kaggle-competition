# N5 — typewell-fingerprint well families (time-boxed diagnostic), 2026-07-28

Autopilot task `n5_typewell_fingerprint_families` (`requires_gpu=false`, `can_submit=false`,
`max_submit_cost=0`, time-boxed to 30 minutes). Script: `scripts/n5_typewell_fingerprint.py`.
Log: `reports/logs/n5_typewell_fingerprint_2026-07-28.log`. Completed inside the box (~2 min of compute).
No submission; quota untouched at 0/5.

**Result: the fingerprint adds nothing over the spatial gate already in production. Direction closed.**
The round also corrects the framing of the M3 measurement that motivated it, and it independently
validates the deployed grouping key.

## 1. Top-5 matches per test well

Each test typewell's GR-vs-TVT curve was resampled onto a common 1 ft grid over the overlapping TVT range
with every train typewell (minimum 50 ft of overlap) and Pearson-correlated.

The 3 test wells also appear in `train/` under the same id (a different heel/toe split of the same well).
That copy is a trivial self-match, reported separately and never counted as a discovered analogue.

```
=== 000d7d20  (group key 11871.5, 505 candidates with >=50 ft overlap) ===
  SELF-MATCH (own train copy): corr 1.0000, rank 1 of 505 -- excluded
  train well      corr    overlap  same_group  xy_sep_ft
  ee4aecac      1.0000      557ft        True      11691
  8cc21f01      1.0000      648ft        True      18207
  a056d01e      1.0000      648ft        True      10543
  1295a25b      1.0000      648ft        True      10812
  1d3fbf02      1.0000      595ft        True      18993
  non-self corr distribution: max 1.0000  p99 1.0000  p50 0.1885

=== 00bbac68  (group key 12367.0, 413 candidates) ===
  SELF-MATCH: corr 1.0000, rank 25 of 413 -- excluded
  2ab29395 1.0000 | 2f19d536 1.0000 | da2d4d7c 1.0000 | ab18d3fc 1.0000 | 3bfee975 1.0000   (all same_group)
  non-self corr distribution: max 1.0000  p99 1.0000  p50 0.0689

=== 00e12e8b  (group key 11871.5, 707 candidates) ===
  SELF-MATCH: corr 1.0000, rank 14 of 707 -- excluded
  000d7d20 1.0000 | 389ae58f 1.0000 | e5ff9fd2 1.0000 | 1d3fbf02 1.0000 | 8cc21f01 1.0000  (all same_group)
  non-self corr distribution: max 1.0000  p99 1.0000  p50 -0.0454
```

The correlation distribution is sharply bimodal — a block at exactly 1.0000 and a bulk near 0 (p50 between
−0.05 and +0.19). Typewells are either *the same curve* or unrelated; there is no useful middle ground for
a similarity ranking to exploit.

## 2. Correction to M3

`new_direction_search` M3 hashed whole typewell files and reported **0 of 3 test wells matching any train
typewell**, concluding that exact grouping was unusable. That measurement was correct but its framing
understated the sharing: **the files are truncated to different TVT ranges**, so byte hashes differ while
the curves are identical on the range they share. On the overlap, matches are exact (corr 1.0000) and
numerous — 13, 40 and 13 near-identical train typewells for the three test wells respectively.

Typewell sharing is therefore *common*, not rare. What M3 measured was file-level identity, not curve
identity.

## 3. The deciding test — does the fingerprint find anything the deployed key misses?

The deployed structural field groups wells by `round(max(typewell.TVT), 1)`. That key is
**truncation-sensitive by construction**, so the obvious worry is that two wells sharing an underlying
typewell but truncated differently get different keys and are missed. Measured directly:

```
well        near-identical      deployed        both      fingerprint-only     group-only
            (corr > 0.9999)   same-group                (missed by the key)  (not identical)
000d7d20              13            13          13                     0              0
00bbac68              40            40          40                     0              0
00e12e8b              13            13          13                     0              0
```

**The two sets are identical, in both directions, for all three test wells.** The group key misses nothing
the correlation fingerprint finds, and finds nothing the fingerprint would reject.

Consistently, all top-5 fingerprint matches are already in the deployed **surviving**-neighbour set
(5/5 for every test well), and the deployed gate already passes on all three:

```
000d7d20: same-group 13, surviving the 150 ft guard 13, closest mate 292 ft -> gate PASS
00bbac68: same-group 40, surviving 40, closest mate 295 ft                  -> gate PASS
00e12e8b: same-group 13, surviving 13, closest mate 354 ft                  -> gate PASS
```

## 4. Verdict

- **The fingerprint adds nothing over the spatial gate in production.** Per the task's own step 3, the
  direction is **closed**. No router was built, as instructed.
- **Positive byproduct:** the deployed `round(max(typewell.TVT), 1)` group key is validated as a lossless
  proxy for typewell-curve identity on the scored wells. The truncation-sensitivity worry is measured and
  dismissed. This matters for the queued `n8_azimuth_matched_neighbours`: the neighbour *set* is correctly
  identified, so grouping is not the weak link in that component — any gain there must come from the
  weighting, not the membership.
- **M3's framing corrected**: typewell sharing is common (13/40/13 near-identical curves per test well);
  the byte-hash measurement was testing file identity, not curve identity.
- Completed well inside the 30-minute time box. No submission.
