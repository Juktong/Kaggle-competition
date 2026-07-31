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

## New submissions this round (COMPLETE)
| ref | candidate | public | conclusion |
|---|---|---|---|
| **54775625** | DWT deterministic base (optuna `n_jobs=1`, LAM=1.0) | **9.487** | ≈ banked DWT 9.519 (marginally better). **Base variance RESOLVED:** `n_jobs=1` reliably reproduces ~9.5; B4′'s 9.864 was the unlucky `n_jobs=-1` τ=55 draw. |
| **54775626** | DWT base + bounded affine-overlap override | **9.823** | **+0.336 WORSE than the 9.487 base** → the affine override HURT on the hidden public split (FPs dominate). |

**Empirical conclusion (task 4):** `affine − detbase = +0.336` — the DWT+affine override **did not capture
the overlap**; it added net FP harm. This **empirically confirms** the train analysis (affine matching is
FP-unsafe / net-negative, heel↔toe wall) and shows a naive DWT-base affine hedge is **not viable** — it
fires on coincidental affine FPs (heel-match, toe-diverge) rather than the true overlap that Gate-Safe's
refined mechanism captures (7.212). So **Gate-Safe remains the proven overlap-slot hedge**; a DWT+affine
does not compete for it. Two useful positives: (a) a **deterministic-base DWT** (`n_jobs=1`) reliably
reproduces ~9.49 (a clean, reproducible honest base, unlike B4′'s variance); (b) the affine result closes
the last "can we put overlap on a DWT base?" question — no, not safely. The primary final-2 recommendation
{DWT, Sunny} is unchanged; the overlap fallback is {DWT, Gate-Safe} (not DWT+affine).
Kernels: `joezzzzz/rogii-dwt-detbase-codex` v1, `joezzzzz/rogii-dwt-affine-codex` v2 (this branch).

## Round 2 (2026-07-17b) — qwer, deterministic-DWT audit, Sunny OOF

### qwer (54777533 = 7.921) — DOWNGRADED, not a slot
Full trace in `qwer_provenance_and_honesty_2026-07-17.md`. Source **not locally recoverable** (remote
Codex, `SHA424e` unresolved). Its "OOF target 6.909" is **below the overlap plateau (7.2)** → a
**leakage-inflated OOF, not an honest CV**; public 7.921 is the **weakest** overlap play on the board
(worse than Gate-Safe 7.212, v36 7.482). → **unverifiable, dominated by Gate-Safe, excluded from the
final-2 pool.**

### Task 3 — deterministic DWT audit (54775625 = 9.487)
- **Source (reproducible):** `joezzzzz/rogii-dwt-detbase-codex` v1 = `kaggle_kernel_dwt_detbase/` in this
  branch = the DWT honest notebook with `LAM=1.0` (5-model) and **`optuna n_jobs=1`** (deterministic
  post-proc). Commit on `codex/autonomous-queue-2026-07-15`.
- **Relation to old DWT 54453597 (9.519):** same model/features (ravaghi lgb1-3+cb1-2, honest); the only
  difference is the optuna post-proc draw — 54453597 used `n_jobs=-1` (non-deterministic, gave 9.519);
  det-base uses `n_jobs=1` (deterministic, gave **9.487**, marginally better). Both are honest DWT; on a
  **novel private** set they behave essentially identically (post-proc affects public, not private-honest
  quality). The 0.032 public gap is post-proc noise.
- **Should it replace 54453597 as the honest slot?** **Yes, preferred** — det-base is (a) **reproducible**
  (deterministic `n_jobs=1`, regenerable exactly for audit/regeneration; 54453597's `n_jobs=-1` is not),
  and (b) marginally better on public (9.487 vs 9.519). old DWT 54453597 remains an equivalent, established
  fallback (identical private-honest behaviour). **Recommendation: honest floor = 54775625 (det-base),
  with 54453597 as the equivalent fallback.**

### Task 2 — Sunny OOF verification (in progress)
Leakage audit of `henry_v10_sunny80_blend` (v34 Sunny meta): **PASSED** — no overlap-copy, no gold-prefix;
proper GroupKFold OOF (LightGBM+CatBoost+XGB ensemble + NCC/beam geosteering forward + Climber blend);
`TVT_input.values` used only for drift-rate features; `y_test_temp` is an honest train-holdout. Sunny's
8.864 is in the honest manifold (above the plateau), so it is a **genuinely honest** candidate, plausibly
stronger than DWT (honest public models reach ~8.1 per lessons §1). A partial OOF fork
(`joezzzzz/rogii-sunny-oof-codex`, FLAG_MODEL mode, TEST_SIZE=120) is running to obtain its CV. Full
verdict in `sunny_pf90_honesty_2026-07-17.md`.
