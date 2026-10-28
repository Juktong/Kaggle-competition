---
id: q57_dip_state_augmented_dp
priority: 628
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q57 Dip-State-Augmented DP (state = (TVT, dip) instead of TVT alone)

Source: Q45's architecture scan found `tiktoktrendz/rogii-dip-aware-hmm-gbm` — not the Kaiwalya family,
Numba forward-backward HMM whose transition searches **41 dip rates with a momentum factor**, i.e. its state
is effectively **(TVT, dip)**.

**Why this is not a repeat of anything closed.** Every transition arm this project has run operated on a
TVT-only state:

- Q40 — 45 soft per-step penalties on `|Δstate|` (L1, L2, Huber, drift, curvature); deployed L1 won;
- N1 — per-step admissible interval derived from well geometry; negative, binds 83–97% of transitions;
- Q54 — global cumulative corridor `|state_j − anchor| ≤ C`; corridor and penalty measured as substitutes;
- Q55 — decoder side (beam average, soft-min / forward-backward); closed, and it found the DP **objective**
  is misaligned with RMSE.

Augmenting the state with a dip/velocity dimension makes **dip continuity a property of the state rather
than a penalty on the increment**. That changes the objective's shape instead of tuning its coefficients,
which is the one direction Q55's closure left open.

Required execution:

1. Reuse the Q10/Q40/Q54 harness (`scripts/q10_twh1_scorer_dp.py`, same split seed, ≥ 40 eval wells,
   splits BY WELL). Validate on **DP OUTPUT only** — never a pointwise emission metric (Q17's rule).
2. Extend the DP state to `(s, d)` where `d` indexes a dip-rate grid. Transition: `s_{j+1} ≈ s_j + d`, with
   a penalty on **changing** `d` (dip continuity) rather than on `|Δs|`. Keep the existing emission
   untouched.
3. **Cost control is mandatory**: the state space multiplies by the dip-grid size. Start with 9–13 dip
   values and the existing beam; measure wall-time on ≤ 8 wells before the full grid. If the full sweep
   would exceed ~40 min, reduce the λ grid, not the well count.
4. **Two controls, both from prior rounds' mistakes:**
   - **degeneracy** — a single-element dip grid `{0}` with the dip-change penalty at 0 must reproduce the
     current `run_dp` output (Q54's control);
   - **binding/activation** — report how often the selected dip actually differs from 0 and from the
     previous step's dip. N1 and Q54 both first produced an inert constraint and nearly reported it as "no
     effect"; an inert arm must be visible as inert, not silent.
5. Sweep the dip grid width and the dip-change penalty jointly, chosen **NESTED** (select on one half of the
   eval wells, score on the disjoint half, both ways).
6. GATE: nested gain over the `l1 lam=60` baseline (**12.170** pooled) > 0 AND helps > 50% of wells AND
   3-well bootstrap 5th > 0.
7. Do not submit.

**Carry into the report:** this line sits at ~12.2 against the deployed honest line's 8.8626, so passing
makes the state-augmentation lever worth pursuing; it does **not** make the artifact submittable. Q41 showed
the 3-well 5th condition is maximised by changing nothing, so expect that condition to fail — the
informative outputs are the nested gain, the per-well win rate, and the activation diagnostic.

**Also record, because Q55 is directly relevant:** if state augmentation lowers the objective's cost but not
RMSE, that is Q55's misalignment finding reappearing, and it should be reported as such rather than as a
tuning failure. Report the accumulated-pull diagnostic (Q40) for any directional dip term.

Expected cost: ~20–40 min. Write `reports/q57_dip_state_augmented_dp_<date>.md`.
