# Submission record — anisotropic structural field (2026-07-21)

**Submission ref `54878409`** · kernel `joezzzzz/rogii-struct-aniso-codex` v1 · **public 7.953**
(deployed `54844628` = 7.891, lower is better) · commit at submission time recorded below.
First submission of this queue; 1 of 5 daily slots used. Submitted at commit `2f35be1`.

> **Outcome: the OOF gain did NOT confirm on public.** Public is **0.062 worse** while OOF predicted
> **+0.16 better**. See the post-mortem at the end of this report before using this in a final-2
> decision.

## What was submitted

The deployed honest pipeline with **one change**: the cross-well structural field's isotropic IDW is
replaced by a dip-aware anisotropic kernel.

```
base   = 0.5*DWT + 0.5*PF
output = base, with (1-W)*base + W*struct_aniso on gated rows
A      = 50      anisotropy: d^2 = (delta.u)^2 + (delta.v)^2 / A^2
                 u = dip direction from a plane fit over surviving group-mates; v = strike (perp)
W      = 0.25    fixed from nested train OOF, capped at 0.25 by prior stress evidence
gate   = nnb >= 4  AND  closest SURVIVING mate < 1000 ft
guard  = MIN_SEP 150 ft duplicate/near-twin guard (unchanged)
```

No new inputs: group key from the target's own typewell, anchor from the target's own known heel rows,
mates are TRAIN wells' `(X, Y, TVT+Z)`. `A = 1` reproduces the previously submitted field exactly.

## Why it was worth a slot

| check | result |
|---|---|
| pre-registered gate | **+0.10 with stably positive bootstrap — MET** |
| nested (A, W) honest gain | **+0.1606** (8.8626 → 8.7020) |
| fixed deployable config | +0.1802 (8.8626 → 8.6825) |
| bootstrap (1000 well-resamples) | mean **+0.1788**, 5th **+0.0490**, frac>0 **99%** |
| duplicate leakage | **cleared** — advantage over isotropic *grows* under stricter guards |
| kernel vs OOF producer | **bit-exact** (88,229 rows, max diff 0.00000000 ft) |
| smoke | PASS, no errors |
| pre-submit HARD checks | **PASS** (format, finite, range, diff-vs-baseline) |
| visible-well pooled RMSE | 3.677 → **3.496** (+0.181, independently matches the OOF estimate) |

This is the **first candidate of the queue to satisfy both gate conditions**. Directions 2, 3, 4, 6, 7
and the top-K line (K=24/48/96) were all held back — the top-K candidate reached a +0.1492 point
estimate but failed bootstrap stability, and was not submitted.

## Attribution — the gain is anisotropy, not the weight change

```
A=50 at unchanged W=0.15   +0.0483      anisotropy alone
A=1  with refitted W       -0.0890      re-weighting the isotropic field alone
A=50 with W=0.25           +0.1802      both
```

The same re-weighting that helps the anisotropic field **hurts** the isotropic one, so the larger weight
is earned rather than merely absorbed.

## The two audit findings that changed the submission

**1. Duplicate-leakage risk (investigated, cleared).** `A=50` divides strike distance by 50, so a mate
just past the 150 ft guard *along strike* has ≈3 ft effective distance. The guard was calibrated at
isotropic distance, so anisotropy could in principle re-admit near-twins. Two checks cleared it:

- weight origin: `A=50` draws *less* weight from close mates than isotropic (<400 ft: 46.6% vs 52.4%)
  and selects mates at *greater* median separation (375 vs 357 ft);
- isotropic control at matched guards: the advantage over `A=1` **grows** as the guard tightens —
  MIN_SEP 150/400/800 → **+0.168 / +0.850 / +2.111**. Leakage would vanish instead.

An intermediate comparison (A>1 at MIN_SEP 400/800 vs the *deployed* A=1 at 150) showed −0.375/−1.44 and
looked like a leakage collapse. It was not: ~50% of IDW weight comes from within 400 ft for **both**
fields, so tightening the guard is information loss, and it hits the isotropic kernel harder.

**2. Gate asymmetry (found by the smoke, fixed).** The smoke reported `closest = 0 ft` for all three
test wells. Cause: `closest` was `min(sep)` over **all** candidate mates *including* ones the guard
drops, so any test well with a train near-twin passed the `< 1000 ft` gate trivially — while in OOF,
self is excluded by name and `closest` is the nearest genuine mate. The inference gate was therefore
more permissive than the gate it was validated under, and that mattered more at W = 0.25 than at 0.15.

