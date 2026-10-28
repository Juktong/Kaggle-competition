---
id: n3_multiscale_gr_matching
priority: 140
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# N3 Coarse-to-fine multi-scale GR matching (diagnostic)

Test whether the scale mismatch that closed the earlier GR-scorer line disappears under wavelet
decomposition.

Context (do not re-derive):

- The closed local-window learned GR scorer line was closed with a named cause: a ~34x vertical scale
  mismatch in the pairing, NCC baseline 0.524 (chance).
- Multilevel wavelet decomposition followed by coarse-to-fine matching is the standard remedy for that
  specific failure. Every previous attempt in this repo matched at a single scale.
- The repo's own base model is a DWT fork, so the decomposition machinery already exists.

Required execution:

1. 4-level DWT of the horizontal-well GR and the typewell GR.
2. Compute the alignment scorer AUC **per level**, using the same pairing protocol and the same
   held-out wells as G3.2 so the numbers are comparable.
3. Report whether any level exceeds G3.2's single-scale AUC of 0.7242, and at which level structure
   peaks.
4. Diagnostic only — no model training, no full run. If a level clearly wins, hand it to N1 as the
   scorer input rather than developing it here.

Write:

- `reports/n3_multiscale_gr_matching_2026-07-28.md`

No submission.
