# ROGII submission ledger — 2026-07-24

Team = "lee Marc223" (`joezzzzz` + `leemarc223`), quota 5/day (team-wide).
**Today (2026-07-24 UTC) used: 0 of 5** → 5 remaining. No submission made this session.

## Board (05:17 UTC)

| ref | date (UTC) | status | public | side | note |
|---|---|---|---|---|---|
| `54922806` | 07-23 08:03 | COMPLETE | **6.563** | teammate | team best-public (PF frontier rerun) |
| `54923144` | 07-23 08:21 | COMPLETE | 6.678 | teammate | frontier GR-sigma branch |
| `54896975` | 07-22 07:24 | COMPLETE | 6.669 | teammate | Kaiwalya repro (this notebook family) |
| `54878409` | 07-21 13:25 | COMPLETE | 7.953 | ours | excluded (regression) |
| `54844628` | 07-20 04:08 | COMPLETE | 7.891 | ours | honest slot |

## Mark's 6.626 package — integrated, audited, smoked; NOT submitted

`kaggle_kernel_kaiwalya_public_tvt_6626_repro/` (origin/main@a589fa8) integrated by targeted extract.
Its notebook is **byte-identical** (sha256 d61a88…) to the public Kaiwalya source and to the family the
team already submitted 3× (6.563/6.669/6.678). Audit:
`reports/mark_kaiwalya_6626_repro_audit_2026-07-24.md`.

**Submission decision: HOLD (no submission).** A direct rerun is homogeneous with the already-submitted
`54922806` (6.563) / `54896975` (6.669); per the standing rule, quota is not spent on a homogeneous
reproduction of the public 6.626 line. A FAST smoke from our account (`joezzzzz/rogii-kaiwalya-6626-smoke`)
is run only to confirm our-side runnability (all 9 datasets verified accessible from our account), not to
submit.

## Our-side quota today: 0 used, 5 available. No our-line candidate passes the corrected gate + policy;
the frontier variants (`reports/kaiwalya_frontier_variant_queue_2026-07-24.md`) are teammate-line hedges
prepared for the final-selection owner, not our-line submissions.
