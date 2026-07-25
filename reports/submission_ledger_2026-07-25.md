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
- **A1 seed-variance**: done (no submit) — frontier is deterministic given seed config; 0.115 public
  spread is config variance. `reports/kaiwalya_seed_variance_audit_2026-07-25.md`.
- **A2 overlap-OFF**: smoke COMPLETE (overlap proven OFF; `overlap probe 3/3` copies exist but override
  skipped). Overlap contributes ~3.2 ft rmse on visible wells. **Full run RUNNING**
  (`joezzzzz/rogii-kaiwalya-overlap-off-full`) to produce a real output for the authorized H-hidden
  diagnostic submission. D1 ensemble preview: overlap-OFF frontier corr 0.99996 with 54844628 → no
  distinct blend gain. Reports: `kaiwalya_overlap_off_ablation_2026-07-25.md`.
- **B1/B2**: origin/main unchanged since a589fa8; no new teammate/public line to integrate; new-direction
  queue written (`new_direction_queue_2026-07-25.md`).

## Submission made this session

**`54968060`** — overlap-OFF frontier diagnostic (kernel `joezzzzz/rogii-kaiwalya-overlap-off-full` v1),
submitted 05:38 UTC, **PENDING** (frontier-family scoring takes hours; 6h watcher running). Purpose:
measure the frontier's public WITHOUT the visible-well overlap lookup. **Today: 1/5 used, 4 remaining.**

D3 finding elevates it: on the 3 wells' train-copy TVT the overlap-OFF frontier RMSE **3.259 beats**
`54844628`'s 3.677, so it may be a **candidate slot-2 H-hidden hedge**, not just a diagnostic — pending
its public score (`reports/frontier_vs_honest_error_decorrelation_2026-07-25.md`).

Board best-public unchanged: `54922806` 6.563; our honest hedge `54844628` 7.891.
