# Final-slot package — 2026-07-26

Deadline **2026-08-05 23:59 UTC** (~10.9 days). Supersedes the 2026-07-25 package; the recommendation is
unchanged but now rests on stronger validation.

## Recommendation

- **Slot 1 — `54922806` (6.563)**: best measured public. Unchanged.
- **Slot 2 — `54968060` (6.643) preferred on evidence; `54844628` (7.891) is the provenance-first
  fallback.**

## What round 1 added to the slot-2 case

`54968060` was **validated as a genuine no-retrieval run** (G1.2 §2): the selected prefix-calibration
profile applied `alpha = 0.0` / `applied_wells = 0`, on top of `guarded_overlap_override: False`. Its
6.643 therefore measures the frontier **without any train-copy lookup** — exactly the quantity that
matters if the private set contains novel wells.

Round 1 also quantified why the retrieval mechanism matters less than its mechanics suggest: the
`contact_md_lookup` candidates reach ~0.008 ft RMSE against the train copy on held-out prefix rows, yet
enabling that path is worth only ~0.080 public. **Near-exact retrieval of train-copy TVT does not convert
into leaderboard score**, which both confirms the 07-22 truth-space finding and bounds the H-visible
advantage of the overlap-ON branches.

| | `54968060` | `54844628` |
|---|---|---|
| public | **6.643** | 7.891 |
| retrieval used | **none** (validated this round) | none (by construction) |
| local proxy (train-copy TVT) | **3.259** | 3.677 |
| validation depth | public + per-stage component validation (G1.2) | 760-well nested OOF + bootstrap |
| provenance | derives from the public Kaiwalya notebook + 9 third-party public datasets | fully owned, built and audited in this repo |

**Recommendation stands:** unless the final-selection owner weights fully-owned provenance and
OOF-backed validation above measured score, `54968060` is the better slot-2 pick. `54844628` remains the
fully-owned fallback.

## Open item that could still change slot 2

G2.1 **SP45-projection-only** (round 2): the frontier's SP45 stage alone has the best local proxy
(2.581 vs 3.259) and is non-homogeneous with everything scored. If it submits and scores below 6.643 it
becomes the stronger slot-2 candidate. The proxy saturation caveat (above) means this is a test, not an
expectation.
