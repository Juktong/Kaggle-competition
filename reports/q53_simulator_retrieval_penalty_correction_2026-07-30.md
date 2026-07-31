# Q53 — simulator retrieval-penalty correction

Date: 2026-07-29 17:05 UTC
Task: `q53_simulator_retrieval_penalty_correction` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Script: `scripts/q53_simulator_retrieval_correction.py` · Log: `reports/logs/q53_simulator_correction_2026-07-30.log`
Outcome: **complete. No GPU, no smoke, no submission. Quota 0/5.**

> Filename note: the prompt's last line still says `q40_...` — a leftover from my own renumbering of this
> task to `q53` last round. Written under the `q53` name to match the task id.

## 0. The answer in one line

**Q18's conclusion survives the correction, but its reasoning did not.** The price of the
our-account-first pair is **+0.0005 worst / +0.0402 mean** under the cell our own evidence supports —
essentially Q18's +0.000 / +0.040 — but reached through an entirely different mechanism. The owner's
slot-1 decision **does not change** and remains an ownership judgement.

## 1. What was corrected, and the two axes

The old input was `retrieval = 0.080`, taken as `54968060 6.643 − 54922806 6.563`. Q39 showed those
kernels differ in **two** stages. Against the pristine baseline **6.6735** (the mean of the code-identical
replicate pair, spread 0.009):

```
overlap / retrieval   54968060 6.643 vs 6.6735  ->  -0.031    (overlap OFF slightly helps)
GR sigma *1.3         54922806 6.563 vs 6.6735  ->  -0.1105
```

Because the correction changes *which stage* carries `54922806`'s edge, one axis is not enough. The rerun
sweeps two:

- **`retrieval_delta`** — what an overlap-ON candidate gains when overlap goes inert on novel wells:
  **−0.031 (measured)**, 0.0, and +0.080 (the old, confounded value).
- **`sigma_transfers`** — whether `54922806`'s GR-sigma edge survives on novel wells. **This is the axis
  that matters**, and it is not a strawman: Q36 measured this exact multiplier on 760 wells with truth and
  found it helps only **42.1%** of wells with a **negative median** per-well gain. So `False` is the arm
  our own held-out evidence supports.

## 2. The grid

```
retrieval sigma     | A: 54922806+54844628      | B: 54968060+54844628      | price of B (our-account)
-0.031    True      | worst 6.5630  mean 6.5475 | worst 6.6430  mean 6.6430 | worst +0.0800  mean +0.0955
-0.031    False     | worst 6.6425  mean 6.6028 | worst 6.6430  mean 6.6430 | worst +0.0005  mean +0.0402
 0.000    True      | worst 6.5630  mean 6.5630 | worst 6.6430  mean 6.6430 | worst +0.0800  mean +0.0800
 0.000    False     | worst 6.6735  mean 6.6182 | worst 6.6430  mean 6.6430 | worst -0.0305  mean +0.0248
+0.080    True      | worst 6.6430  mean 6.6030 | worst 6.6430  mean 6.6430 | worst +0.0000  mean +0.0400
+0.080    False     | worst 6.7535  mean 6.6582 | worst 6.6430  mean 6.6430 | worst -0.1105  mean -0.0152
```

The last-but-one row (`+0.080`, `True`) is the **old model**: price +0.0000 worst / +0.0400 mean — exactly
what Q18 reported. The **measured, evidence-supported** cell is (`−0.031`, `False`): price **+0.0005 worst
/ +0.0402 mean**.

**Two wrong inputs were cancelling.** The old model overstated the retrieval term (+0.080 instead of
−0.031) *and* implicitly let the GR-sigma edge survive under H-hidden. Correcting both moves the price by
0.0005. Correcting only one would have moved it to +0.080 and flipped the conclusion — which is why this
needed the two-axis rerun rather than a single parameter edit.

## 3. The three questions the task asks

### 3.1 Does the recommended pair change? — No, in any way that survives noise

Under the measured cell with `sigma_transfers=False`:

```
score-first        54896975 + 54922806      worst 6.6380  mean 6.6013
diversity-first    54844628 + 54922806      worst 6.6425  mean 6.6028
provenance-first   54844628 + 54922806      worst 6.6425  mean 6.6028
our-account-first  54844628 + 54968060      worst 6.6430  mean 6.6430
```

