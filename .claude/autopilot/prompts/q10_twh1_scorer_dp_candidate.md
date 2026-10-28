---
id: q10_twh1_scorer_dp_candidate
priority: 200
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q10 TWH=1 Scorer + DP Candidate

Use the strongest open signal from N3: typewell window `TWH=1` (3 ft) improved held-out-WELL AUC to
`0.7655 +/- 0.0030` versus `0.7300 +/- 0.0028` at the earlier `TWH=8` setting.

Goal:

- Turn the `TWH=1` scorer signal into an actual TVT candidate, not only an AUC observation.
- Use held-out-WELL validation only; do not use pair split for model selection.
- Compare against flat-anchor, G3.2, and the deployed honest pipeline.

Required execution:

1. Live refresh and read `reports/n3_multiscale_gr_matching_2026-07-28.md` and `reports/g32_learned_alignment_smoke_2026-07-28.md`.
2. Build a small candidate where the `TWH=1` score is used as a DP/Viterbi emission.
3. Use nested held-out-WELL split for any transition/hyperparameter choice.
4. Report:
   - scorer AUC by WELL;
   - DP RMSE vs flat-anchor;
   - nested performance;
   - failure cases by well family/typewell key.
5. If it beats flat and materially narrows the gap to deployed honest, prepare Kaggle smoke.
6. Submit only if smoke/full/audit pass and the output is non-homogeneous with clear information value.

Write `reports/q10_twh1_scorer_dp_candidate_2026-07-29.md`.
