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

**The slot recommendation is unchanged** — all three criteria still converge on
`54922806 + 54844628`. What changes is the *argument*: the frontier's dependency exposure is a single
quantified dataset worth ≈0.047, not a nine-dataset surface. Provenance-first still prefers `54844628`
in slot 2, but on the grounds that it is the only fully-owned, 760-well-OOF-validated candidate — a
different property from dependency count.

