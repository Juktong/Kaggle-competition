---
id: q58_honest_kernel_backward_smoothing
priority: 629
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q58 Honest-Kernel Backward Smoothing (carry Q56's smoother to the deployed line, then decide)

Q56 measured the ancestral-path PF smoother on **760 wells inside the deployed blend**:

```
forward (= deployed PF)          9.2903      (deployed blend `base` 9.2987; NS=32 vs 64 accounts for 0.008)
full smoother, alpha=1.0         9.0362      nested +0.2541, helps 68.9%, median per-well +0.2044
3-well bootstrap 5th             -0.3238     P(gain>0) 0.7919   <- the gate condition it FAILS
```

Mechanism verified there and not to be re-litigated: monotone in lookahead dose
(block25 +0.0205 → block100 +0.0768 → block400 +0.1898 → full +0.3686), monotone in alpha, and a
Savitzky-Golay denoising control that accounts for only ~10% of the gain. Honesty audit clean — the PF
touches no truth or train-only column, and the smoother adds no inputs.

**What is NOT yet known, and is the whole point of this task:** Q56's number is at the **blend** level. The
deployed honest line `54844628` (public 7.891) applies a **gated structural-field stage** after the blend,
worth +0.436 (9.2987 → 8.8626) — and that stage was **fitted against the forward PF**. Its gain is not
transferable as-is to a smoothed PF, and it could absorb, keep, or destroy the +0.2625.

Required execution:

1. Reproduce the smoother inside the honest line end-to-end: PF (with `perdip`-free ancestral smoothing,
   `full` mode, alpha chosen NESTED — do not hard-code 1.0 because Q56 selected it on the same data it
   scored) → blend → structural field → final prediction.
2. **Re-fit the structural-field stage against the SMOOTHED PF.** Report both: the old stage applied
   unchanged, and the re-fitted stage. If the re-fit needs a hyper-parameter, choose it NESTED.
3. Report the end-to-end honest OOF against **8.8626**, with per-well win rate and the 3-well bootstrap.
4. **SMOKE FIRST (Directive 4)** on ≤ 12 wells before any full run, and record the wall-time. Q56's own
   12-well smoke over-stated its effect by 58% — treat a smoke as an activation check, never as a size.
5. Use **NS=64** if the wall-time allows, since that is the deployed configuration; if NS=32 is used,
   state it and note the direction of the bias (more seeds = more ensemble averaging).
6. **Submission is permitted but not assumed** (`max_submit_cost=1`). Apply the standing submit gate in
   full. Note two things when deciding:
   - the 3-well bootstrap 5th was **negative** at blend level, and Q41 showed that condition is maximised
     by changing nothing while Q44 measured the 3-well draw's difference-sd at 2.40 ft — so it constrains
     what a *public* score can tell us, not necessarily novel-well quality;
   - Q44 measured slot 2 (the honest line) as the **largest positive term in the final-pair decision**
     (~0.46 ft mean / ~0.94 ft tail as the decorrelated member of a best-of-2). Improving the honest line
     improves the slot the project actually relies on, which is the strongest argument for spending a slot
     here — state it explicitly in the report if a submission is made.

Do not submit a near-duplicate: if the re-fitted line's output is not materially different from
`54844628`, say so and do not spend a slot.

Write `reports/q58_honest_kernel_backward_smoothing_<date>.md`.
