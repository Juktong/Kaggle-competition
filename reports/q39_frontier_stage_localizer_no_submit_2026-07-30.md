# Q39 — frontier stage localizer, from code diffs alone

Date: 2026-07-29 16:50 UTC
Task: `q39_frontier_stage_localizer_no_submit` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Outcome: **complete, with no public re-run and no submission. Quota 0/5.**
**Headline: the "0.080 retrieval penalty" that the final-slot simulator is built on is a confound.**

## 1. Method — every family member diffed against the pristine base

Q38 pulled all teammate kernels, so for the first time the whole family can be compared as *code* rather
than by description. Each member is normalised (comments and whitespace stripped) and diffed cell-by-cell
against `kaggle_kernel_kaiwalya_public_tvt_6626_repro` (the pristine public base, 45 code cells).

```
member                        cells   differing cells   the actual diff
54896975  6.669 (9 datasets)    45     NONE             — pristine
54923144  6.678 (7 datasets)    45     NONE             — pristine
54922806  6.563  OUR BEST       45     [29]             insert '*1.3'  (GR sigma)
54968060  6.643                 45     [0]              _profile['run_guarded_overlap_override']=False
54990075  6.690                 46     [0] +1 cell      overlap OFF + SP45-only truncation
55064411  6.695                 45     [0, 42]          overlap OFF + _BH_CAP 2 -> 0
pub 6.213 (advertised)          45     [29]             insert '*1.3'  — identical to 54922806
```

Every member is a **single- or double-factor** variant of one common base. That makes clean contrasts
possible without any re-run.

## 2. The replicate pair, and the variance it implies

`54896975` and `54923144` are **code-identical** (both diff to NONE) and were run on different days:

```
54896975  2026-07-22  ->  6.669
54923144  2026-07-23  ->  6.678
                          -----
same-code spread          0.009        baseline mean 6.6735
```

Their only difference is two attached datasets (`thbdh5765/rogii-v11-fresh-artifacts`,
`chesnikovleonid/rogii-v50-dwt-phaseb-modelonly`), both classified **vestigial** by G1.3 — and the 0.009
spread is consistent with that. This pair is the reference point every contrast below is measured against.

## 3. THE CORRECTION — the simulator's retrieval penalty is a confound

`scripts/final_selection_simulator.py` and the final-slot package both encode:

> `H-hidden : … a candidate degrades by its MEASURED retrieval dependence = 0.080`
> `(= 6.643 overlap-OFF − 6.563 overlap-ON, i.e. 54968060 vs 54922806)`

**Those two kernels do not differ only in overlap.** `54922806` also carries `*1.3` on the GR sigma
(cell 29). The 0.080 is the *sum* of two stages, and against the pristine baseline they separate:

| stage | contrast | effect (− = better) |
|---|---|---|
| **overlap / retrieval** | `54968060` 6.643 vs pristine 6.6735 | **−0.031** (turning overlap **OFF** slightly *helps*) |
| **GR sigma ×1.3** | `54922806` 6.563 vs pristine 6.6735 | **−0.1105** |

and indeed −0.1105 − (−0.031) = −0.080, reproducing the recorded number as a **difference of two
different stages** rather than a retrieval term.

**So the retrieval/overlap stage is not worth 0.080 — it is worth about −0.03, and in the direction that
removing it slightly helps.** `54922806`'s advantage comes from the GR-sigma multiplier, which is **not**
a train-duplicate lookup and therefore **does not go inert on novel wells**.

### What this does to the H-hidden model

The simulator assumes overlap-ON candidates lose 0.080 under H-hidden, which is what made `54922806`
degrade exactly onto `54968060`'s 6.643 and produced the "9 pairs tie / diversity is free" structure. On
the corrected decomposition that convergence does not happen: `54922806` keeps its GR-sigma edge under
H-hidden and stays ahead of `54968060`.

**Consequence: the our-account-first pair is probably no longer free.** Q18 priced it at +0.000 worst /
+0.040 mean *because of* the assumed tie. Corrected, the cost is closer to the GR-sigma term.

**The counterweight, which matters just as much:** Q36 measured this very multiplier on 760 wells with
truth and found it helps only **42.1%** of wells with a **negative** median per-well gain. So the stage
carrying `54922806`'s public advantage is precisely the one our own held-out evidence says does **not**
transfer broadly. The public edge is real on 3 wells; its novel-well value remains unsupported.

I am **not** unilaterally rewriting the recommendation on this. It is queued (§6) as a simulator change,
because it moves a load-bearing input and the owner should see the re-run rather than a narrative.

## 4. Stage matrix

Contrasts are against the pristine baseline (6.6735) unless stated. "resolvable?" compares the effect to
the **0.009** same-code spread from §2 and, in brackets, to the older recorded **~0.115** config-variance
floor — the two disagree and that is flagged, not hidden.

