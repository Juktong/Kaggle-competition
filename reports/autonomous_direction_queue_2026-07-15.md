# ROGII — Autonomous direction queue (2026-07-15)

Single continuous session (`16baec36`) working the full one-shot task pack. Baseline = honest DWT
(public **9.519**, internal native-mask CV **10.40**, ref 54453597). Overlap/public hedge = Plane
Top2 Gate-Safe (public **7.212**, ref 54289934). Neutral technical language; honest OOF/masked-CV as
the private proxy; public-hedge kept strictly separate from honest work.

## Inherited state (from prior sessions / v2-sa-v5 branch)
- **V1** marker gate: GR→formation learnable (OOF acc 0.486 vs 0.282 majority) but predicted-marker
  blend weight **−0.095** → facies branch closed (signal already in DWT).
- **V2** structural-surface gate: **oracle-positive** (true surf−Z blend weight **+0.216**, first
  positive oracle; 10.39→10.14) but **achievable-negative** (OOF-predicted surf blend weight −0.020 =
  base). New ledger category *oracle-positive / achievable-negative* = **label-availability ceiling**.
  N-A/N-B GPU **not warranted**.
- **S-A** final-2 optimization: **B4′+DWT weakly dominates DWT+HEDGE at every overlap fraction f**
  (max advantage 1.28 RMSE); B4′ = strongest single submission; DWT slot = false-positive safety net.
- **V5** visible-well pre-submit audit tool built (`scripts/visible_well_audit.py`).

## Scoreboard

| # | Direction | Status | Compute | Submission | Key metric | Decision |
|---|---|---|---|---|---|---|
| 0 | Init/hygiene: worktree, artifacts, submissions, processes | done | CPU | — | 54723189 PENDING; no live proc; no local GPU | proceed |
| 1 | **B4′ guarded honest+overlap** (highest priority) | **COMPLETE — public 9.864** | CPU+notebook | **54727655** | FP=0, visible recon 0.000; but base post-proc variance → 9.864 > banked DWT 9.519 | mechanism validated; NOT a slot upgrade |
| 2 | Duplicate-detector hardening variants | done (folded into B4′) | CPU | — | tight gate tvt_rmse<0.02, 0 FP incl hard near-collision | adopted |
| 3 | V3 stratified blend audit | done — negative | CPU | — | pooled OOS gain **−0.0024**; 2/16 cells +0.03 (noise) | close |
| 4 | B3′ hidden-batch transductive diagnostic | done — negative | CPU | — | corr(e,e_nn)**+0.03** (−0.10 densest); oracle transduct worse | close (no Kaggle diag) |
| 5 | B1′ real strong public pipeline OOF | done — assessed | CPU | — | matcher ρ0.65 (best real OOF) → V3 pooled gain −0.0024; GPU full-run not warranted | close (defer GPU) |
| 6 | Final-2 portfolio optimizer update | done | CPU | — | best-of-2=min-pooled; B4′ self-floors at DWT; slot-2 = free option | {B4′,DWT} robust / {B4′,Sunny} upside |
| 7 | Submission productionization + audit harness | done | CPU | — | `presubmit_gate.py` + ledger + reproducible B4′ notebook | delivered |
| 8 | ≥5 additional new directions + cheap gates | done | CPU | — | 8a B4′-recall robust; 8d best-of-2 confirmed; 8b/8c/8e closed | no new RMSE lever; B4′ hardened |
| 9 | Commit / PR / Chinese final report | in progress | — | — | — | — |

## Environment facts
- Worktree: `.claude/worktrees/autonomous-queue` (branch `codex/autonomous-queue-2026-07-15`, based on
  the completed v2-sa-v5 tip 959f800). Data + large artifacts live in the MAIN checkout
  (`/home/ubuntu/workstation/JoeProject/Kaggle-competition/data/rogii`, gitignored) — scripts read
  from there via absolute paths.
- Data: 773 train wells (each `__horizontal_well.csv` + `__typewell.csv` + `.png`); 3 visible test
  wells (000d7d20, 00bbac68, 00e12e8b) that are **byte-identical** to their train twins.
- Train horizontal cols: `MD,X,Y,Z,ANCC,ASTNU,ASTNL,EGFDU,EGFDL,BUDA,TVT,GR,TVT_input`.
  Test horizontal cols: `MD,X,Y,Z,GR,TVT_input`. `TVT_input` = known heel prefix (finite) then NaN in
  toe; submission = toe rows only, id `{well}_{ridx}`, 14,151 rows over the 3 visible wells.
- Cached DWT native-mask OOF: `/home/ubuntu/.claude/jobs/3fa775c0/tmp/combo_state.npz`
  (well/ridx/oof/yt/base/cut over 773 train wells).
- No local GPU (nvidia-smi empty); GPU only via Kaggle. No live python/kaggle processes.

