# Final-slot package under the corrected gate (2026-07-22)

Direction 8. A final recommendation for our own honest line. Not a submission. Teammate/overlap
submissions are noted for completeness only and are not centred in any decision (per standing directive).

## Recommendation

**Honest slot = `54844628` (public 7.891, OOF 8.8626).**

Rationale, in priority order:
1. It is the best **real leaderboard** result on the actual 3 test wells from our honest line.
2. `54878409` (public 7.953) is a **measured regression** and is excluded from the honest slot. Its
   +0.18 local OOF gain did not transfer — the truth-space gap (local RMSE 3.68 vs public 7.891, rank
   not preserved at ~0.1 margin) means local gains at this scale are not evidence.
3. No other own candidate meets the corrected 3-well gate (all fail; see
   `reports/corrected_gate_candidate_reaudit_2026-07-22.md`). There is nothing to promote over `54844628`.

## How public↔private affects the choice

The whole test set is 3 wells; public and private are **row splits of the same 3 wells**. So:
- Public is a **direct** signal on the wells that decide private (not a different well sample).
- But the split geometry is unknown: under a random row split public≈private (corr 0.999), under a
  contiguous block split they are near-independent (corr 0.10). We cannot assume which.
- Given this, the candidate with the **best measured public** on these exact wells is the most defensible
  private bet from our honest line — that is `54844628`.

## Own-line candidate ledger (corrected-gate view)

| candidate | public | local OOF | corrected 3-well gate | final-slot role |
|---|---|---|---|---|
| **`54844628`** | **7.891** | 8.8626 | baseline | **honest slot** |
| `54878409` | 7.953 | 8.6825 (+0.18) | FAIL (5th −1.26) | excluded (regression) |
| `54804893` (DWT+PF blend) | 8.080 | 9.2969 | — | superseded by 54844628 |
| topk96_l75 (unsubmitted) | — | 8.5070 (+0.36) | FAIL (5th −1.95) | not submitted |

## Overlap/hedge line — noted only, not centred

`54174151` (public 7.182) and `54289934` (public 7.212) score better on public than our honest line.
They belong to the overlap/aggressive line documented in prior audits
(`reports/final_overlap_slot_audit_2026-07-19.md`, `reports/historical_submission_board_audit_2026-07-19.md`),
not the honest line, and — per standing directive — no decision here is built around them. Their public
advantage is consistent with an overlap mechanism that benefits from the test wells being visible in
train; whether that transfers to a genuinely novel private split is the open risk recorded in those
audits, and is a call for the final-selection owner, not this honest-line work.

## Net

For our honest line: **submit nothing new; keep `54844628` as the honest slot; exclude `54878409`.**
The one direction with a positive standalone signal this round (wider-emission PF, +0.31 on the PF
component) is small-margin at the pipeline level and, by direction C, would not be expected to transfer;
it is recorded for a future full run, not a submission.
