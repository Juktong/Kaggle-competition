# ROGII submission ledger — 2026-07-26

Team = "lee Marc223" (`joezzzzz` + `leemarc223`), quota 5/day team-wide.
**Today (2026-07-26 UTC) used: 0 of 5 → 5 remaining.** Live-checked 02:30 UTC.
Deadline **2026-08-05 23:59 UTC** (~10.9 days).

## Board

| ref | date | public | side | role |
|---|---|---|---|---|
| `54922806` | 07-23 | **6.563** | teammate | best-public (frontier overlap-ON) — slot 1 |
| `54968060` | 07-25 | **6.643** | **ours** | frontier overlap-OFF — live slot-2 candidate |
| `54896975` | 07-22 | 6.669 | teammate | frontier overlap-ON |
| `54923144` | 07-23 | 6.678 | teammate | frontier GR-sigma branch |
| `54844628` | 07-20 | 7.891 | ours | fully-owned honest — slot-2 provenance-first fallback |
| `54878409` | 07-21 | 7.953 | ours | excluded (regression) |

## Round 1 (2026-07-26)

**No submission.** Rotation infrastructure built and G1.2 completed with zero quota and zero GPU
(the frontier's own masked-split reports were reused). Round-2 candidate identified:
SP45-projection-only (non-homogeneous, best proxy RMSE) — needs smoke → full before the gate applies.

`54968060` was validated this round as a **genuine no-retrieval run** (`alpha=0.0`, `applied_wells=0`
in the selected prefix profile, plus `guarded_overlap_override: False`), so its 6.643 is a clean
measurement of the frontier without any train-copy lookup.
