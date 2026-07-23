# ROGII submission ledger — 2026-07-23

Quota is per TEAM ("lee Marc223" = `joezzzzz` + `leemarc223`), 5/day.
**Today used: 2 of 5** (both teammate-side, PENDING at last poll) → **3 remaining**.
The 2026-07-22 ledger's "0/5 used" was written before the teammate's `54896975` (07:24 UTC that day)
appeared; team-wide it was 1/5 that day. Corrected here.

## Board (2026-07-23 10:25 UTC)

| ref | date (UTC) | status | public | side | description |
|---|---|---|---|---|---|
| `54923144` | 07-23 08:21 | COMPLETE | 6.678 | teammate | Codex GR sigma 1.0 PF frontier independent hidden-runtime branch 20260723 |
| `54922806` | 07-23 08:03 | COMPLETE | **6.563** | teammate | Codex public PF frontier independent hidden-runtime rerun 20260723 |
| `54896975` | 07-22 07:24 | COMPLETE | **6.669** | teammate | Codex verified Kaiwalya PF bimodal midpoint reproduction SHA b192d3 |
| `54878409` | 07-21 13:25 | COMPLETE | 7.953 | ours | anisotropic field (excluded from final slot) |
| `54853492` | 07-20 12:32 | COMPLETE | 7.360 | teammate | Codex V66 safe MHA140 hidden-mode architecture |
| `54844628` | 07-20 04:08 | COMPLETE | 7.891 | ours | honest slot (DWT+PF+struct) |

**Team best-public: `54922806` = 6.563** (supersedes `54896975` 6.669; `54923144` = 6.678). Our-side best: `54844628` = 7.891.

## Watcher

`pending_watch_0723.sh` polls the two PENDING refs every 6 min (max 60 min), matches only those refs,
exits on terminal status or timeout. Results will be appended here.

## Our-side submissions today: 0. No new our-side submission is planned unless a candidate passes the
corrected gate and the source-audit conditions (see policy). Remaining team quota is primarily the
teammate line's to use today given their two in flight.

## Watcher update (11:21 UTC)

First watcher (6-min interval) reached its 60-min cap with **both refs still PENDING** (pending >3 h
since 08:03/08:21 — consistent with heavy GPU frontier notebooks in the rerun queue). A long-horizon
watcher is now running: 15-min interval, 6-h cap, ref-matched only, self-terminating. Ledger and
final-slot package update automatically when either ref goes terminal (rule: a score below 6.669
promotes that ref to slot-1 candidate).

## Watcher final (15:57 UTC)

Long-horizon watcher reached terminal state on both refs after ~7.7 h in the rerun queue:
`54922806` COMPLETE **6.563** (new team best-public, −0.106 vs 54896975); `54923144` COMPLETE 6.678
(−0.009 vs 54896975, does not supersede). Team quota today: 2/5 used, both complete; 3 remaining.
Per the pre-registered rule, `54922806` is promoted to slot-1 candidate in
`reports/final_slot_package_corrected_gate_2026-07-23.md`.
