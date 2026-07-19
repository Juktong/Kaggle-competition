# ROGII — honest-slot improvement sprint backlog (2026-07-19)

Session `1246d008` (chain `…→8de8cbed→1246d008`). Target: a candidate that beats or positively ensembles with
the honest slot **54804893 (DWT+PF blend, public 8.080, honest OOF 9.2969)**. Final selection is background
context only. Neutral technical language. Status legend: TODO / RUNNING / DONE-POS / DONE-NEG.

## Standing gate for any submission
honest OOF clearly < 9.2969 · bootstrap stably positive · stress scenarios not materially worse ·
leakage audit pass · format audit pass (rows/id-order/finite/range) · diff-vs-54804893 explainable.

## Sprint-critical prior (why this sprint is framed as it is)
Earlier router work (sessions 1a07ce3e) showed **no test-available feature predicts WHICH of DWT/PF is better**
(all corr with (|errDWT|−|errPF|) < 0.05) and a nested router was WORSE than the fixed blend. **But every
feature tested was SYMMETRIC** (|PF−DWT| disagreement, GR roughness, curvature, heel-drift — these flag
*hardness*, not direction). The untested class is **ASYMMETRIC, model-specific confidence**:
**PF seed-spread / likelihood dispersion** and **GBM per-model disagreement**. That is this sprint's key test (B).

## Directions
| # | direction | hypothesis | status | result / next |
|---|---|---|---|---|
| A | DWT+PF error decomposition | error structure by segment/geometry/quality gives the selector its inputs | **DONE-NEG (routing)** | full 773-well table built (`decomp_features.npz`, 3.78M rows). Winner: PF 46.2% / DWT 37.7% / blend 16.2%; both-fail 8.6%; blend beats both in ALL toe-distance quartiles. **Directional screen: max |corr| = 0.061; `gbm_disagree` only +0.030 → GBM-disagreement hypothesis NOT supported.** Report written. |
| B | selector / router with ASYMMETRIC confidence | PF-uncertainty (seed spread) + GBM disagreement predict *which* model to trust | **DONE-NEG (GBM) / PARTIAL-NEG (PF-unc), full re-test RUNNING** | `gbm_disagree` refuted at full power (A). `pf_unc` on 96-well partial: corr(eD−eP)=+0.169, a* spread 0.587, BUT **nested router 10.316 LOSES to fixed-0.5 10.263**; under-powered (even a global refit loses there). Full 773-well PF-unc run in progress (detached pid 24489) for the full-power re-test. |
| C | top-K path search + ranker | multiple TVT paths + a learned ranker beats the single averaged path | **DONE — quantified partial-neg** | oracle gap is REAL: blend 5.628 → **oracle-seed 4.935 (−0.69)**; but likelihood ranks paths only at r=0.343 and the deployable max-likelihood pick (7.148) is **worse than averaging (6.729)**. Ranker must clear +0.42 just to reach parity. Report written; build deferred (needs PF re-run retaining all K paths). |
| D | CNN/Siamese GR local scorer + DP | learned local GR-window similarity replaces hand-written NCC/DTW cost | **DEFERRED (not started)** | 2-core box was saturated by the PF-unc + struct-field runs; and the sprint's evidence lowers its prior (A: no row-level routing signal; C: learned ranking must clear +0.42 just to match averaging). Next-round item; needs Kaggle GPU + tiny→medium→full smoke. |
| E | MTP multi-hypothesis residual paths | min-of-K loss yields diverse paths; selector picks | **DEFERRED (not started)** | same reason as D, plus it depends on a selector that C showed is the hard part. Lower priority than finishing F's submission path. |
| F | external / industry honest pipeline OOF | a genuinely different correlation method decorrelates from GBM+PF | **DONE-POS — clears the OOF gate** | **Discovery: 773 typewells = ~54 master logs → group = structural unit.** Group-anchored cross-well `r=TVT+Z` field: corr +0.073 vs DWT, −0.048 vs PF (near-orthogonal), **nested gain +0.4938 at min_sep=150** on 165 wells. Honesty gate PASSED: closest mates differ by median 64 ft TVT at matched XY, GR corr 0.10, **0/52 are duplicates**. **FULL 760-well OOF: nested 9.2987 → 9.1626, gain +0.1361, w≈0.07 positive & stable in all 5 folds.** Clears the OOF gate; still needs stress + notebook smoke + format audit before submission. |
| G | submission audit | only if B–F clears the gate | TODO | ≤2 submissions this sprint |

