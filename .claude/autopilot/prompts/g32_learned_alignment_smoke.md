---
id: g32_learned_alignment_smoke
priority: 30
status: queued
requires_gpu: true
can_submit: true
max_submit_cost: 1
---

# G3.2 Learned Local Alignment Scorer + DP

Test whether a learned local GR-window scorer can provide a better emission signal than hand-written NCC/DTW.

Goal:

- Build positive/negative GR-window pairs from train wells using true TVT or masked split alignment.
- Train a tiny CNN/Siamese/local scorer.
- Plug the scorer into a DP/Viterbi alignment smoke.
- Use GPU if available and useful, but keep the first run tiny.

Required execution:

1. Build a minimal dataset of positive/negative window pairs.
2. Train a tiny model for a few epochs and verify:
   - loss decreases;
   - validation signal is above chance;
   - output scores can be consumed by a DP/Viterbi path search.
3. Compare against the known weak NCC baseline and flat-anchor baseline.
4. Run a small masked split only if the model smoke has real signal.
5. Do not launch full Kaggle unless smoke and masked split both support it.
6. Submit only if the candidate is non-homogeneous and passes the submit gate.

Write:

- `reports/g32_learned_alignment_smoke_2026-07-28.md`
- Any scripts needed for reproducible smoke.

If the learned scorer is at chance or does not beat baselines, close the task and move on.
