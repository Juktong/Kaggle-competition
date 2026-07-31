# Autonomous backlog status — 2026-07-23

## State refresh (10:20–10:30 UTC, from live board + processes, not stale ledgers)

- **Stale waiter cleaned**: user killed `smoke_finalize_wait.sh`; live check confirms **no**
  `pf_variant_smoke` / `hneighbor_gr_smoke` / notebook / kaggle training processes exist.
- **PF medium smoke had actually completed** (2026-07-22 04:54): the wider-emission standalone
  advantage shrank from +0.31 (24 wells) to **+0.035** (60 wells) — closed. The horizontal-neighbour GR
  smoke produced **no output** (process died with session teardown) — needs rerun, deprioritised.
  Both reports corrected.
- **Board**: `54896975` COMPLETE public **6.669** (team best); `54922806`/`54923144` PENDING
  (teammate PF-frontier reruns); our `54844628` 7.891 / `54878409` 7.953 unchanged.
- **Quota**: team-wide 5/day; today **2/5 used** (both teammate, pending); our side 0 today.

## Completed today

| task | outcome |
|---|---|
| 1 live-status cleanup | done; two 07-22 smoke reports corrected, committed |
| 2 source audit | done — `reports/pf_frontier_submission_source_audit_2026-07-23.md`: all three are **teammate (leemarc223) Codex** submissions from **private kernels**; `54896975` reproduces the **public** `kaiwalyaatulraut/rogii-public-tvt-solution` (overlap override + prefix calibration + bimodal midpoint; 9 public dataset deps; no internet) |
| 3 pending poll | watcher running (6-min interval, 60-min cap, ref-matched, self-terminating) |
| 4 candidate audit | done — `reports/pf_frontier_candidate_audit_2026-07-23.md`; direct CSV diff impossible (private kernels); mechanism decomposition + **H-visible/H-hidden** framework fork recorded |
| 6 docs | 2026-07-23 ledger, final-slot package, this backlog |

## The H-visible / H-hidden fork (key open question)

"Hidden-runtime" constructions across the public frontier + CLAUDE.md's "novel wells" framing imply the
kernels-only rerun may mount a **hidden test set** (H-hidden). This conflicts with the 07-22 inference
(row splits of the 3 visible wells, H-visible) and — if true — resolves the truth-space puzzle (public
computed on unseen wells) and **restores 760-well OOF as the right private proxy**, while overlap/prefix
tricks go inert on novel wells. Neither hypothesis is locally provable; both are recorded and the
final-slot package covers both.

## No our-side submission today

No candidate passes the corrected gate + post-54878409 policy. The teammate line has 2 in flight;
remaining team quota (3) is effectively theirs today. Our honest slot `54844628` unchanged.

## Continues automatically

- Pending watcher → on completion: update `submission_ledger_2026-07-23.md` + final-slot package
  (rule: better-than-6.669 pending becomes slot-1 candidate).
- If both pendings fail/score worse: no action; package stands.
- Queued (behind any transfer-argument direction): horizontal-neighbour GR rerun; wider-emission PF full
  run (de-prioritised after the medium-smoke shrink).
