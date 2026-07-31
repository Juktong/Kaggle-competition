# Q58 — carrying the PF smoother to the deployed honest line: the stage is now exactly reproduced, and the end-to-end run is in flight

Date: 2026-07-29 23:50 UTC
Task: `q58_honest_kernel_backward_smoothing` (`requires_gpu=false`, `can_submit=true`, `max_submit_cost=1`)
Scripts: `scripts/q58_smoothed_pf_produce.py` (producer), `scripts/q58_struct_refit.py` (evaluator)
Logs: `reports/logs/q58_pf_produce_2026-07-30.log`
Outcome: **the deployed honest line is now reproduced exactly from saved arrays (§2); the NS=64 row-level PF
run is in flight, ETA ~02:50 UTC. No submission yet — the decision needs the end-to-end number. Quota 0/5.**

## 1. The structural-field stage does not depend on the PF — which changes what "re-fit" means

The task's premise was that the structural-field stage "was fitted against the forward PF" and might absorb,
keep or destroy the smoother's gain. Reading `scripts/struct_oof_produce.py` rather than assuming, the stage
is:

```
group   = round(max(typewell.TVT), 1)                 # the target's OWN typewell -> test-available
field   = IDW(k=12, w=1/(d+1)) over same-group train wells with median XY separation >= 150 ft
anchor  = mean(r_true - r_pred) over the target's OWN last 100 known heel rows
struct  = r_pred + anchor - Z
```

**None of that reads the PF.** `struct` is an external per-row prediction column, already computed for all
3,721,471 rows and stored in `struct_oof.npz`. The deployed line then combines it with the blend by a fixed
convex weight on gated rows:

```
final = (1 - W) * base + W * struct    where the gate holds
final = base                           elsewhere
```

So the only things "fitted against the forward PF" are **W and the gate threshold**. Re-fitting the stage
against a smoothed PF therefore means re-choosing those two — arithmetic over saved arrays, with no PF
re-run. That is why this round splits into a slow producer (row-level PF predictions) and a fast evaluator,
so the re-fit can be iterated without repeating a 3-hour filter run.

## 2. Reproduction control — and the gate source was not what the aligned frame implied

Nothing about a modified line is trustworthy until the *unmodified* one can be rebuilt from the same arrays,
so that is step 0 and it gates the rest of the script.

The first attempt used the aligned frame's own per-row `nnb` / `closest_surv` columns and **did not**
reproduce: 2139 rows wrong (0.057%), max |diff| 4.59 ft, pooled RMSE 8.8634 against the deployed 8.8626.
The residual was concentrated in **6 wells of 760** — `8b95d6d1` alone accounted for 1731 rows. That well
has `closest_surv = 1011.1` in the aligned frame, i.e. just *outside* a `< 1000` gate, yet the deployed line
had gated it **in**.

The gate is built from `struct_oof.npz`'s **own per-well meta** (`meta_nnb`, `meta_closest`), which differs
from the aligned frame's per-row columns for those boundary wells. With the meta gate:

```
deployed s_54844628 RMSE                                   8.8626   (ledger: 8.8626)
base (0.5*dwt + 0.5*pf) RMSE                               9.2987   (ledger: 9.2987)
rebuilt (meta gate nnb>=4 & closest<1000, W=0.15) RMSE     8.8626
rows differing by >0.01: 9 of 3,721,471 | max |diff| 0.0182    -> float32 rounding
gated rows: 87.3%                                          (ledger: 87%)
```

The weight was **recovered from the deployed column itself** rather than taken from the ledger, which is a
stronger check than matching a documented constant:

```
implied W = (deployed - base) / (struct - base)
  on gated rows : median 0.1500   p5 0.1497   p95 0.1503
  off-gate      : median 0.0000
```

**The stage is now fully characterised by (meta gate, W = 0.15)**, so substituting a smoothed PF into it is
a clean one-factor change. This also corrects a latent trap for any future round: the aligned frame's
`nnb`/`closest_surv` columns are *not* the deployed gate and silently disagree on 6 wells.

## 3. What the producer is computing, and why NS=64

Q56 saved only per-well SSE, so it cannot support a re-fit; the missing artifact is the row-level PF
prediction. The producer emits `pf_fwd` and `pf_sm` per toe row, aligned to `aligned_preds.npz` by
(well, ridx) with the same `ridx`-equality and truth-equality assertions Q36/Q56 use.