## Kaggle submission ledger (relevant)
| ref | public | what | role |
|---|---|---|---|
| 54453597 | **9.519** | DWT honest base (5-model) | honest primary |
| 54289934 | **7.212** | Plane Top2 Gate-Safe | overlap hedge |
| 54710185 | 8.864 | Sunny PF90 beam-mean10 test-only | architecture hedge |
| 54672680 | 8.874 | Sunny PF75 beam-median25 test-only | architecture candidate |
| 54723189 | **PENDING** | spatial formation surface w30 guarded strict LOO | monitor |
| 54174151 | 7.182 | active-account baseline (base+overlap stack) | prior best public |

(Full detail appended per-direction below as work proceeds.)

---

## Direction 1 — B4′ guarded honest+overlap (built + validated)

**Detector** (`scratchpad_probes/b4_duplicate_detector.py`, `scripts/b4_guarded_override.py`).
Per-well, precision-first. Two match tiers (same-id, then fingerprint by heel-location), both gated by
the proven-tight agreement test adopted from the public guarded-recovery (david_v12): on the test
well's KNOWN region, interpolate the train twin's Z/GR/TVT onto the test MD grid and require
`tvt_rmse < 0.02 ft AND z_mad < 0.02 AND gr_mad < 0.50 AND ≥50 overlap rows`. Reconstruction =
`np.interp(toe_MD, train_MD, train_TVT)`. Per-well (not all-or-nothing → novel wells keep DWT).

**Validation (all local, honest):**
- **False positives = 0** on 773 train non-twin wells (no train well matches any *other* train well;
  distinct wells have distinct fingerprints). Tighter gate (tvt_rmse<0.02): still 0 FP.
- **Zero genuine train-train twins** — the only near-collision (8b95d6d1 ↔ a2e8e7f6: identical X/Y/Z/GR
  geometry over the known region) has **TVT_input differing on 40% of rows** → correctly REJECTED by the
  TVT agreement guard (proves geometry-alone matching is unsafe; the TVT guard is essential and working).
- **Reconstruction exact:** 771/773 self-match with recon RMSE 0; all 3 visible test wells → exact twin,
  recon RMSE **0.000**. V5 pre-submit audit PASS (format/finite/range OK, visible pooled RMSE 0.000).
- Embedded Kaggle cell re-tested standalone against local data: visible RMSE 0.000, all finite, id-set
  preserved. LAM set 1.09→**1.0** to recover the honest 9.519 base (pulled notebook had the disproven
  LAM=1.09 = public 10.138). Override wrapped in try/except → on any error keeps DWT unchanged (B4′ ≥ DWT).

**Compliance:** within-competition-data overlap only (no external data); identical mechanism to the
already-banked hedge (ref 54289934) and the public 7.2 plateau. Worst case (novel-heavy private, f=0)
→ B4′ == DWT exactly (override never fires). Low-risk / established. Notebook `kaggle_kernel_b4_guarded/`,
kernel `joezzzzz/rogii-b4-guarded-codex`.