| stage | evidence | effect on public | classification |
|---|---|---|---|
| **GR sigma ×1.3** | `54922806` vs pristine | **−0.1105** | **supported benefit on public** (12× the 0.009 spread; ~1× the 0.115 floor). **Novel-well transfer unsupported** — Q36: helps 42.1% of wells, negative median |
| **bimodal hedge** | `55064411` hedge-OFF 6.695 vs `54968060` 6.643 | **+0.052 when removed** → hedge helps public | **supported benefit on public [confounded by which floor applies]**. 5.8× the 0.009 spread but inside 0.115. **Measured harm locally**: Q14 — applies +2.0 ft to a well whose residual was already −0.19 |
| **post-SP45 stages, jointly** | `54990075` SP45-only 6.690 vs `54968060` 6.643 | **+0.047 when truncated** → the stages help | **supported benefit, but joint** over learned-traj blend + prefix calibration + model-package + hedge |
| **overlap / retrieval** | `54968060` vs pristine | **−0.031** (OFF is better) | **not load-bearing**, and of uncertain sign at 3.4× the 0.009 spread. **Supersedes the 0.080 figure** |
| **learned trajectory blend** | inside the 0.047 joint bound (G1.3: `fleongg`, weight 0.40) | ≤ 0.047, unseparated | **unknown** — cannot be isolated without a run |
| **prefix calibration** | G1.3 run log: applied `alpha = 0.0` | **0** | **measured inert** in the observed run |
| **model-package fallback** | G1.3: guard-rejected at runtime (`p95 diff 29.464 > 25.000`, `selected_for_submission_csv = False`) | **0** | **measured inert** — the dataset loads but contributes nothing |

Two of the seven stages are **measured inert**, one is **not load-bearing**, two are **supported on public
but contradicted or unsupported on truth**, one is **joint/unseparated**, and one is **unknown**.

## 5. Stage changes proposed — none require a submission

Against Q33's threshold (a slot is worth spending only if the expected public effect exceeds the floor)
and the fact that **zero slots are required** for the final pair:

- **GR sigma ×1.3 — already banked.** `54922806` *is* this variant, and it is our slot-1 candidate. Any
  new run would be a near-duplicate, which the submit gate forbids. **No action.**
- **bimodal hedge — leave as is.** Removing it costs +0.052 on public and Q14 says it is locally harmful;
  the two point opposite ways and `55064411` already bought that information. **No further slot.**
- **overlap — no action.** Its effect is ~0.03 and of uncertain sign; both settings are already submitted.
- **learned-trajectory blend — the only genuinely unknown stage**, bounded at ≤0.047 jointly. Isolating it
  would cost a GPU run plus a slot to measure something bounded **below** even the optimistic 0.009-based
  resolution threshold's practical relevance, and well below Q33's bar. **Not proposed.**
- **prefix calibration, model-package — inert.** Nothing to change.

**Net: no stage change clears the information-value threshold. No submission, as the task requires.**

## 6. Queue item appended — simulator correction, zero cost

The one genuinely load-bearing action from this round needs no run at all:

> **`q53_simulator_retrieval_penalty_correction`** — `scripts/final_selection_simulator.py` encodes
> `retrieval = 0.080` for overlap-ON candidates, derived from `54968060` vs `54922806`. Q39 showed those
> kernels differ in **two** stages, and decomposed against the pristine baseline the overlap term is
> **−0.031**, not +0.080. Re-run the four views with `retrieval ≈ 0.03` (and a sensitivity arm at 0.0),
> keeping `54922806`'s GR-sigma edge **non-inert** under H-hidden since it is not a retrieval mechanism.
> Report whether the recommended pair, the tie structure, and the price of our-account-first change.
> Carry Q36's counterweight explicitly: the GR-sigma stage helps only 42.1% of wells on truth.
> `can_submit=false`, no GPU, no smoke needed — it is arithmetic over recorded scores.

## 7. Limits

- All contrasts are **single public runs on 3 wells**, except the one replicate pair. The 0.009 spread is
  **two runs**, not a distribution, and it disagrees with the recorded ~0.115 floor; §4 reports against
  both rather than picking one.
- `54896975` and `54923144` differ in two attached datasets. They are code-identical and G1.3 classified
  those datasets vestigial, but "vestigial" was established by source/log inspection, not by an ablation.
- Effects are assumed additive when decomposing the 0.080. The arithmetic is exact by construction, but
  stage interactions are not measurable from these six runs.
- Kernels were pulled at their **current** version; Q38 §7 records the open confirmation that this equals
  the submitted `scriptVersionId`.
- Public effects say nothing directly about novel wells — Q18's reversal measurement stands.

## 8. Next

`q53_simulator_retrieval_penalty_correction` (queued below). Otherwise the queue remains empty until
`q29_final_slot_candidate_packager` reactivates on **2026-08-03**; the selection action is due by
**2026-08-04** and costs no quota.
