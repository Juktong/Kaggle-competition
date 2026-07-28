

## 2026-07-28 update (N5 typewell fingerprint)

- **Closed: typewell-fingerprint well families.** The near-identical set and the deployed group-key set
  are identical in both directions on all three test wells (13/13, 40/40, 13/13). 5/5 of the fingerprint
  top-5 are already in the deployed surviving-neighbour set. Nothing is added over production.
- **M3 corrected:** its byte-hash measured FILE identity, not CURVE identity (files are truncated to
  different TVT ranges). Typewell sharing is common — 13/40/13 near-identical curves per test well — not
  rare as M3 implied.
- **Banked positive:** the deployed `round(max(typewell.TVT), 1)` group key is a lossless proxy for
  typewell identity on the scored wells; its truncation-sensitivity was a real worry and is now measured
  and dismissed. Relevant to `n8`: neighbour membership is correct, so any gain there must come from the
  weighting.
- Next runnable: **`n8_azimuth_matched_neighbours`** (170) — the only queued item with a submission path —
  then `n7` (180), `n9` (190).
