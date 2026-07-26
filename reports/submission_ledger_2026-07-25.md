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
submitted 2026-07-25 05:38 UTC, **COMPLETE — public 6.643**. Commit at submission: `9857c3a`.
**2026-07-25 usage: 1/5 used, 4 remaining.** (2026-07-26 is a fresh day: 0/5 as of 02:13 UTC.)

## Board after 54968060

| ref | public | side | note |
|---|---|---|---|
| `54922806` | **6.563** | teammate | best-public (frontier, overlap-ON) |
| **`54968060`** | **6.643** | **ours** | **overlap-OFF frontier** — 2nd best on the board |
| `54896975` | 6.669 | teammate | frontier overlap-ON (Kaiwalya repro) |
| `54923144` | 6.678 | teammate | frontier GR-sigma branch |
| `54844628` | 7.891 | ours | fully-owned honest slot |
| `54878409` | 7.953 | ours | excluded |

## What 6.643 means — a correction to the earlier overlap hypothesis

Removing the visible-well overlap lookup costs **very little on public**:

```
vs its own family reference (the 6.626 package, overlap-ON) : 6.643 - 6.626 = +0.017
vs current best-public 54922806 (overlap-ON, other branch)  : 6.643 - 6.563 = +0.080
A1-established config-variance noise floor                   : ~0.115
```

Both gaps are **at or below the noise floor**, so the overlap override's measurable public contribution
is small. The earlier hypothesis — that the 6.5→7.9 gap was essentially the overlap lookup — is **not
supported**. The correct decomposition is the opposite:

```
7.891 (our honest)  ->  6.643 (frontier WITHOUT overlap)   = 1.248  <- the frontier's MODELING
6.643 (no overlap)  ->  6.563 (best overlap-ON branch)     = 0.080  <- overlap + config, within noise
```

The frontier's PF/beam/SP45/visible-prefix stack, **independent of the overlap lookup**, accounts for
essentially all of the advantage over our honest line. `54968060` also beats two overlap-ON family
members (6.669, 6.678), which is only possible if the modeling — not the lookup — carries the score.

Also notable: the local D3 measurement (overlap-OFF frontier RMSE 3.259 < honest 3.677) **agreed
directionally with public** (6.643 < 7.891). That is the opposite of the 54878409 case, where a local
gain did not transfer.