**NS = 64, the deployed configuration.** Q36 and Q56 both ran NS=32 to bound wall-time and both had to carry
a caveat about it. Beyond removing that caveat, NS=64 buys a second control for free: the stored `pf` column
in `aligned_preds.npz` *is* the deployed NS=64 forward PF, so `pf_fwd` can be checked directly against it.
The evaluator prints that comparison (§1 of its output) before using anything.

The smoother, the trellis twin and its byte-for-byte degeneracy check are **imported unchanged** from
`scripts/q56_pf_backward_smoothing.py` rather than re-implemented, and the producer re-runs the degeneracy
assertion itself so the artifact carries its own proof:

```
degeneracy control: array_equal(deployed run_particle_filter, trellis twin) = True
```

Producer smoke (Directive 4): 6 wells, NS=4, 0.1 min, 6/6 usable, 27,945 rows written. Full run launched at
NS=64 over 760 wells; measured rate 14 wells / 3.5 min → **ETA ~3.2 h**.

## 4. What the evaluator will decide

Once the producer lands:

- **α chosen NESTED over `{0, 0.25, 0.5, 0.75, 1.0}` jointly with W over `{0, 0.05, 0.10, 0.15, 0.20, 0.30}`**,
  splits by well, both directions. Q56 selected α=1.0 on the same data it scored, so it is re-chosen here.
- the comparison baseline is the **deployed line itself** (`s_54844628`, 8.8626), not the blend;
- per-well win rate and the 3-well bootstrap are reported, as in every prior round;
- a carry-through figure: the smoother's blend-level gain versus what survives the unchanged stage, which is
  the quantity the task asks about.

## 5. Submission position, stated before the number is known

`max_submit_cost=1`, so a submission is permitted but not assumed, and the standing submit gate applies in
full. Recorded now so the decision is not rationalised afterwards:

- **A submission is justified only if the end-to-end line beats 8.8626 by a margin that survives nesting**,
  and if the resulting output is materially different from `54844628` (the gate forbids near-duplicates).
- The **3-well bootstrap 5th was negative at blend level** (−0.3238, P(>0) 0.7919). Q41 showed that
  condition is maximised by changing nothing and Q44 measured the 3-well draw's difference-sd at 2.40 ft, so
  it constrains what a *public* score can resolve rather than novel-well quality. It is a reason to expect a
  noisy public reading, **not** a reason to discount a clean OOF gain.
- Q44 measured slot 2 — the honest line — as the **largest positive term in the final-pair decision**
  (~0.46 ft mean, ~0.94 ft tail, as the decorrelated member of a best-of-2, and the only submission we hold
  whose error is decorrelated from the crowd). Improving it improves the slot the project actually relies
  on. That is the strongest argument for spending one of five idle daily slots, and it will be stated
  explicitly in the submission description if a submission is made.
- Against that: a Kaggle submission would need the smoother reproduced inside the honest kernel. The test
  set is 3 wells / 14,151 rows against the 760 train wells measured here, so runtime is not a constraint.

## 6. Limits

- **No end-to-end number yet.** §2 is a control, not a result; §5 is a pre-registration, not a decision.
- The producer runs the PF on **train** wells to build an OOF proxy, as every prior honest-line round has.
- `struct` is reused unchanged from `struct_oof.npz`. Its own construction (IDW over same-group train wells)
  is independent of the PF, so it does not need recomputing — but it was produced once, in July, and is
  taken as given here rather than re-derived.
- The re-fit sweeps W and α. The gate threshold itself (`nnb>=4`, `closest<1000`) is held at the deployed
  values; re-choosing it as well would widen the selection space against a fixed eval set, and Q41's
  evidence is that such widening does not survive the 3-well condition.

## 7. Next

Collect `reports/logs/q58_pf_produce_2026-07-30.log`, run `scripts/q58_struct_refit.py`, apply the §5
position, and either submit with the stated justification or record why not.
`q46_submission_asset_inventory` is next by priority. `q29_final_slot_candidate_packager` reactivates
**2026-08-03**; the final selection is due **2026-08-04** and costs no quota.
