

---

## CORRECTION to M3 (same day, from N5) — the byte-hash understated typewell sharing

M3 hashed whole typewell files, found 752 distinct files over 773 wells and **0 of 3 test wells matching
any train typewell**, and concluded that typewell grouping was capped. The hashes are correct but they
measure **file identity, not curve identity**: typewell files are truncated to different TVT ranges, so
two wells sharing an underlying typewell hash differently.

`reports/n5_typewell_fingerprint_families_2026-07-28.md` re-measured on the *overlapping* TVT range:

```
near-identical train typewells (corr > 0.9999) per test well:
  000d7d20 -> 13    00bbac68 -> 40    00e12e8b -> 13
```

Typewell sharing is therefore **common, not rare**. This does not revive the direction — N5 also showed
the deployed `round(max(typewell.TVT), 1)` group key already recovers exactly those sets (13/13, 40/40,
13/13, zero difference in either direction), so the fingerprint adds nothing over production. N5's own
conclusion (direction closed) stands; only M3's stated reason is corrected.
