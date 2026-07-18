# ROGII — DWT+PF blend Kaggle smoke → submit (2026-07-18)

Session `06dd2efb` (resumed). Kaggle-side smoke + submit of the honest DWT+PF blend whose local honest OOF =
**9.2969 vs DWT 10.3987 (+1.10)** — the strongest honest signal in the project (see
`sunny_physical_oof_2026-07-18.md`). Neutral technical language. Kaggle CLI:
`/home/ubuntu/workstation/JoeProject/kaggle-api-workbench/.venv/bin/kaggle` (account `joezzzzz`).

## 0. Pre-conditions (verified this round)
- No ROGII agent in `working` state (no conflict). Kaggle CLI 2.2.3 OK. Today (07-18) has **0** prior
  competition submissions → budget available.
- Kernel `kaggle_kernel_dwt_pf_blend/` metadata: slug `joezzzzz/rogii-dwt-pf-blend-codex`, competition
  `rogii-wellbore-geology-prediction`, dataset `ravaghi/wellbore-geology-prediction-artifacts`,
  **CPU (enable_gpu=false)** — correct: the notebook is DWT-GBM (artifacts pre-loaded, no training) + numpy
  particle-filter forward; GPU is unnecessary and would not speed the numpy PF. Left CPU.

## 1. Push + smoke (interactive run = 3 visible wells)
- **v1 pushed** OK (`kernels push`). Interactive run executes the full notebook on the 3 visible test wells
  (the Directive-4 smoke); a competition Submit later reruns on the hidden novel wells.
- **Smoke status: COMPLETE (KernelWorkerStatus.COMPLETE), 0 errors.** Interactive run ~9.5 min (artifact
  load + DWT inference ~517s, then PF on 3 wells @ NS=64 ~54s).
- **Smoke log — PF-blend execution evidence (verbatim):**
  `[PF-blend] test wells=3 NS=64 W=0.5 SMOKE=False` ; `[PF-blend] PF rows=14151 finite=True
  range=[11598.6,12241.2]` ; `[PF-blend] coverage 14151/14151 rows blended (W=0.5)` ;
  `[PF-blend] mean|PF-DWT|=3.05ft ; avg blend shift=1.53ft`.

## 2. Output validation (on the smoke submission.csv) — ALL PASS
- rows=14,151 == sample_submission ✓ ; id order identical ✓ ; id set identical ✓ ; TVT all finite (0 NaN) ✓ ;
  TVT range [11596.4, 12239.0] sane ✓ ; PF coverage 14,151/14,151 = 100% ✓ ; log has `[PF-blend]` lines ✓ ;
  log error-like lines = 0 ✓ ; leak-term (`tvt_from_contacts`/EGFDU/`guarded_contact`) mentions in executed
  log = 0 ✓.
- **Bonus mechanical check** — the smoke ran on the 3 visible (exact-twin) dev wells whose truth is known:
  honest blend RMSE = **3.94** (000d7d20 3.03 / 00bbac68 4.22 / 00e12e8b 4.24) vs DWT-OOF 7.23 on the same
  rows → the blend produces accurate preds on real wells (consistent with the OOF). NOTE: public/private LB
  use HIDDEN wells at rerun, so this is a mechanics validation, not an LB prediction.

## 3. Pre-submit audit (Directive 1)
- (a) Honest inputs only: the PF cell reads hw[MD,X,Y,Z,GR,TVT_input] + tw[TVT,GR]; NO `tvt_from_contacts`,
  NO EGFDU/structural surfaces, NO `hw['TVT']` toe truth. DWT part = banked det-base notebook (audited).
- (b) Format/order/finite/range PASS (local + smoke). Blend weight fixed 0.5, no test-time tuning.
- **Gate: honest OOF improvement 9.2969 vs DWT 10.3987 is clear + reproducible + robust (bootstrap 100%
  positive, decorrelation-driven) → submission authorized per Directive 1.**
- Audit result: **PASS** (all checks green; leak-grep of the executed Kaggle log = 0).

## 4. Submission
- **Submitted (code-competition kernel submission): `kaggle competitions submit -k joezzzzz/rogii-dwt-pf-blend-codex -v 1 -f submission.csv`.**
  ref **54804893**, time **2026-07-18 09:51:05 UTC**, status **PENDING** (hidden-well rerun in progress).

## 5. Public score + final-2 meaning
- **Public score: <PUBLIC_SCORE>** — note: public = 3 visible OVERLAP wells (leakage game); an honest blend
  (no overlap exploitation) is NOT expected to beat overlap plays (Gate-Safe 7.212) on public. The value is
  on the hidden/novel PRIVATE set (the prize), which the honest OOF 9.30 proxies. Interpretation vs DWT
  public 9.487 and vs the OOF: <PUBLIC_INTERPRETATION>
- **final-2 implication: <FINAL2>**

## 6. Ledger row
| ref | public | candidate | class | source | final-2 role |
|---|---|---|---|---|---|
| 54804893 | <PUBLIC_SCORE> | DWT+PF blend | honest decorrelated model blend | `joezzzzz/rogii-dwt-pf-blend-codex` v1 (commit 8544143) | **honest slot (OOF 9.30, +1.10 vs DWT)** |
