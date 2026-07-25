# ROGII submission ledger — 2026-07-25

Team = "lee Marc223" (`joezzzzz` + `leemarc223`), quota 5/day (team-wide).
**Today (2026-07-25 UTC) used: 0 of 5** → 5 remaining. Live-checked at 05:05 UTC.

## Board (05:05 UTC, unchanged from 07-24)

| ref | status | public | side | note |
|---|---|---|---|---|
| `54922806` | COMPLETE | **6.563** | teammate | team best-public (PF frontier) |
| `54896975` | COMPLETE | 6.669 | teammate | Kaiwalya repro (same notebook family) |
| `54923144` | COMPLETE | 6.678 | teammate | frontier GR-sigma branch |
| `54878409` | COMPLETE | 7.953 | ours | excluded (regression) |
| `54844628` | COMPLETE | 7.891 | ours | honest slot (fully-owned, no overlap) |

## Session activity (A queue — Kaiwalya frontier variants)

- **A3/A4/A5 ablations**: done from the baseline FAST smoke's staged intermediates (no new GPU). All
  HOLD (homogeneous). `reports/kaiwalya_modelpkg_prefix_bimodal_ablations_2026-07-25.md`.
- **A2 overlap-OFF**: `joezzzzz/rogii-kaiwalya-overlap-off-smoke` pushed (FAST, overlap forced OFF);
  watcher polling. If smoke proves `rows_overridden=0` → full run → diff → submit-if-worthy.
- **A1 seed-variance**: queued (no submit).

No submission made this session. Quota preserved (0/5).
