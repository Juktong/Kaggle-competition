# ROGII — Submission ledger (through 2026-07-15 autonomous queue)

Reproducible record of the submissions that matter for the final-2 decision. Public score is Kaggle's
hidden-rerun public split; private is hidden until close. Honest models: public ≈ private. Overlap/
public plays: public ≪ private (they revert on novel wells). Source = the kernel/notebook that produced
the submission; the B4′ notebook lives in this branch.

| ref | public | role | source (kernel / notebook) | commit | pre-submit audit | decision |
|---|---|---|---|---|---|---|
| **54727655** | pending | **B4′ guarded honest+overlap** (slot-1 candidate) | `joezzzzz/rogii-b4-guarded-codex` v1 = `kaggle_kernel_b4_guarded/rogii-b4-guarded-codex.ipynb` | `codex/autonomous-queue-2026-07-15` | V5 PASS, visible RMSE 0.000, FP=0 | **submitted 2026-07-15 13:52; monitor** |
| **54453597** | **9.519** | honest primary / anchor | `joezzzzz/rogii-dwt-honest-codex` (LAM=1.0, 5-model) | banked | (banked) | keep — final-2 slot-2 (robust) |
| 54289934 | 7.212 | overlap/public hedge (kept separate) | Plane Top2 Gate-Safe | banked | (banked) | dominated by B4′; not a final slot |
| 54710185 | 8.864 | Sunny PF90 — independent PF/beam architecture | `henry_v10_sunny80_blend` | banked | — | final-2 slot-2 UPGRADE candidate (best-of-2 free option; gate: verify novel-well honesty) |
| 54672680 | 8.874 | Sunny PF75 — same class | (sunny) | banked | — | alt to PF90 |
| 54723189 | pending | spatial-surface guarded router (V2 structural direction) | codex | banked | — | monitor; likely overlap-guarded (dominated by B4′ for honest slot) |

## B4′ (54727655) full record
- **Source:** `kaggle_kernel_b4_guarded/rogii-b4-guarded-codex.ipynb` (28 cells) = the DWT honest
  notebook with two changes: (1) `LAM = 1.0` (recover honest 9.519 base; the pulled DWT notebook had
  the disproven LAM=1.09 = public 10.138), (2) an appended guarded-override cell (self-contained,
  try/except-guarded). Kernel `joezzzzz/rogii-b4-guarded-codex` v1, CPU, offline, dataset_source
  `ravaghi/wellbore-geology-prediction-artifacts`.
- **Mechanism:** DWT everywhere; per-well override reconstructs toe TVT from a matched train twin only
  when the tight gate passes (`tvt_rmse<0.02 ft`, z_mad<0.02, gr_mad<0.50, ≥50 overlap rows), via
  same-id then fingerprint tiers. Reconstruction = `np.interp(toe_MD, train_MD, train_TVT)`.
- **Local validation (honest):** FP=0 on 773 train wells (incl. the hard 8b95d6d1/a2e8e7f6 near-collision,
  rejected by the TVT guard); 771/773 self-match recon RMSE 0; 3 visible test wells → exact twin, recon
  RMSE 0.000. V5 pre-submit audit PASS (format/finite/range OK).
- **Kaggle run:** clean (5-model DWT base loaded, cb3 absent as expected; override fired on 3 duplicate
  wells, 14151 rows, tvt_rmse=0; no errors). Downloaded submission re-audited: visible pooled RMSE 0.000.
- **Audit record:** `experiments/presubmit/B4_guarded_54727655_presubmit.{json,md}`.
- **Why this submission was spent:** S-A identifies B4′ as the strongest single submission (weakly
  dominates DWT+hedge at every overlap fraction); it self-floors at DWT (≥ DWT by construction), so the
  downside is nil and the upside (private overlap capture on a strong honest base) is real. Compliance:
  within-competition overlap only, identical mechanism to the already-banked hedge (54289934).

## Reproduce any candidate
```
# regenerate + audit B4′ locally-embeddable override on the visible sample:
python3 scratchpad_probes/b4_duplicate_detector.py          # FP/TP/visible detector validation
python3 scripts/presubmit_gate.py --candidate <sub.csv> --name <name> \
        --out-dir experiments/presubmit --timestamp <iso>   # V5 audit + written record
# B4′ Kaggle notebook: kaggle_kernel_b4_guarded/  (push: kaggle kernels push -p <dir>;
#   submit: kaggle competitions submit rogii-wellbore-geology-prediction -k joezzzzz/rogii-b4-guarded-codex -v <n> -f submission.csv -m "...")
```
