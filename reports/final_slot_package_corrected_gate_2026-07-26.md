# Final-slot package — 2026-07-26 (rewritten; supersedes all earlier versions)

Deadline **2026-08-05 23:59 UTC**. Final score = **best of the 2 selected submissions** on the private
set, so the object being chosen is a **pair**, not two independent picks.

This version replaces the earlier text, which contained a contradiction: the top recommended
`54844628` for slot 2 while a later section still recommended `54968060` unless provenance was weighted.
The three criteria are now separated explicitly and each is stated in full.

## Board (live 2026-07-26 15:09 UTC)

| ref | public | side | family | provenance | OOF |
|---|---|---|---|---|---|
| `54922806` | **6.563** | teammate | frontier (overlap-ON) | public-derived | no |
| `54968060` | 6.643 | ours | frontier (overlap-OFF, validated no-retrieval) | public-derived | no |
| `54896975` | 6.669 | teammate | frontier (overlap-ON) | public-derived | no |
| `54923144` | 6.678 | teammate | frontier (GR-sigma) | public-derived | no |
| `54990075` | 6.690 | ours | frontier (SP45-only) | public-derived | no |
| `54844628` | 7.891 | ours | **honest** (DWT+PF+structural field) | **fully owned** | **yes** |
| `54878409` | 7.953 | ours | honest variant | fully owned | yes — excluded (regression) |

## The three recommendations

Produced by `scripts/final_selection_simulator.py` (pair-level best-of-2 under H-visible / H-hidden /
mixed; retrieval penalty = the **measured** 0.080 = 6.643 − 6.563).

### score-first → `54922806` (6.563) + `54844628` (7.891)
Minimise the modelled private score, ignoring lineage. Worst case **6.643**, mean **6.603** — the best
available. Note that **9 pairs tie** within 0.01 of this worst case, because under H-hidden `54922806`
degrades exactly to 6.643, which is the level of every no-retrieval candidate. Score alone therefore
does **not** pick a unique pair.

### diversity-first → `54922806` (6.563) + `54844628` (7.891)
Among the score-tied pairs, prefer members that fail independently. Every frontier+frontier pair has
family diversity 0 — a family-wide problem in the frontier stack (third-party artifacts, or a
visible-well-specific fit beyond the measured overlap term) would remove **both** slots at once. Pairing
the frontier with the honest line gives family diversity 1 at **the same worst case (6.643)**, so the
insurance is free. Among the diverse pairs, `54922806` has the better mean (6.603 vs 6.643).

### provenance-first → `54922806` (6.563) + `54844628` (7.891)
Require at least one slot to be a fully-owned, OOF-validated pipeline. `54844628` is the only candidate
meeting that bar (760-well nested OOF + bootstrap, every component built and audited in this repo).
Among pairs containing it, the best worst case is again with `54922806`.

## Consolidated recommendation

**All three criteria converge on `54922806` + `54844628`.** There is no criterion under which a second
frontier candidate improves the pair: slot 1 already represents the frontier line, so adding
`54968060` / `54990075` / `54896975` / `54923144` as slot 2 is redundant (family diversity 0, identical
worst case), while `54844628` supplies independent-failure insurance at no modelled cost.

## Where the other candidates stand

- `54968060` (6.643) — fully validated no-retrieval frontier run, and the natural **replacement for
  slot 1** if an our-account frontier representative is ever preferred over the teammate branch. It is
  redundant as a *second* slot.
- `54990075` (6.690) — SP45-only. Its result **settled an open question** (below), but it is neither the
  best frontier variant nor diverse, so it is not a slot candidate.
- `54878409` (7.953) — excluded, measured regression.

## What `54990075` = 6.690 settled

Pre-registered reading (2026-07-26 round 2): `< 6.643` → post-SP45 stages are net-negative;
`6.643–6.678` → neutral; `> 6.678` → the stages earn their place. **Result 6.690 → the last branch.**

