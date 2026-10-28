# Q18 — final-pair stress test: the gap that decides slot 1 is not resolvable at 3-well scale

Date: 2026-07-29
Task: `q18_public_leaderboard_family_stress` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Script: `scripts/q18_final_pair_stress.py`
Log: `reports/logs/q18_final_pair_stress_2026-07-29.log`
Outcome: **decision task completed. No submission (the task forbids one). Quota untouched at 0/5.**

## 1. Headline

The recommended pair is **unchanged**, but the *reason* changes materially. Slot 1 currently rests on
`54922806` (6.563) beating `54968060` (6.643) by **0.080**. That gap is now measured to be
**uninformative at the scale the competition actually scores**: on random 3-well draws, candidate pairs
whose pooled gap is ≤ 0.30 reverse their ranking **44.8%** of the time — a coin flip.

Consequently score-first does not really distinguish the two slot-1 options, and the **our-account-first**
pair costs **+0.000 worst case / +0.040 mean** — inside the ~0.115 config-variance floor.

## 2. What changed since the 2026-07-26 package

- **No Q10–Q17 candidate enters the board.** Q10 (DP 12.170, ~37% worse than the deployed line), Q11
  (rankers reliably negative), Q12/Q13 (closed), Q16 (closed on prerequisite), Q17 (HOLD, emission lever
  closed by measurement) produced **no submittable candidate**. Q15 is still not started.
- **One contingent entrant:** `55064411` (Q14 frontier hedge-OFF, our account) — still **PENDING** with no
  public score after ~5.8 h. It is swept parametrically below rather than given an assumed value.
- **No new private-score visibility.** Every submission's `privateScore` remains empty. Confirmed live.
- **A fourth view is added — our-account-first.** Ownership is distinct from provenance: `54968060` is our
  account but *public-derived*, so provenance-first does not select it while our-account-first does.

## 3. Board and pair evaluation

```
candidate                       public   H-vis   H-hid   mixed  family    account   prov
54922806_frontier_overlapON      6.563   6.563   6.643   6.603  frontier  teammate  public-derived
54968060_frontier_overlapOFF     6.643   6.643   6.643   6.643  frontier  ours      public-derived
54896975_frontier_overlapON      6.669   6.669   6.749   6.709  frontier  teammate  public-derived
54923144_frontier_gr_sigma       6.678   6.678   6.758   6.718  frontier  teammate  public-derived
54990075_frontier_sp45only       6.690   6.690   6.690   6.690  frontier  ours      public-derived
54844628_honest                  7.891   7.891   7.891   7.891  honest    ours      fully owned
```

```
pair                          H-vis  H-hid  WORST   mean  famDiv   OOF   ours
54844628 + 54922806           6.563  6.643  6.643  6.603     1.0  True  False
54896975 + 54922806           6.563  6.643  6.643  6.603     0.0 False  False
54922806 + 54923144           6.563  6.643  6.643  6.603     0.0 False  False
54922806 + 54968060           6.563  6.643  6.643  6.603     0.0 False  False
54922806 + 54990075           6.563  6.643  6.643  6.603     0.0 False  False
54844628 + 54968060           6.643  6.643  6.643  6.643     1.0  True   True
```

## 4. The four views — concise recommendation table

| view | pair | worst | mean | famDiv | note |
|---|---|---|---|---|---|
| **score-first** | `54922806` + `54844628` | 6.643 | 6.603 | 1 | 5 pairs tie on worst case |
| **diversity-first** | `54922806` + `54844628` | 6.643 | 6.603 | 1 | only tied pair with famDiv 1 |
| **provenance-first** | `54922806` + `54844628` | 6.643 | 6.603 | 1 | `54844628` is the only fully-owned + OOF candidate |
| **our-account-first** | `54968060` + `54844628` | 6.643 | 6.643 | 1 | **price: +0.000 worst, +0.040 mean** |

**Three of four views converge on `54922806` + `54844628`**, as before. The fourth differs only in slot 1
and is free on worst case.

## 5. The degradation stress Q18 asks for

How far must `54922806` degrade (beyond the modelled retrieval penalty) before it loses slot 1?

| rival | H-visible | H-hidden |
|---|---|---|
| `54968060` | **0.080** | **0.000** |
| `54844628` | 1.328 | 1.248 |

Under **H-hidden the threshold against `54968060` is already zero** — the two are exactly tied at 6.643,
because that hypothesis makes the overlap contribution inert and 6.643 *is* the measured overlap-OFF
level. Slot 1's advantage exists only under H-visible, and there it is 0.080.

## 6. The load-bearing new measurement — is 0.080 resolvable on 3 wells?

The competition scores **3 wells**. N4 measured that the scored quantity spans 3.49–15.14 across random
3-well draws for a *fixed* model, but that spread is **common-mode** and cancels in a ranking. What does
not cancel is the **candidate × draw interaction**: two candidates can swap order on a different 3-well
subset. That is measurable locally — 9 candidate prediction columns with truth over 760 wells / 3.72M rows
— so it was measured rather than assumed. For every pair: pooled RMSE gap vs the probability that a random
3-well draw reverses the pooled ranking (20,000 draws each).

