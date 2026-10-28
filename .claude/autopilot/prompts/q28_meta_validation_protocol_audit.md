---
id: q28_meta_validation_protocol_audit
priority: 380
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q28 Meta Validation Protocol Audit

Audit whether our validation protocol is rejecting true improvements or accepting false positives.

Goal:

- Improve decision quality for the remaining submissions.
- Calibrate OOF, held-out-WELL, 3-well bootstrap, public transfer, and proxy metrics.

Required execution:

1. Read N4, Q10-Q16, and all submission ledgers.
2. Build a table of local metric vs public score for all submissions where both exist.
3. Quantify which metrics transfer:
   - OOF RMSE;
   - local public proxy;
   - non-homogeneity;
   - family diversity;
   - 3-well bootstrap;
   - run variance.
4. Update submit gate if needed.
5. Do not submit.

Write `reports/q28_meta_validation_protocol_audit_2026-07-29.md`.
