# ROGII submission ledger — 2026-07-26

Team = "lee Marc223" (`joezzzzz` + `leemarc223`), quota 5/day team-wide.
**Today (2026-07-26 UTC) used: 1 of 5 → 4 remaining.** Live-checked 15:09 UTC.
Deadline **2026-08-05 23:59 UTC** (~10.9 days).

## Board

| ref | date | public | side | role |
|---|---|---|---|---|
| `54922806` | 07-23 | **6.563** | teammate | best-public (frontier overlap-ON) — slot 1 |
| `54990075` | 07-26 | 6.690 | **ours** | frontier SP45-only — settled the post-SP45 question |
| `54968060` | 07-25 | **6.643** | **ours** | frontier overlap-OFF (validated no-retrieval) |
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

## Round 2 result (2026-07-26)

**`54990075` = 6.690 COMPLETE** (G2.1 SP45-projection-only, kernel
`joezzzzz/rogii-frontier-sp45-only-full` v1, commit `9f0d6a4`). Today 1/5 used, 4 remaining.

Pre-registered reading resolved to the `> 6.678` branch: **the frontier's post-SP45 stages earn their
place** on the leaderboard, and the local train-copy proxy that favoured SP45-only pointed the wrong way
— an independent confirmation of the G1.2 §3 saturation finding. The submission did its job: it answered
a question that no local evidence could settle.

Slot recommendation after this result (all three criteria converge):
**slot 1 `54922806` (6.563) + slot 2 `54844628` (7.891)** — see
`reports/final_slot_package_corrected_gate_2026-07-26.md`.

## 2026-07-28 (autopilot rounds 4–5)

**Quota used today: 0 of 5.** No submission. Board unchanged since `54990075` (6.690, 07-26).
Deadline 2026-08-05 23:59 UTC.

- Round 4 `live_refresh_and_decision`: state refreshed, queue advanced.
- Round 5 `g35_honest_prefix_calibration`: **closed on evidence, no submission** — the prefix-cut
  calibration prerequisite does not hold once the same-run confound is removed.

