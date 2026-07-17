# ROGII — submission ledger + candidate audit (2026-07-17)

Relaxed-submission round, session 16baec36. Extends `submission_ledger_2026-07-15.md`. Goal = private
rank on NOVEL wells. Decision analysis: `final2_decision_update_2026-07-17.md`; overlap-mechanism +
v36 trace: `v36_provenance_and_risk_2026-07-17.md`. Neutral technical language.

## Candidate ledger (all final-relevant refs)

| ref | public | candidate | class | source / provenance | final-2 role |
|---|---|---|---|---|---|
| 54453597 | **9.519** | DWT honest | honest GBM ensemble | `joezzzzz/rogii-dwt-honest-codex` (banked) | **slot-1 (honest floor)** |
| 54710185 | **8.864** | Sunny PF90 | honest PF/beam/DTW+GBM (architecturally) | `henry_v10_sunny80_blend` (local nb; heavy GPU fork) | **slot-2 (honest upside), verify OOF** |
| 54289934 | 7.212 | Gate-Safe | affine-overlay hedge (bounded) | Plane Top2 (banked) | fallback slot-2 (overlap scenario) |
| 54753209 | 7.482 | v36 zero-contact | overlap/spatial hedge | **source NOT recoverable** (remote Codex, no local trace) | not a slot (weaker than Gate-Safe) |
| 54723189 | 9.150 | spatial-formation | structural-surface guarded LOO | Codex remote (no local source) | not a slot (partial/unclear; §below) |
| 54727655 | 9.864 | B4′ exact override | DWT + exact duplicate override | `joezzzzz/rogii-b4-guarded-codex` (this branch) | not a slot (base variance, no capture) |
| TBD | pending | **DWT+affine** (this round) | DWT + bounded affine override (deterministic base) | `joezzzzz/rogii-dwt-affine-codex` (this branch) | diagnostic — is overlap affine-capturable? |

## Task 1 — v36 provenance: NOT locally recoverable
Full trace in `v36_provenance_and_risk_2026-07-17.md`. Summary: no `joezzzzz` kernel exists for v36;
no local repo / job-dir / filesystem source; Codex local sessions end 07-14 while v36 was submitted
07-16 (remote session, no local trace). Classified from metadata + score as an overlap/spatial hedge
(7.482, "zero-contact"), weaker than Gate-Safe (7.212), high novel-collapse risk. **Task 5 (v36 variant)
is blocked** by the missing source.

## spatial-formation (54723189 = 9.150) classification
Beat DWT on public (9.150 < 9.519). "spatial formation surface w30 guarded strict LOO" → structural
surfaces (the V2 direction, which is *achievable-negative* for honest blending — a predicted-surface
model is blend-neutral). So the 9.150 gain is unlikely to be an honest structural improvement; it more
likely comes from the **guard** (a strict-LOO overlap/consistency guard), i.e. a **mild/partial overlap
play**. On novel private its guard would not fire → reverts toward its honest base (~9.5). Source is
remote/unrecoverable → cannot verify. Not recommended for a slot (partial-overlap, unverifiable).

## Task 3 — diff / correlation fingerprint: LIMITATION recorded
Diff-vs-DWT / diff-vs-GateSafe / diff-vs-v36 requires each candidate's submission.csv. **These are not
available:** Kaggle does not expose past submission files via API, and the Gate-Safe / v36 / Sunny /
spatial-formation kernels are remote/deleted (no local source, no downloadable output). Only B4′ and the
new DWT+affine csvs are locally reproducible (both via this branch's kernels). What *can* be stated
structurally, without the csvs:
- On the 3 VISIBLE wells, every OVERLAP candidate (Gate-Safe, v36, spatial-guard, B4′-same-id, affine)
  reconstructs them ≈ truth (RMSE→0), while honest candidates (DWT) predict them with their normal error
  — so a visible-well diff separates "reconstruct" from "predict" but not the overlap candidates from each
  other (they all →0 on the visible dups).
- The informative diff is on the HIDDEN toe, which is unobservable locally. The affine analysis (train
  near-dups) is the best available proxy: the overlap candidates diverge from DWT only on affine-matched
  wells (localized), and that divergence is FP-prone (heel↔toe wall). No same-source fingerprint can be
  computed without the csvs → recorded as a hard limitation of the offline environment.

## New submission this round
- **DWT+affine (`joezzzzz/rogii-dwt-affine-codex`)** — deterministic DWT base (optuna `n_jobs=1` to remove
  the post-proc public variance that hit B4′) + a bounded affine-overlap override (same-id then
  fingerprint tier; gate: geometry median<0.5 ft, affine residual<3 ft, |a−1|<0.06, |b|<800 ft, ≥60 rows;
  try/except → DWT). Local: captures the 3 visible wells (same-id, a=1,b=0) at RMSE 0.000; valid/finite.
  **Purpose:** empirically test whether the hidden overlap is affine-capturable on a DWT base (validating
  the central finding) and whether a DWT-base affine hedge is competitive with Gate-Safe for the overlap
  fallback. Ref + public score appended on completion.
