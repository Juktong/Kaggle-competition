# ROGII submission ledger — 2026-07-23

Quota is per TEAM ("lee Marc223" = `joezzzzz` + `leemarc223`), 5/day.
**Today used: 2 of 5** (both teammate-side, PENDING at last poll) → **3 remaining**.
The 2026-07-22 ledger's "0/5 used" was written before the teammate's `54896975` (07:24 UTC that day)
appeared; team-wide it was 1/5 that day. Corrected here.

## Board (2026-07-23 10:25 UTC)

| ref | date (UTC) | status | public | side | description |
|---|---|---|---|---|---|
| `54923144` | 07-23 08:21 | **PENDING** | — | teammate | Codex GR sigma 1.0 PF frontier independent hidden-runtime branch 20260723 |
| `54922806` | 07-23 08:03 | **PENDING** | — | teammate | Codex public PF frontier independent hidden-runtime rerun 20260723 |
| `54896975` | 07-22 07:24 | COMPLETE | **6.669** | teammate | Codex verified Kaiwalya PF bimodal midpoint reproduction SHA b192d3 |
| `54878409` | 07-21 13:25 | COMPLETE | 7.953 | ours | anisotropic field (excluded from final slot) |
| `54853492` | 07-20 12:32 | COMPLETE | 7.360 | teammate | Codex V66 safe MHA140 hidden-mode architecture |
| `54844628` | 07-20 04:08 | COMPLETE | 7.891 | ours | honest slot (DWT+PF+struct) |

**Team best-public: `54896975` = 6.669.** Our-side best: `54844628` = 7.891.

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
