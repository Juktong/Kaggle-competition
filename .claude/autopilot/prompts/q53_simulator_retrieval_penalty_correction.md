---
id: q53_simulator_retrieval_penalty_correction
priority: 305
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q53 Simulator Retrieval-Penalty Correction

Q39 found that a load-bearing input to the final-slot simulator is a confound.

`scripts/final_selection_simulator.py` (and `scripts/q18_final_pair_stress.py`) encode
`retrieval = 0.080` for overlap-ON candidates, documented as
`6.643 overlap-OFF - 6.563 overlap-ON, i.e. 54968060 vs 54922806`.

**Those two kernels differ in TWO stages, not one.** Q39's code diff shows `54922806` also carries
`*1.3` on the PF GR sigma (cell 29). Decomposed against the pristine baseline (mean 6.6735 from the
code-identical replicate pair `54896975` 6.669 / `54923144` 6.678):

    overlap / retrieval   54968060 6.643 vs pristine 6.6735  ->  -0.031  (OFF slightly HELPS)
    GR sigma *1.3         54922806 6.563 vs pristine 6.6735  ->  -0.1105

and -0.1105 - (-0.031) = -0.080, i.e. the recorded "retrieval penalty" is the difference of two different
stages.

Required execution:

1. Re-run the four views with `retrieval ~ 0.03`, plus a sensitivity arm at `0.0`.
2. **Keep `54922806`'s GR-sigma edge NON-INERT under H-hidden** — it is a likelihood-width parameter, not
   a train-duplicate lookup, so it does not switch off on novel wells.
3. Report whether these change: the recommended pair; the tie structure (the old model made 9 pairs tie
   at 6.643); and the price of our-account-first (Q18 priced it at +0.000 worst / +0.040 mean *because of*
   the assumed tie).
4. Carry the counterweight explicitly and do not bury it: **Q36 measured this same GR-sigma multiplier on
   760 wells with truth and found it helps only 42.1% of wells with a NEGATIVE median per-well gain.** So
   the stage carrying the public advantage is the one our own held-out evidence says does not transfer
   broadly. Present both, and do not overstate the public edge as a private-ranking edge.
5. State clearly whether the owner's slot-1 decision changes, or whether it remains an ownership judgement.

No GPU, no smoke, no submission — this is arithmetic over already-recorded public scores.

Write `reports/q40_simulator_retrieval_penalty_correction_<date>.md`.