The frontier's post-SP45 stages (learned-trajectory blend, prefix calibration, model-package correction,
bimodal hedge) **do** contribute on the leaderboard, and the local proxy that favoured SP45-only
(2.703 vs 3.259 vs train-copy TVT) pointed the **wrong way**. This is a direct, independent confirmation
of the G1.2 §3 saturation finding: proximity to train-copy TVT is a weak and sometimes misleading signal.
Practical consequence for the pipeline: **a proxy-only preference is not sufficient evidence to re-rank
candidates** — it must be paired with either a large effect or a structural argument.

## Sensitivity

The only input that could move this is the retrieval penalty (measured 0.080). If the true H-hidden
degradation of overlap-ON branches were much larger, `54922806` would fall behind `54844628` under
H-hidden and the pair's worst case would be set by the honest slot — which strengthens, not weakens, the
case for keeping `54844628` in slot 2. The recommendation is stable across the plausible range.

## Provenance reservation — narrowed by the G1.3 audit (2026-07-28)

Earlier wording described the frontier line as depending on "9 third-party public datasets". Measured
against source and run logs (`reports/frontier_dependency_provenance_audit_2026-07-28.md`):

> Frontier candidates depend on **one** third-party public dataset that is not already part of our own
> stack — `fleongg/rogii-claude-models-pub` (learned-trajectory model, blend weight 0.40), whose measured
> public value is **≈0.047** (`54990075` SP45-only 6.690 vs `54968060` 6.643), i.e. inside the
> ~0.115 config-variance floor. Of the rest: `ravaghi/…artifacts` is **shared with our own honest line**,
> `koolbox-offline` supplies offline pip wheels only, `pilkwang/rogii-model-package` was
> **guard-rejected at runtime** (`p95 diff 29.464 > 25.000`, `selected_for_submission_csv = False`), and
> five datasets are **vestigial** (zero source references, zero log appearances).

**Amended same day (variant-matrix round).** The ≈0.047 above was derived on the assumption that the
other post-SP45 stages were inert. That assumption was wrong: the **PF bimodal branch hedge applies
+2.0 ft to all 4,301 rows of `00e12e8b`** (`reports/frontier_variant_matrix_lite_2026-07-28.md`). So
`54990075` and `54968060` differ across **two** active stages, and ≈0.047 is a **joint upper bound** for
the learned-trajectory blend *and* the bimodal hedge — the `fleongg` dataset's own share can only be
smaller. The dependency count (one prediction-affecting third-party dataset) is unaffected.

**The slot recommendation is unchanged** — all three criteria still converge on
`54922806 + 54844628`. What changes is the *argument*: the frontier's dependency exposure is a single
quantified dataset worth ≈0.047, not a nine-dataset surface. Provenance-first still prefers `54844628`
in slot 2, but on the grounds that it is the only fully-owned, 760-well-OOF-validated candidate — a
different property from dependency count.

## Sensitivity addendum — the scored scale's own variance (N4, 2026-07-28)

`reports/n4_conformal_well_uncertainty_2026-07-28.md` measured, for the deployed honest line held FIXED,
the pooled row-weighted RMSE of a random 3-well draw:

```
5th 3.491   25th 5.040   median 6.708   75th 8.990   95th 15.138
```

The scored quantity itself spans more than 4x between its 5th and 95th percentiles for an unchanged model.
Two consequences for this package:

1. The public gaps that separate the frontier family from the honest line (6.563 vs 7.891, i.e. 1.33) are
   comfortably larger than the config-variance floor (~0.115) but are **not** large relative to 3-well
   draw variance. The *ranking* used here is still the best available evidence — it is measured on the
   same 3 wells for every candidate, so draw variance is common-mode and cancels — but no absolute
   private score should be inferred from it.
2. The recommendation is unchanged: `54922806` + `54844628` under score-first, diversity-first and
   provenance-first. Draw variance strengthens the diversity argument, since it raises the value of
   holding two members that fail independently.

Also measured: OOF on the 3 test wells 4.756 vs public 7.891 = **1.659x**. OOF-derived bounds are not
leaderboard bounds and must not be quoted as such in this package.

## Q18 stress test (2026-07-29) — the slot-1 gap is not resolvable at 3-well scale

