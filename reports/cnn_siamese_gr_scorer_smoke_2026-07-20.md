# ROGII — CNN/Siamese GR local scorer: smoke results (direction E, 2026-07-20)

Session `e5b89aa5`. Goal: learn a GR local-window similarity to replace the hand-written NCC/PF emission
cost, then drive a DP/top-K global search. Script `scripts/cnn_siamese_gr_scorer.py`. Neutral technical
language.

## E1 — compute inventory
- **No local GPU**: `torch 2.12.1+cpu`, `cuda.is_available() = False`; box is 2 cores / 11 GB.
- Therefore any full train needs a **Kaggle GPU kernel**; all smokes below were run on CPU at tiny/medium
  scale, which the protocol requires before committing GPU time.

## Method (honest by construction)
- **positive pair** = (horizontal-GR window at row *i*, typewell-GR window centred at the TRUE TVT of row *i*)
- **negative pair** = same horizontal window vs a typewell window centred at TVT + offset, |offset| ≥ 10 ft
- Shared 1D-CNN encoder (Siamese) + concat/abs-diff MLP head → similarity logit; BCE loss.
- Inputs at inference are the target's own GR window and its typewell profile (both test-available); labels
  come from TRAIN wells' TVT, i.e. ordinary supervised use.

## E2 — tiny smoke (20 wells, 1 epoch, 12 k pairs, CPU, 7.8 s) — PASS
`train pairs 2396 / val 608` · train_loss 0.6935 · **val_acc 0.535 · val_auc 0.605**
Pipeline runs end-to-end (sampling → train → validation) with no shape/label faults.

## E3 — medium smoke (80 wells, 6 epochs, 40 k pairs, CPU, 43 s)
| epoch | train_loss | val_acc | val_auc |
|---|---|---|---|
| 0 | 0.6918 | 0.581 | 0.605 |
| 1 | 0.6806 | 0.571 | 0.621 |
| 2 | 0.6705 | 0.613 | 0.628 |
| 3 | 0.6678 | 0.608 | 0.639 |
| 4 | 0.6653 | 0.601 | 0.653 |
| 5 | 0.6661 | 0.581 | **0.657** |

## Assessment — signal present, but the gate is NOT met this round
1. The learned scorer discriminates aligned from misaligned typewell windows **better than chance**
   (AUC 0.605 → 0.657) and was **still improving** at epoch 5, so the direction is not exhausted.
2. But AUC 0.657 is **weak discrimination**. The PF's existing GR likelihood already performs this matching
   and yields OOF ≈ 11.0 on its own; replacing that emission cost with a scorer this weak has no demonstrated
   advantage.
3. Converting a window-similarity scorer into TVT predictions requires a full DP/Viterbi + top-K integration
   and its own OOF — substantial work that should follow evidence, not precede it.
4. **Decision: do not spend a full GPU train yet.** The tiny→medium protocol did its job: it surfaced the
   effect size cheaply (51 s of CPU total) instead of after hours of GPU time.

## What would change the decision (concrete, for the next round)
- A Kaggle-GPU run with a larger encoder / more pairs / more epochs reaching **val_auc ≳ 0.75**; or
- a mini-DP experiment showing the learned cost beats the NCC cost on a held-out well subset even at
  AUC ≈ 0.66 (i.e. the global DP tolerates a weak local scorer).
Both are cheap to check with the committed script (`DEVICE=cuda`, larger `MAXW`/`MAXPAIRS`/`EPOCHS`).
