# Q49 — transition-prior smoke: Q43's highest-value idea was already fully executed by Q54

Date: 2026-07-31 13:00 UTC

Task: `q49_transition_prior_smoke_from_research` (`requires_gpu=false`, `can_submit=true`, `max_submit_cost=1`)

Selected idea: Q43 P1, a hard cumulative corridor around the anchor (the Sakoe–Chiba analogue)

Implementation: `scripts/q54_dp_corridor.py`

Prior full audit: `reports/q54_dp_hard_path_constraints_2026-07-30.md`

Outcome: **smoke passes activation and degeneracy controls; full gate fails. No Kaggle run or submission. Quota 0/5.**

## 1. Selection — exactly one idea

Q40 found no usable soft transition prior: its deployed L1 term was the best of 45 arms, while nested
selection over all arms lost 1.851 RMSE, helped 20.0% of wells, and had a 3-well bootstrap 5th percentile
of -5.845. In particular, its prefix-derived drift prior failed by 11.475 because a small per-step bias
compounded over a median 477 path steps.

Q43 then ranked P1, a hard global corridor plus slope admissibility limits, as its **highest-value** idea.
It is structurally distinct from Q40's soft penalties because it caps cumulative displacement rather than
adding another repeated cost. Q49 therefore selects P1 and no other proposal.

The repository history matters: Q43 appended P1 as Q54, and Q54 already implemented it and completed the
required 40-well nested audit. Its slope-limit half was also already covered more specifically by N1's
geometry-derived per-step bounds. A second full Q49 sweep would be duplicate compute, so this round runs
only the smallest implementation smoke and uses Q54's completed full audit for the gate.

## 2. Smallest local validation executed

A synthetic four-step path was passed through the checked-in `run_dp_corr` implementation:

```text
baseline_rmse=0.0000000000
corridor_inf_rmse=0.0000000000 bind=0.000000
corridor_zero_rmse=2.7386127875 bind=1.000000
expected_zero_rmse=2.7386127875
SMOKE_PASS: infinite corridor degenerates exactly; zero-width corridor activates and locks the path.
```

This validates both required directions cheaply: `C=inf` reproduces the baseline exactly, while `C=0`
binds on every step and returns the analytically expected anchor-locked RMSE. Outputs are finite. No data,
GPU, background process, or Kaggle artifact was needed.

Q54's full-data controls are stronger and agree: `C=inf` reproduced `run_dp` to 0.0000000000 at lambdas
5/20/60/150, and its finite corridor ladder bound 21.9%, 14.7%, 5.3%, 1.4%, and 0.4% of steps at
`C={2,3,5,10,20}`. The feature was therefore active rather than silently inert.

## 3. Full audit and gate

Q54 ran the same split seed and harness as Q10/Q40 on 40 held-out wells, selected parameters by well in
both fold directions, and scored DP output directly. Its result is the applicable full audit for the one
selected idea:

```text
nested selected       12.570
unconstrained baseline 12.601
nested gain              +0.031
helps held-out wells        2.5%  (1/40)
3-well bootstrap 5th      -0.518
3-well median             +0.000
P(gain > 0)                0.0724
```

| gate | required | observed | verdict |
|---|---:|---:|---|
| nested by-well gain | > 0 | +0.031 | pass, negligible |
| positive 3-well 5th percentile | > 0 | -0.518 | **fail** |
| breadth or justified selector | >50% wells or selector | 2.5%; no test-available selector | **fail** |
| non-duplicate | new candidate | exact idea already completed as Q54 | **fail for another run/artifact** |
| expected public effect if submitting | >0.115 | at most the +0.031 local signal, on a ~12.2 line versus deployed 8.8626 | **fail** |

The mechanism also fails in the expected direction. At the optimal lambda, the unconstrained DP moves
only about +/-3 ft from its anchor while truth requires up to +/-19.4 ft. The DP is over-damped; a corridor
can only remove motion. Q54 found that a corridor can rescue an under-regularised lambda, but it merely
substitutes for the soft penalty and does not improve the optimum materially.

The one helped well does not support a selector: there is no pre-registered, test-available property that
identifies it, and constructing one after observing a single win would not be an honest selector audit.

## 4. Submission decision

**No submission.** Three gates fail, the measured local effect is 0.031 below the required 0.115 public
threshold, and the alignment line remains roughly 12.2 versus the deployed honest line's 8.8626. There is
no candidate output to audit, no kernel to launch, and no quota justification. Q49 closes as superseded by
Q54's stronger full execution, not as an authentication or infrastructure block.

## 5. Live state

- Git fetch succeeded; the working branch matched `juktong/codex/autonomous-queue-2026-07-15` at task start.
- No local Kaggle/papermill/notebook producer was active; only the Codex queue runner and this task worker
  were running.
- The newest owned Kaggle kernel remains `joezzzzz/rogii-frontier-hedgeoff-full` from 2026-07-28; no new
  owned kernel was launched for Q49.
- No submission has been made on 2026-07-31: daily quota remains **0/5 used, 5/5 remaining**.
- Next queued task: `q50_ownership_first_candidate_search`.
