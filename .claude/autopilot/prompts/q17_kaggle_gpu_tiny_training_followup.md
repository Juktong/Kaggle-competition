---
id: q17_kaggle_gpu_tiny_training_followup
priority: 270
status: queued
requires_gpu: true
can_submit: true
max_submit_cost: 1
---

# Q17 Kaggle GPU Tiny Training Follow-Up

Run a small GPU-backed training follow-up only if Q10/Q11/Q13 show enough signal to justify training.

Goal:

- Use Kaggle GPU for a tiny learned scorer or ranker, not a long full training run.
- Verify that the model can improve held-out-WELL metrics beyond the no-training `TWH=1` score.

Required execution:

1. Live refresh and inspect Q10/Q11/Q13 reports.
2. If none of them show a real signal, mark this task HOLD and move on.
3. If signal exists, prepare a tiny Kaggle GPU smoke:
   - few wells;
   - few epochs;
   - explicit output checks;
   - log proof that GPU is available and the intended training path ran.
4. Expand only if smoke improves held-out-WELL metrics.
5. Submit only after full audit and gate.

Write `reports/q17_kaggle_gpu_tiny_training_followup_2026-07-29.md`.
