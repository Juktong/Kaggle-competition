# New-method probe queue (2026-07-22)

Direction 9. Five small probes and five larger directions, each executable, framed by the two dominant
findings of this round: (i) validation must be at 3-well scale, and (ii) local truth space does not
predict the leaderboard for ≲0.1-margin candidates. So probes are judged by whether they could produce
a *large* or *structurally distinct* signal, not a small OOF gain.

## Small probes — 3 executed this round

| # | probe | result | disposition |
|---|---|---|---|
| S1 | **pure base vs 54844628 at 3-well scale** | base is worse in OOF (−0.44) AND worse 3-well downside (5th −1.91, P>0 36%). Struct is not the risk driver. | closed — keep struct |
| S2 | **well-family risk of the 3 test wells** | baseline well-RMSE percentiles 26 / 48 / 50 — typical difficulty, not outliers. corr(RMSE, nnb) −0.15. | closed — no risk flag |
| S3 | **heel-anchor stability on the 3 test wells** | heel r std 0.5–1.3 ft, dr std 0.01 — anchor is very stable; a median anchor would not change the result. | closed — anchor not the issue |
| S4 | GR-difference level correction (prior round) | 0.0% variance explained | closed |
| S5 | anti-harm guard (direction 1) | harm predictor AUC 0.53 = chance | closed |

The three new probes (S1–S3) jointly establish that **there is no test-available red flag** on the 3
test wells: they are typical difficulty, their anchors are stable, and the structural field is not the
risk driver. The `54878409` miss is not attributable to any pre-public feature — it is the truth-space
gap (`reports/public_mismatch_feature_audit_54878409_2026-07-22.md`).

## Larger directions — five, ranked by transfer potential

| # | direction | why it could matter | cost | status |
|---|---|---|---|---|
| L-a | **Wider-emission PF as a component upgrade** | Smoke shows it is stronger standalone (+0.31 on PF) and partly decorrelated (corr 0.885). A *component* upgrade changes the base for all wells and could be large enough to transfer. | full PF re-run (773×128), hours | medium smoke running; full run is the top future item |
| L-b | Horizontal-neighbour GR **sequence** alignment | The last un-occupied L5 shape: GR as a sequence referenced against neighbouring horizontal wells. | high | smoke running (direction 5) |
| L-c | Alternative decorrelated forward (resistivity/other-log) | **Not feasible** — the only test-available log is GR (data audit). Closed. | — | closed |
| L-d | Trajectory-analog ensemble (match whole-well trajectory shape, transfer TVT profile) | A genuinely different cross-well computation; could decorrelate from geometry-IDW. | medium | queued (not yet smoked) |
| L-e | Robust Bayesian model averaging across DWT/PF/struct with per-well uncertainty | Uses pf_unc; but per-well win/loss is unpredictable (AUC 0.53), so expected value is low. | low | deprioritised on prior evidence |

## The honest conclusion for probe strategy

Under the truth-space finding, **only large or structurally-distinct signals are worth pursuing**, and
the only one with a positive standalone smoke is the wider-emission PF (L-a). Small re-weightings and
selectors are closed: they produce ≲0.2 local gains that the leaderboard cannot resolve and that do not
transfer. The next concrete action is the L-a full PF run, explicitly flagged as knowledge-building
(its ~0.15 pipeline effect is below the transfer threshold, so it is not expected to be submittable) —
which is why it was not started this round in preference to completing the validation infrastructure.
