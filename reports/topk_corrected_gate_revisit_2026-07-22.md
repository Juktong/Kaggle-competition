# Top-K revisited under the corrected framework (2026-07-22)

Direction 7. The K=96 top-K shrinkage candidate had the best 760-well OOF (+0.3556, `topk96_l75` =
8.5070) and was held back last round for a negative 760-well bootstrap tail. Re-examined here under the
3-well gate. No post-public tuning.

## Result (from `scripts/eval_three_well_gate.py`)

```
topk96_l75:  OOF 8.5070  oofGain +0.3556 | ref760_5th +0.1397 | 3w_5th -1.946  3w_25th -0.396  P>0 59% | FAIL
```

Under the 760-well reference it is the **strongest** candidate (5th +0.1397). Under the corrected 3-well
gate it is the **worst** (5th −1.946), because path selection injects the largest per-row moves and thus
the widest per-well tail. Shrinkage `alpha` (direction 4) only scales that tail; the guard (direction 1)
cannot identify the harmful rows (AUC 0.53). So there is no pre-public/test-available mechanism that
lifts its 3-well 5th above zero.

## Conclusion

Top-K stays closed. The corrected framework makes the reason sharper than last round: it is not merely
"a large-N point estimate with a marginal tail" — it is the candidate **most** exposed to 3-well
variance, and the leaderboard cannot resolve its (local, non-transferring) OOF advantage. No submission.
