# ROGII — final-2 decision update (2026-07-19)

Session `dcdcec05`. Supersedes `final2_decision_update_2026-07-17.md` and the 2026-07-18 reassessment, now
that the DWT+PF blend is submitted + public-verified and qwer has been re-audited. Goal = private/final rank
on NOVEL wells. Best-of-2 = min of two pooled private scores. Neutral technical language.

## 1. Board (verified public scores)
| candidate | ref | public | honest OOF | class | novel-private behavior |
|---|---|---|---|---|---|
| **DWT+PF blend** | **54804893** | **8.080** | **9.2969** | honest, decorrelated (w*=0.44) | **holds ~9.3 (public-verified transfer)** |
| Gate-Safe | 54289934 | 7.212 | — | overlap-exploitation hedge | collapses (affine FP-unsafe) |
| qwer | 54777533 | 7.921 | 6.909 (**leakage**) | overlap/meta play | collapses (overlap component) |
| Sunny PF90 | 54710185 | 8.864 | ~11 (honest PF on novel) | overlap-leaked physical | ≈DWT on novel |
| det-base DWT | 54775625 | 9.487 | 10.3987 | honest GBM base | safe ~9.5 (superseded by blend) |

## 2. qwer re-audit (detail: `qwer_final2_audit_2026-07-19.md`)
- Source re-confirmed unrecoverable (3rd independent check: no git/kernel/Codex trace; no joezzzzz kernel ran
  at the 07:15 submit time; candidate kernels carry no qwer/424e signature; CLI can't download past-submission
  CSVs). qwer's predictions are not obtainable.
- **qwer OOF 6.909 is definitively leakage-inflated:** it is 2.39 (26%) BELOW the verified honest frontier
  (DWT+PF 9.30) — no honest model reaches it; and the OOF→public direction (6.909→7.921, public WORSE) is the
  overlap-overfit signature (contrast DWT+PF 9.30→8.080, public better). **qwer is not honest.**
- **qwer's better public than DWT+PF (7.921<8.080) is overlap-driven, not novel-quality.** For the overlap
  slot it is dominated by Gate-Safe (7.212); for the honest slot it is not honest. **Excluded.**

## 3. Secondary search — new low-correlation honest candidates (all negative this round)
- **qwer + DWT+PF blend/selector:** not validatable — qwer's OOF/predictions are unobtainable, and qwer is
  leakage (would inject overlap into an honest blend). Not pursued.
- **Hard-well router (test-available):** the OOF complementarity (PF beats DWT on truth-defined hard wells) is
  **NOT detectable from test-available features.** Per-well PF-advantage vs features: heel_drift corr +0.074,
  z_span −0.01, n_eval +0.063, gr_std −0.01 (all noise). Nested drift-tercile router = **9.272 vs fixed-0.5
  blend 9.297 → gain +0.025 ft (negligible)**; per-group optimal weight ≈0.42–0.47 (constant → no routing
  signal). **The fixed 0.5 DWT+PF blend is the deployable optimum** (the complementarity is oracle-only).
  (`scripts` → `$JOB/tmp/router_feasibility.py`; per-well features `router_feat.csv`.)
- **Public high-score notebooks honest-replay:** the 2026-07-18 reassessment already found no honest-different
  pipeline beyond Sunny (now captured by DWT+PF); the Lucifer PF-stack extras (beam/ANCC-PF/Z-PF) were tested
  and add nothing (`lucifer_pf_stack_oof_plan_2026-07-18.md`). No new honest pipeline identified.
- **MTP / top-K trajectory selector:** deferred — it also needs a test-available selection signal, which the
  router analysis shows is weak; not worth a heavy run without evidence a selection signal exists. No smoke
  launched.

## 4. Decision — final-2 = {DWT+PF blend, Gate-Safe} (Option A), unchanged
| option | pair | novel-heavy private (goal) | overlap-heavy private | verdict |
|---|---|---|---|---|
| **A (recommended)** | **{DWT+PF 54804893, Gate-Safe 54289934}** | **~9.3** (blend holds; Gate-Safe floored) | **~7.2** (Gate-Safe wins) | best of both |
| B | {qwer, Gate-Safe} | weak (both overlap collapse, no honest floor) | ~7.2 | dominated on novel |
| C | {qwer, DWT+PF} | ~9.3 (qwer adds nothing) | ~7.9 > Gate-Safe 7.2 | dominated on overlap |

- **Option A weakly dominates every alternative** in both private scenarios. qwer does not improve the pair.
- **No new submission this round:** the router gain is negligible (+0.025, not a clear honest gain), qwer is
  leakage, and no new honest candidate cleared a gate. The submission budget is preserved.

## 5. Recommendation
**Final-2 = {DWT+PF blend 54804893 (honest slot, public 8.080 / OOF 9.30), Gate-Safe 54289934 (overlap hedge,
public 7.212)}.** The DWT+PF blend remains the verified best honest model; the fixed 0.5 weight is optimal (no
deployable router). qwer is excluded (leakage OOF, overlap-dominated). Private hidden until 2026-08-05.
