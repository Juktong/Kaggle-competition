---
id: q28_measurement_traps_ledger
priority: 672
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q28 (narrowed) Measurement-Traps Ledger

`q28_meta_validation_protocol_audit` was deferred with the condition *"revisit only if a measurement error
recurs."* **That condition has fired four times in roughly six hours**, which is why this narrowed successor
exists. It is not the general introspective audit the original proposed.

The four incidents, all from Q46–Q58 and all caught rather than shipped:

1. **A 12-well smoke over-stated its effect by 58%.** Q56: smoke +0.6050 / helps 91.7% / 3-well 5th +0.0836
   → 760-well truth +0.2541 / 68.9% / **−0.3238**. The smoke *passed* the gate and the full run *failed* it.
2. **An 8-well smoke produced a conclusion the 40-well run contradicted.** Q57's draft concluded "the DP
   declines the freedom it is given" from a well where the dip stayed nearly off; at 40 wells the dip was
   active on 42–46% of steps and path deviation rose 4.9 → 21.1 ft. The report had to be corrected.
3. **A saved column was not the deployed quantity.** Q58: the aligned frame's per-row `nnb` / `closest_surv`
   are **not** the deployed structural-field gate — the deployed gate comes from `struct_oof.npz`'s per-well
   meta. Using the wrong one left 2139 rows wrong and the reproduction 0.0008 off, concentrated in 6
   boundary wells.
4. **An API default returned the wrong artifact.** Q46: `api.kernels_output(slug)` serves the **latest**
   version, not the submitted one. Three teammate kernels that scored 6.563 / 6.669 / 6.678 all returned one
   byte-identical file.

Required execution — deliberately bounded, this is a **documentation** task:

1. Write `reports/measurement_traps_ledger.md`: one entry per trap, each with (a) the symptom as it first
   appeared, (b) the mechanism, (c) **the specific check that would have caught it**, (d) the round and the
   report where it was found. Cite the four above and sweep the earlier reports for any others already
   recorded as project rules (Rule #1, Rule #3, the Q17 / Q40 / Q42 rules, N1's and Q54's inert-constraint
   trap, the `pkill -f` self-match, `python3` block-buffering, `head` SIGPIPE, the `open(path,'w')`
   truncation that `scripts/append_section.py` exists to prevent).
2. Convert the checks into a short **pre-flight list** a future round can actually run, ordered by how often
   the trap has actually occurred, not by how severe it sounds.
3. State plainly which traps are **already** enforced in code (e.g. `append_section.append`, the anchored-
   insertion + `array_equal` degeneracy pattern from Q56, the `ridx`/truth-equality assertions in
   `q36`/`q56`/`q58`) and which are only conventions a reader must remember. The second list is the useful
   output.
4. **No new measurement, no CPU-heavy run, no submission.** If it cannot be written from existing reports,
   say so and stop rather than launching work.
5. Keep it to about one page of checks plus the incident table. A long document will not be read at the point
   of use, which is the whole failure mode being addressed.

Do **not** re-litigate any closed result. This task changes no conclusion; it records how the conclusions
were nearly got wrong.