`reports/q18_public_leaderboard_family_stress_2026-07-29.md`, `scripts/q18_final_pair_stress.py`.
**The recommended pair is unchanged. The reason for it changes materially.**

### A fourth view: our-account-first

Ownership is distinct from provenance — `54968060` is our account but *public-derived*, so
provenance-first does not select it while our-account-first does.

| view | pair | worst | mean | famDiv |
|---|---|---|---|---|
| score-first | `54922806` + `54844628` | 6.643 | 6.603 | 1 |
| diversity-first | `54922806` + `54844628` | 6.643 | 6.603 | 1 |
| provenance-first | `54922806` + `54844628` | 6.643 | 6.603 | 1 |
| **our-account-first** | `54968060` + `54844628` | 6.643 | 6.643 | 1 |

**Price of the our-account constraint: +0.000 worst case, +0.040 mean** — inside the ~0.115
config-variance floor.

### Degradation stress

How far must `54922806` degrade beyond the modelled retrieval penalty to lose slot 1?

| rival | H-visible | H-hidden |
|---|---|---|
| `54968060` | 0.080 | **0.000** |
| `54844628` | 1.328 | 1.248 |

Under H-hidden the threshold against `54968060` is already **zero** — both sit at 6.643, because that
hypothesis makes the overlap contribution inert and 6.643 IS the measured overlap-OFF level. Slot 1's
advantage exists only under H-visible, and there it is 0.080.

### The load-bearing measurement — is 0.080 resolvable on 3 wells?

N4 measured that the scored quantity spans 3.49..15.14 across random 3-well draws for a FIXED model, but
that spread is **common-mode and cancels in a ranking**. What does not cancel is the candidate x draw
INTERACTION. That was measured, not assumed: 9 local candidate prediction columns with truth over 760
wells / 3.72M rows, 20,000 random 3-well draws per pair, pooled gap vs P(the draw reverses the pooled
ranking).

| pooled gap band | mean P(reversed) | n |
|---|---|---|
| <= 0.30 | **44.8%** | 10 |
| >= 1.00 | **28.3%** | 13 |

- **Slot-1 gap 0.080** — nearest measured pairs (0.024, 0.028, 0.043) reverse **46-50%** of the time. A
  0.080 public advantage carries essentially NO information about which candidate is better on a
  different 3-well draw. **Score-first does not actually distinguish `54922806` from `54968060`.**
- **Frontier-vs-honest gap 1.328** — nearest measured pair (1.426) reverses **29.1%**. The honest line
  beats the frontier line on roughly **3 in 10** random 3-well draws. The slot-2 insurance is not a
  remote contingency; it is a ~29% event, which is a far firmer basis for diversity-first than
  "free on worst case".

### Consequence for the decision

- **Default unchanged: `54922806` + `54844628`.**
- **`54968060` + `54844628` is fully defensible** at +0.000 worst / +0.040 mean, and the 0.080 separating
  them is not resolvable at the scoring scale. Choosing between these two pairs is an **ownership
  judgment for the project owner, not something score evidence can settle** — recorded as such rather
  than decided unilaterally.
- **Slot 2 is now settled on firmer ground:** family-independent insurance that pays on ~29% of draws at
  zero modelled worst-case cost.

### Limits

Reversal probabilities are measured on honest-family local candidates, since frontier candidates have no
per-well truth (they are scored only on the 3 hidden wells). The transfer argument is that 3-well
sampling noise is a property of the well population rather than of a pipeline, and one measured member
(`s_54844628`) is an actual pair member. Draws sample with replacement (~0.4% collision over 3 draws).
The 760 local wells are train wells, so this measures the SCALE of 3-well ranking instability, not the
specific instability of the actual test draw.

### Live-refresh confirmations

No new private-score visibility (`privateScore` empty for every submission; never used). `55064411` still
PENDING (~5.8 h) and carried only as a parametric contingent entrant: below 6.563 it takes slot 1 on all
four views; between 6.563 and 6.643 it is the best our-account frontier and takes slot 1 on
our-account-first only — but that band sits inside the same coin-flip region, so it would be **ownership
evidence, not score evidence**. No Q10-Q17 candidate enters the board.