Fixed by gating on the **closest surviving mate** in both OOF and inference. Cost on train is
negligible (+0.1808 → +0.1802; only 2 of 657 wells change), and OOF/inference now agree by construction.
Post-fix smoke: `closest = 292 / 344 / 355 ft` with `closest_all = 0 ft` reported separately.

## Known weak subgroup — recorded, deliberately not guarded

On the 39 train wells (5.1%) whose closest *candidate* mate is a dropped near-twin, the candidate
**loses −0.4439** pooled (6.7170 → 7.1609), against +0.2628 on the 618 wells whose closest mate
survives.

No extra guard was added for them. That subgroup is only known to be harmful by inspecting validation
outcomes, so guarding it would be outcome-driven selection — the same error rejected in directions 2 and
4 and in the top-K line. It is recorded here as a known risk instead.

## Reproduction

```
kernel     : kaggle_kernel_struct_aniso/rogii-struct-aniso-codex.ipynb  (cell 27)
producer   : scripts/struct_aniso_produce.py
validation : scripts/eval_aniso_capped.py, scripts/eval_surv_gate.py
leakage    : scripts/eval_ctrl.py, scripts/weight_origin.py
equivalence: scripts/verify_kernel_equiv.py
audit      : scripts/presubmit_gate.py -> experiments/presubmit/L4_aniso_A50_W025_vs_deployed_presubmit.{json,md}
logs       : reports/logs/aniso_*.log
```

## Submission-mechanics note

`kaggle competitions submit -f submission.csv` returns **400 Bad Request** for this competition: it is
**kernels-only** (`is_kernels_submissions_only = True`). File submissions are rejected by design. The
working path is the code-submission API:

```python
api.competition_submit_code(file_name='submission.csv', message=..., 
                            competition='rogii-wellbore-geology-prediction',
                            kernel='joezzzzz/rogii-struct-aniso-codex', kernel_version=1)
```

Recorded because the CSV route silently looks like a candidate problem when it is a competition-type
constraint. Competition limits: `max_daily_submissions = 5`, deadline 2026-08-05 23:59.

## Post-mortem — local/public gap (required record)

| | OOF (760 wells, nested) | public |
|---|---|---|
| `54844628` deployed | 8.8626 | **7.891** |
| `54878409` anisotropic | 8.7020 (**+0.1606**) | **7.953** (**−0.062**) |

**The OOF gain did not transfer.** Recording the diagnosis rather than explaining it away:

**1. OOF predicted these very wells would improve.** The public test set is 3 wells, all visible
(duplicated in train). Their OOF per-well gains were **+0.287, +0.539, −0.019** (mean +0.269) — i.e. the
local evidence pointed the same way and still missed.

**2. Three wells cannot resolve an effect this size.** Resampling 3 wells from the 655 gated wells gives
a mean-gain spread of **5th −1.182 / 95th +1.443**, and **42.6%** of random 3-well draws are negative,
against a true mean per-well gain of +0.119. The public leaderboard for this competition is therefore a
very weak discriminator at the ±0.06 scale — it separated the earlier large steps (9.519 → 8.080 →
7.891) but cannot separate these two.

**3. The visible-well local check was weaker than it was treated as.** It compared against the *train*
copies of those wells (pooled RMSE 3.677 → 3.496, +0.181), but the test versions have a **different
heel/toe split**, so the anchor and the scored rows differ. That check should not have been presented as
an independent confirmation of the OOF number — it is a related but not equivalent quantity, which is
also why its absolute level (≈3.5) is nowhere near the public level (≈7.9).

**What this does and does not overturn.** It does not invalidate the OOF result (760 wells, nested
(A,W), bootstrap 5th +0.0490, 99% positive, leakage cleared, kernel bit-exact). It does show the gain is
unconfirmed on real held-out data, and that our only public signal is too small to confirm it either
way. Under a strategy that targets the private ranking on novel wells and treats OOF as the proxy, this
is a candidate with strong local evidence and no public corroboration.

## Final-2 implication — recommendation, not a decision

`54844628` (public 7.891, OOF 8.8626) remains the **primary honest slot**: it is the only candidate
verified on both axes.

`54878409` is the OOF-superior variant of the same pipeline, differing only in the structural kernel.
Because final selection is best-of-2, using it as the **second** slot is a reasonable hedge — the two are
highly correlated and the choice is essentially "isotropic vs dip-aware structural field". But this is a
final-selection decision with a hard deadline, so it is left as a recommendation for the project owner
rather than actioned here.

No decisions were made around any teammate/external submission.
