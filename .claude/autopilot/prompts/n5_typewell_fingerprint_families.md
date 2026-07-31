---
id: n5_typewell_fingerprint_families
priority: 160
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# N5 Typewell-fingerprint well families (time-boxed to 30 minutes)

Test whether near-matching the test typewell against train typewells identifies a useful analogue set.

Context (do not re-derive) — this direction is already bounded by measurement:

- The typewell file IS a test-available input (`TVT, GR`; note `Geology` is train-only and absent from
  the test schema).
- `reports/new_direction_search_2026-07-28.md` M3: 773 train wells map to 752 distinct typewell files,
  group sizes {1: 739, 2: 12, 10: 1}, and **none of the 3 test wells shares a typewell byte-identically
  with any train well**. Exact grouping is unusable and the near-match upside is capped by this
  distribution.

Required execution (stop at 30 minutes of compute either way):

1. Correlate each test typewell's GR-vs-TVT curve against all 773 train typewells on the overlapping
   TVT range.
2. Report the top-5 matches per test well with their correlation.
3. Report whether those matches are ALSO spatial neighbours under the deployed gate — i.e. whether the
   fingerprint adds anything over the spatial gate already in production. If it does not, close the
   direction.
4. Do not build a router in this task.

Write:

- `reports/n5_typewell_fingerprint_families_2026-07-28.md`