```
pair                                   pooled gap    P(reversed)
s_54878409 vs s_a20_w25                    0.0035          47.2%
s_a20_w25  vs s_k96_aniso                  0.0243          49.8%
s_54878409 vs s_k96_aniso                  0.0278          46.4%
base       vs base_k96                     0.0432          46.8%
s_k96_aniso vs topk96_l75                  0.1477          44.2%
s_54844628 vs s_54878409                   0.1802          42.2%
s_54844628 vs topk96_l75                   0.3556          41.4%
base       vs s_54844628                   0.4360          37.4%
dwt        vs base                         0.9904          33.2%
dwt        vs s_54844628                   1.4264          29.1%
pf         vs base                         1.7576          26.4%
pf         vs topk96_l75                   2.5493          30.8%
```

| pooled gap band | mean P(reversed) | n |
|---|---|---|
| ≤ 0.30 | **44.8%** | 10 |
| ≥ 1.00 | **28.3%** | 13 |

**Reading the two decisive gaps against this scale:**

- **Slot-1 gap 0.080.** Nearest measured pairs (0.024, 0.028, 0.043) reverse **46–50%** of the time. A
  0.080 public advantage carries essentially **no information** about which candidate is better on a
  different 3-well draw. *Score-first does not actually distinguish `54922806` from `54968060`.*
- **Frontier-vs-honest gap 1.328.** Nearest measured pair (1.426) reverses **29.1%**; the ≥1.00 band
  averages 28.3%. So the honest line beats the frontier line on roughly **3 in 10** random 3-well draws.
  The slot-2 insurance is not a remote contingency — it is a ~29% event.

This is a considerably firmer basis for diversity-first than the package previously had, which argued the
insurance was "free" on worst case but could not say how often it pays.

Note the relationship decreases but is **not monotone** at the top (gap 2.55 → 30.8% vs gap 1.78 → 24.0%),
because heavy-tailed candidates like `pf` reverse more often than their pooled gap suggests. The bands
above are therefore reported as bands, not as a fitted curve.

## 7. Contingent entrant `55064411`

| if public | consequence for slot 1 |
|---|---|
| < 6.563 | becomes best public overall → takes slot 1 on **all four views** |
| 6.563 – 6.643 | best **our-account** frontier → takes slot 1 on our-account-first only |
| ≥ 6.643 | no change (worse than `54968060`, our existing our-account frontier) |

Given §6, the middle band should be read with care: a `55064411` landing at, say, 6.60 would be inside the
same coin-flip region as the 0.080 gap, so it would not constitute score evidence for displacing
`54922806` — only ownership evidence.

## 8. Assumptions updated, as Q18 step 2 requires

| assumption | status |
|---|---|
| family correlation | unchanged — locally measured pred-corr ≥ 0.99996 within the honest/frontier local set; family diversity stays a 0/1 term, since correlation is unavailable for teammate outputs and a missing value must be neutral, not worst-case |
| provenance risk | narrowed by the G1.3 audit: **one** prediction-affecting third-party dataset (`fleongg/rogii-claude-models-pub`), worth ≈0.047 as a **joint** bound with the bimodal hedge |
| OOF support | `54844628` remains the only 760-well nested-OOF + bootstrap candidate |
| public→private transfer (N4) | OOF on the 3 test wells 4.756 vs public 7.891 = **1.659×**; OOF-derived bounds are not leaderboard bounds. **Extended by §6:** not only the level but the *ranking* is unstable at 3-well scale |
| private score visibility | **none** — `privateScore` empty for every submission; never used |

## 9. Verdict

- **Default recommendation unchanged: `54922806` + `54844628`** (score-first, diversity-first,
  provenance-first).
- **`54968060` + `54844628` is a fully defensible alternative** at +0.000 worst case and +0.040 mean, and
  §6 shows the 0.080 that separates them is not resolvable at the scoring scale. Choosing between these
  two pairs is therefore an **ownership judgment for the project owner, not a question score evidence can
  settle**. Recorded as such rather than decided unilaterally.
- **Slot 2 is settled on much firmer ground than before:** `54844628` supplies family-independent
  insurance that pays on ~29% of 3-well draws, at zero modelled worst-case cost.
- No Q10–Q17 candidate changes the pair. `55064411` may, once scored, and only per §7.

## 10. Limits, stated plainly

- The reversal probabilities are measured on **honest-family local candidates**, because the frontier
  candidates have no per-well truth — they are scored only on the 3 hidden wells. The transfer argument
  is that 3-well sampling noise is a property of the *well population*, not of a particular pipeline, and
  one measured member (`s_54844628`) is an actual pair member. Frontier-family per-well structure could
  differ, and that is not measurable with what is in hand.
- Draws sample wells **with replacement**; with 760 wells the collision rate over 3 draws is ~0.4%, which
  is negligible but not zero.
- The 760 local wells are train wells, not the 3 hidden test wells. This measures the *scale* of 3-well
  ranking instability, not the specific instability of the actual test draw.
- H-visible / H-hidden / mixed remain hypotheses, not knowledge. The private split is not visible.

## 11. Next

`q19_external_solution_refresh`. `q15_frontier_dependency_replacement` remains blocked — it needs its own
frontier full run and `55064411`'s kernel re-run is still in flight.