## Per-direction records
### A — error decomposition (RUNNING)
- inputs: DWT OOF (`combo_state.npz`), PF OOF (`pf_oof_full773.npz`), truth, per-well geometry/GR/typewell
  features, GBM per-model disagreement (`sunny_oof.npz` `per_model`, lightgbm-1/2/3 std).
- leakage/compliance: all features derived from test-available columns (MD,X,Y,Z,GR,TVT_input + typewell
  TVT,GR) EXCEPT `tvt_shift`/`truth` which are diagnostic-only and must NOT enter any deployable selector.
- smoke: script ran to completion on a 2-min foreground attempt (timed out on I/O) → moved to background.
- full: `python3 $JOB/tmp/a_error_decomp.py` (bg `b1w8rzrpm`) → `decomp_features.csv`.

### B — selector with asymmetric confidence (RUNNING, key test)
- hypothesis: `pf_unc` (weighted seed-spread) high → trust DWT; `gbm_disagree` high → trust PF. These are
  directional, unlike previously-tested symmetric features.
- inputs: A's feature table + `pf_unc.npz` (pred, truth, unc, likdisp).
- leakage: selector trained with nested GroupKFold by well; only test-available features.
- smoke: PF-uncertainty harness TINY SMOKE **PASS** (3 wells, NS=4: unc mean 1.78, range [0.001,8.06], finite).
- full: `NS=24 MAXW=773 BATCH=16 python3 $JOB/tmp/pf_unc_oof.py` (bg `b41znz17x`, ckpt+resumable).
- gate: nested OOF < 9.2969 with stable bootstrap, else record negative and close.

### C–G — see individual reports as they are produced.

## RECOVERY RECORD (session `3f11942e` → `4d6cd351`)
**Interruption cause:** the previous Claude Code process exited; all three background items were bound to its
lifecycle and died with it (Claude-managed background shell jobs do not survive process exit).

| job | state at interruption | artifact | action |
|---|---|---|---|
| `b41znz17x` PF-uncertainty OOF | stopped at **64/773 wells** | `pf_unc.npz` VALID (64 wells / 339,618 rows / 5 keys / CV 11.3498 / meanUnc 1.515) | **resumed from checkpoint** (`todo=709 resumed=64` confirmed in log) |
| `b1w8rzrpm` A error decomposition | died during the 773-CSV load | `a_decomp.out` **0 bytes**, no `decomp_features.csv` | **re-run** (added flushed progress printing so it is monitorable) |
| F external-pipeline scan agent | **failed**, in-process state lost | none | **relaunched** |

**Durability fix (applied):** long runs now live in a **stable shared dir**
`/home/ubuntu/.claude/jobs/rogii_sprint_shared/tmp/` (the per-session `$CLAUDE_JOB_DIR` changes on restart and
would orphan checkpoints), and are launched **detached via `setsid nohup`** so they reparent to init
(**PPID=1**, own session id) and survive a Claude exit. Verified: PF-unc pid 24489 PPID=1, A pid 24571 PPID=1.

## Running jobs (all detached, resumable)
- **PF-uncertainty OOF** — pid 24489, resuming 709 remaining wells, ckpt
  `rogii_sprint_shared/tmp/pf_unc.npz`, log `pf_unc.log`. Re-runnable/resumable at any time with the same
  `CKPT=`/`LOG=` env.
- **A error decomposition** — pid 24571, log `a_decomp.out` → `decomp_features.csv`.
- **F external-pipeline scan** — analysis agent (read-only).