**RESULT (public 9.864) — honest diagnosis.** B4′ scored **public 9.864**, i.e. **0.345 WORSE than the
banked DWT 9.519** — not the expected `≤ DWT`. Root cause is **DWT-base post-proc variance, NOT the
override:** the notebook re-runs the optuna post-proc with `n_jobs=-1` (non-deterministic), and this run
drew `{alpha 1.0, tau 55, w_pf 0.08}` (best trial 231, internal CV **10.4009**) versus the banked run's
smaller-tau draw — **same internal CV 10.40, different public (9.864 vs 9.519)**. This is exactly §7's
"held-out CV is misleading for post-proc," now manifesting as *public variance across optuna draws at
fixed CV* (`tau` sets the drift ramp `1−e^{−md_since/τ}`; τ=55 ⇒ slower ramp ⇒ different toe). The
override itself is sound (FP=0, exact recon, try/except self-floor); on this public split it was a
**no-op** (B4′ was not pulled toward the ~7.2 overlap band), so the 9.864 is essentially the base.
**Why the override was a no-op — the deeper reason:** the proven Gate-Safe hedge reaches **7.212 on the
same public split**, so exploitable overlap *does* exist there — yet my exact-match override captured
**none** of it (B4′ stayed at the base 9.864). A true exact duplicate would clear `tvt_rmse<0.02` (the 3
visible wells give tvt_rmse=0), so the hidden overlap is **not exact-duplicate form** — most likely
**affine-overlaid** train wells (consistent with §1's affine-overlay evidence, 7.278/7.294). My
precision-first *exact* gate is therefore mismatched to the actual overlap: it guarantees FP=0 but
captures ~0 of the affine overlap that Gate-Safe exploits. A B4′ that captured this overlap would need an
affine-aware (but still FP-safe) override — i.e. it would essentially recreate the Gate-Safe mechanism on
a DWT base; since the Gate-Safe hedge already occupies the overlap slot, this is lower-value than it first
appeared. (The alternative reading — a low-overlap public split — is ruled out by Gate-Safe's 7.212.) **Consequences:** re-running the DWT notebook does not
reproduce the banked 9.519 (no local backup; optuna non-deterministic) → the **banked ref 54453597 is
the reliable honest slot** (Kaggle reruns its frozen version on private). B4′-as-submitted is NOT a slot
upgrade over the banked DWT. The override *mechanism* is validated and kept for future use (e.g. a
looser-but-still-safe gate, or if private overlap is confirmed). **Lesson:** to stack an override on the
honest base, sit it on the banked kernel version / pin the post-proc — do not re-optuna.

## Direction 3 — V3 stratified blend audit (negative)
Row-level nested well-split blend of DWT + matcher (corr 0.65, most decorrelated candidate) across
distance-from-cut × DWT-drift-magnitude quartiles (test-available strata). **Pooled out-of-sample gain
= −0.0024 RMSE.** Only 2/16 cells positive-stable (+0.03 in ~12% of rows → ~+0.004 global), surrounded
by sign-flipping neighbors (noise signature). Large apparent gains all come from negative-w* cells (the
λ-disguise drift-rescaling, public-rejected). Blend-neutrality is uniform at row level — extends the
prior well-family routing negatives (§9,§13-S3). Scripts: `$JOB/tmp/v3_strat.py`, `v3_nested.py`.

## Direction 4 — B3′ transductive / hidden-batch diagnostic (negative)
Tests the prerequisite for any batch transduction: is DWT's whole-well toe-offset error (std 7.93)
spatially structured? corr(e_well, e_nearest_neighbor) = **+0.029** overall; **−0.10** in the densest
10–25% of wells (nn_dist≤350). Oracle transduction (subtract neighbor residual) makes it *worse*
(std 7.93→10.36; densest 6.57→9.64). The offset error is per-well idiosyncratic (interpretation
selection), not a spatial field — so a batch-level structural-field correction cannot help. Train
simulation negative → **STOP B3′** (no Kaggle hidden-batch metadata diagnostic warranted). Confirms and
strengthens §11/§12 spatial-field negatives. Script: `$JOB/tmp/b3_transduct.py`.

## Direction 5 — B1′ real independent-pipeline OOF (assessed; GPU deferred)
The most-decorrelated *real* OOF available (the matcher, ρ=0.65 with DWT) already gives a row-level
nested pooled blend gain of **−0.0024** (V3) — the B1′ answer for the strongest-decorrelated pipeline on
hand. A NEW heavyweight pipeline (romantamrazov 9.956 / the 9.538 kernel) is *weaker* than DWT on the
honest manifold (board 9.5–10), so by the §11 relation (ρ≈σ_D/σ_M for same-input models) it lands
blend-neutral; its full OOF needs GPU + heavy fork-ops (§3) for a predicted-neutral result → **not
warranted**. The one architecturally-different, *stronger-than-DWT* candidate is **Sunny PF (8.864,
54710185)** — a submission-level candidate (no train OOF; different PF/beam architecture, no overlap-copy
trick), handled in the final-2 portfolio (Direction 6) as a best-of-2 free option, not a blend input.

## Direction 6 — Final-2 portfolio update (see `final2_update_b4_built_2026-07-15.md`)
Best-of-2 = **min of two pooled private scores** (confirmed standard Kaggle rule, Direction 8d). B4′
**self-floors at DWT** (try/except → DWT on any override error; FP=0; exact recon on true dups) ⇒ B4′ ≥ DWT
by construction and dominates the hedge at every f ⇒ **B4′ is the correct slot-1**. Slot-2 is a free option:
DWT is redundant (B4′ ⊇ DWT), the hedge is dominated; the only slot-2 that can improve the pair is a
genuinely-different, potentially-stronger model on novel wells = **Sunny PF90 (8.864)**.
- **Robust lock:** `{B4′ 54727655, DWT 54453597}` (both proven honest; DWT anchor).
- **Upside upgrade (best-of-2 free option, evidence-gated):** `{B4′, Sunny PF90 54710185}` — adopt iff B4′
  public confirms ≥DWT behavior AND Sunny's novel-well honesty is checked.

## Direction 7 — Productionization + audit harness (delivered)
- `scripts/presubmit_gate.py` — one command: V5 visible-well audit + format/finite/range/diff-vs-DWT →
  PASS/FAIL + reproducible JSON+markdown audit record. Verified on the B4′ Kaggle submission (PASS;
  `experiments/presubmit/B4_guarded_54727655_presubmit.{json,md}`).
- `reports/submission_ledger_2026-07-15.md` — ref/public/role/source/commit/audit/decision per submission,
  full B4′ record, reproduce-any-candidate commands.
- B4′ notebook `kaggle_kernel_b4_guarded/` committed + reproducible (push+submit commands in the ledger).

## Direction 8 — Five genuinely-new cheap gates (no new RMSE lever; B4′ hardened)
| # | direction (why not a repeat) | cheap gate | result | decision |
|---|---|---|---|---|
| 8a | B4′ recall on *realistic* hidden-dup forms (resampled MD / GR-noise), not just byte-identical | detector recall + FP on 60 perturbed train wells | **recall 60/60, FP 0** for MD-shift & GR-noise (MD-interp handles it); only heel-truncation drops recall (unrealistic) | POSITIVE — coverage robust; no change needed |
| 8b | GR-sequence hash as an independent 3rd fingerprint | uniqueness/separability of GR-quantile signature | not needed — gate already FP=0 + full realistic recall; GR has NaNs in some known regions (handled by masks) | closed (adds no precision) |
| 8c | per-well `.png` — a data artifact not yet used | test-available? adds info? | PNGs are **train-only** (absent from test/), CSV visualizations → unusable at inference | closed (train-only) |
| 8d | confirm compliance linchpins (best-of-2 rule; external-data clause) | web check | **best-of-2 CONFIRMED** (standard Kaggle) → de-risks final-2; ROGII external-data clause still JS-gated → manual (B4′ uses no external data) | best-of-2 locked; S-B still gated |
| 8e | targeted heel-shrinkage for high-drift wells (reduce, not inflate, drift) | OOF RMSE at s∈{.02,.05,.1,.2}, top-drift quartile | every shrink **HURTS** (−0.024 … −0.40); DWT drift not over-scaled | closed (mirror of λ/dip-reversion) |

Round read: no new honest RMSE lever (consistent with the label-availability ceiling), but 8a confirms B4′
captures the realistic overlap forms and 8d confirms the final-2 rule. Scripts: `$JOB/tmp/d8a_recall.py`,
`d8e_shrink.py`.

## Conclusion (queue exhausted)
- **Delivered:** B4′ built, locally validated (FP=0, visible recon 0.000, V5 PASS), submitted, and
  **scored (54727655 = public 9.864)**. Audit harness + submission ledger + reproducible notebook shipped.
- **B4′ outcome (honest):** public **9.864 > banked DWT 9.519** due to **DWT-base post-proc optuna
  variance** (this run drew τ=55, internal CV 10.40, same CV / worse public), NOT override harm (override
  validated, was a no-op on the public split). Re-running the DWT notebook does not reproduce the banked
  9.519 → **the banked ref 54453597 is the reliable honest slot.** B4′-as-submitted is not a slot upgrade.
- **Closed this round (honest negatives):** V3 stratified blend (−0.0024), B3′ transductive (no spatial
  error structure), B1′ blend (matcher −0.0024; new GPU pipeline not warranted), 8b/8c/8e. All consistent
  with the label-availability / information ceiling for the honest RMSE frontier.
- **Recommended final-2 now (REVISED):** **`{DWT 9.519 (54453597), Gate-Safe 7.212 (54289934)}`** — the
  robust, proven pair (S-A's original): proven honest base + proven overlap hedge, best-of-2 hedged across
  private-composition scenarios. **Top upside candidate to verify:** Sunny PF90 (8.864, 54710185) — best
  public among plausibly-honest candidates, different PF/beam architecture; if its novel-well honesty is
  confirmed it is a best-of-2 free-option upgrade for either slot. B4′ is NOT recommended for a slot
  (worse base than the banked DWT; override showed no public overlap capture).
- **Remaining blockers:** 54723189 (structural-surface guarded, prior session) **remained PENDING >4h**
  through session close — Kaggle rerun queue backlog / slow notebook; it does not affect the final-2
  recommendation regardless of its eventual score (it is a structural-surface guarded router, dominated
  by the proven Gate-Safe hedge for the overlap slot). Sunny PF novel-well honesty unverified (needs its
  OOF / a light audit — the top follow-up); ROGII external-data clause still needs manual human
  confirmation (only blocks external-data S-B).
- **Session close (16baec36):** queue exhausted; deliverable = robust final-2 `{DWT 9.519, Gate-Safe
  7.212}` + documented B4′ experiment (exact override, precision-first per spec; honest negative: base
  post-proc variance + affine hidden-overlap). Next-iteration paths recorded (Sunny-PF verification;
  base-pinned/affine-aware B4′ if ever justified). PR #2 (draft) carries all work.
- **Key lesson recorded:** to stack an override on the honest base, sit it on the *banked kernel version*
  or pin the post-proc — do not re-run the non-deterministic optuna (fixed CV ≠ fixed public, §7).
