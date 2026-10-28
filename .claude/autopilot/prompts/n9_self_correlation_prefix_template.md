---
id: n9_self_correlation_prefix_template
priority: 190
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# N9 Self-correlation: the lateral's own known zone as the matching template

Score toe rows against the well's OWN known-zone GR instead of (or alongside) the typewell.

Context (do not re-derive):

- `reports/n6_public_solution_audit_2026-07-28.md`: a public methodology repo carries a full
  self-correlation feature group (multi-scale NCC vs the lateral's own known zone) alongside the typewell
  NCC group. Absent from our ledger.
- This is DISTINCT from the closed G3.5, which used the prefix to calibrate the toe *bias*. Here the
  prefix GR is a higher-resolution matching *template*.
- `reports/n3_multiscale_gr_matching_2026-07-28.md` established that the **level** cue dominates and NCC
  shape matching is at chance (0.490-0.517 across 9 wavelet bands x 6 windows). Self-correlation shares
  one instrument and one baseline with the target rows, so it removes the cross-instrument level offset
  by construction — that is the specific reason to expect it to behave differently from typewell NCC.
- Mechanism it relies on: a horizontal well re-crosses similar stratigraphic levels along the lateral, so
  toe GR can match prefix GR recorded at the same TVT.

Required execution:

1. For each toe row, build a scorer over candidate TVT states using the well's own known-zone GR at
   matching TVT as the template (level features preserved, not z-scored).
2. **Split by WELL, not by pair** — N3 established that G3.2's random pair split mis-ranks configurations
   and understates absolute AUC.
3. Report held-out-well AUC against N3's banked baselines: typewell scorer `TWH=1` LEARNED
   0.7655 +/- 0.0030 and the no-training level score 0.7352.
4. Report what fraction of toe rows have any prefix coverage at their true TVT — if coverage is low the
   mechanism cannot apply broadly, and that is the result.
5. Diagnostic only. Do not build a DP or a trajectory on it in this task: N1 established that the
   alignment gap is in the transition model, not the emission.

Write:

- `reports/n9_self_correlation_prefix_template_2026-07-28.md`

No submission.
