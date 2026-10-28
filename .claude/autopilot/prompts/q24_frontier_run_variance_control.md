---
id: q24_frontier_run_variance_control
priority: 340
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q24 Frontier Run Variance Control

Q14 found fresh GPU run variance confounds stage-isolation. Quantify and reduce run-to-run variance before
spending more submission slots on frontier variants.

Goal:

- Determine whether frontier differences are deterministic or runtime/config variance.
- Make future variant comparisons cleaner.

Required execution:

1. Compare stored outputs from `54968060`, Q14 hedge-OFF full, and any available reruns.
2. Identify sources of variance: seed, GPU nondeterminism, kernel data attachments, model package load order.
3. Try to pin deterministic settings in the notebook/kernel.
4. If a zero-change deterministic rerun is needed, smoke first; full run allowed only if it improves future decision quality.
5. Submit only if a deterministic rerun itself has slot value; otherwise hold.

Write `reports/q24_frontier_run_variance_control_2026-07-29.md`.
