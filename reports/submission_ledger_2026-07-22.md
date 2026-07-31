# ROGII submission ledger — 2026-07-22

Daily quota: **0 of 5 used** (2026-07-22 UTC). Honest slot unchanged: `54844628`, public **7.891**.

## No submissions today

Under the corrected 3-well validation gate (`scripts/eval_three_well_gate.py`, infrastructure A), **no
candidate qualifies**. The full re-audit (`reports/corrected_gate_candidate_reaudit_2026-07-22.md`) shows
every candidate — `54878409`, `s_a20_w25`, `s_k96_aniso`, `topk96_l75`, and all blends — fails the
3-well 5th>0 bar, because per-well gain has median ≈ 0 and std ≈ 1.3, so a 3-well draw is a coin flip.

Per the submission policy (`reports/submission_policy_after_54878409_2026-07-22.md`), no "try it"
submission is made. The quota is preserved for a candidate that is either large in local space (≳0.5 OOF,
where local predicts the leaderboard) or structurally distinct with a transfer argument.

## Standing status

| candidate | public | role |
|---|---|---|
| `54844628` | **7.891** | honest slot |
| `54878409` | 7.953 | excluded (measured regression; passed only a mis-scaled 760-well gate) |

Prior-day context: `reports/submission_ledger_2026-07-21.md` (1/5 used on `54878409`).