Score-first nominally moves to a frontier+frontier pair (`54896975 + 54922806`) — but by **0.0045**, which
is **half the 0.009 replicate spread**. That is not a distinction the instrument can make, and the pair has
family diversity 0. Diversity-first and provenance-first are unchanged at `54922806 + 54844628`.

With `sigma_transfers=True` all three of score-, diversity- and provenance-first give
`54844628 + 54922806`, unchanged from Q18.

### 3.2 Does the tie structure change? — It stays heavily tied

| cell | best worst | pairs tied within 0.01 |
|---|---|---|
| −0.031, True | 6.5630 | 6 |
| **−0.031, False** | **6.6380** | **11** |
| 0.000, True | 6.5630 | 6 |
| 0.000, False | 6.6430 | 6 |
| +0.080, True (old) | 6.6430 | 11 |
| +0.080, False | 6.6430 | 6 |

Q18 reported 9 tied pairs at 6.643. Corrected, the count is 6–11 depending on the cell and **11 in the
evidence-supported one**. The qualitative fact Q18 rested on — *score alone does not pick a unique pair* —
is unchanged and if anything stronger.

### 3.3 Does the price of our-account-first change? — Not materially

**+0.0005 worst / +0.0402 mean**, against Q18's +0.000 / +0.040. It would rise to **+0.080 worst** only in
the `sigma_transfers=True` arm, i.e. only if the GR-sigma edge transfers to novel wells — which is exactly
what Q36's 760-well measurement argues against.

## 4. The counterweight, stated plainly and not buried

`54922806`'s entire public advantage over the pristine baseline is the GR-sigma multiplier. Our own
held-out evidence on that same knob:

- **Q36**, 760 wells with truth, inside the deployed ensemble and blend: nested gain +0.1699 pooled, but it
  **helps only 42.1% of wells**, with **mean −0.1197 and median −0.0569** per well — a tail-driven pooled
  gain, the signature that preceded the `54878409` public regression.
- The H-hidden gap between the two slot-1 options in the measured cell is **0.0005** if the edge does not
  transfer and **0.1110** if it does.

So the whole slot-1 question reduces to a single unresolved quantity: *does GR-sigma widening help on
novel wells?* Public says yes on 3 wells; our truth-based measurement says it helps a minority of wells.
**The public edge must not be read as a private-ranking edge.**

## 5. Does the owner's slot-1 decision change?

**No. It remains an ownership judgement**, and the corrected model makes that firmer rather than weaker:

- under the evidence-supported cell the two pairs differ by **0.0005** on worst case — far inside the
  0.009 replicate spread, and inside Q18's separate finding that pooled gaps ≤ 0.30 reverse on ~45% of
  random 3-well draws;
- the only cell where the choice is materially priced (+0.080) requires assuming the GR-sigma edge
  transfers, which our own 760-well measurement does not support;
- so no additional public evidence can settle it, and **no submission would help** — consistent with Q33's
  standing conclusion that the next 24 h spends 0 slots.

Recommendation as it stands:

| view | pair |
|---|---|
| score- / diversity- / provenance-first | `54922806` + `54844628` |
| our-account-first | `54968060` + `54844628` (price ≈ +0.0005 worst, +0.040 mean) |

## 6. What should be updated in the code

`scripts/final_selection_simulator.py` and `scripts/q18_final_pair_stress.py` still carry
`retrieval=0.080` with the confounded derivation in their docstrings. **They were left unmodified this
round** so the Q18 record stays reproducible as written; `scripts/q53_simulator_retrieval_correction.py`
supersedes them and carries the corrected derivation. If either is rerun for a decision, use the Q53
script.

## 7. Limits

- Both stage effects come from **single public runs on 3 wells**, except the one replicate pair, which is
  **two runs** — not a distribution. The 0.009 spread and the recorded ~0.115 config-variance floor still
  disagree, and that reconciliation remains open (flagged in Q38 and Q39).
- The decomposition assumes stage effects are **additive**; the arithmetic is exact by construction but
  interactions are not measurable from six runs.
- `sigma_transfers` is modelled as binary. Reality is a degree, and Q36's 42.1% suggests partial transfer,
  which would land between the two rows.
- H-visible / H-hidden / mixed remain **hypotheses**. The private split is not visible, and no private
  score is visible for any submission.

## 8. Next

Queue continues with `q40_transition_model_search` (priority 590). `q29_final_slot_candidate_packager`
reactivates **2026-08-03**; the final selection action is due by **2026-08-04** and costs no quota.
