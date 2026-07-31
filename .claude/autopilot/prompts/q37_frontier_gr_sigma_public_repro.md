---
id: q37_frontier_gr_sigma_public_repro
priority: 470
status: blocked
requires_gpu: true
can_submit: true
max_submit_cost: 1
---

# Q24 Frontier GR-sigma one-token public reproduction

**BLOCKED on `q36_gr_sigma_in_blend_oof` passing its 3-well gate.** Do not start otherwise.

Q19 established that `leonidzaporozhets/new-strategy-score-6-213` (advertised public 6.213 vs our 6.563)
is byte-identical to our pristine `kaggle_kernel_kaiwalya_public_tvt_6626_repro` on 44 of 45 normalised
code cells. The entire difference is inserting `* 1.3` on the PF GR-sigma line in code cell 29.

Required execution:

1. Re-verify the one-token diff against the current base before building (do not trust this note).
2. Build the kernel as a **one-line, diff-verified** change; state the exact diff in the report.
3. **Smoke first** — confirm the patched line is actually reached and that the output schema, row count,
   id order, finiteness and value range all pass. Never launch the full run before the smoke passes.
4. Do not overlap with another frontier full run in flight.
5. Apply the full submit gate. The advertised 6.213 is **author-advertised and unverifiable**; the report
   must state that and must not present it as a predicted gain.
6. Record ref, score, commit, kernel slug/version, output hash, reason, quota usage.
