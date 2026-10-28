# Q41 — non-homogeneous ensemble search: 0 of 355 arms clear the 3-well gate

Date: 2026-07-29 17:40 UTC
Task: `q41_nonhomogeneous_ensemble_search` (`requires_gpu=false`, `can_submit=true`, `max_submit_cost=1`)
Script: `scripts/q41_nonhomogeneous_ensemble.py` · Log: `reports/logs/q41_ensemble_2026-07-30.log`
Outcome: **closed with an exact reason. No submission. Quota 0/5.**

## 1. Blocker on the arm the task asks for first

The task's first requested ensemble is **honest + frontier**. It **cannot be validated by well**: the
frontier family exists locally only as **test-set submission CSVs** — 14,151 rows over the 3 hidden wells,
**no truth**. There is no frontier prediction on any train well, so no honest+frontier mix can be scored
against truth, bootstrapped, or gated.

What could be computed for that arm is only *how different* the outputs are, which is non-homogeneity
without accuracy — precisely the "information without validation" the ledger has repeatedly declined to
act on. **Recorded as a blocker, not guessed at.** Producing such an ensemble would require a fresh
frontier GPU run to generate train-well predictions, which Q33's budget rules out.

Everything below is therefore on the honest family, where truth exists on 760 wells / 3.72M rows.

## 2. Why this is not a repeat of the 2026-07-22 audit

That audit tested **single** candidates against the 3-well gate and every one failed — including
`topk96_l75`, best OOF at 8.5070 (+0.3556 vs deployed) but 3-well 5th **−1.946**, beating baseline in only
59% of draws. Its recorded lesson: per-well gain std (~1.3) far exceeds the mean gain, so the 5th
percentile is negative for everything.

That is a **variance** failure, and averaging is the one operation that reduces variance — Rule #1's
transferable class. So Q41 asks the one question the earlier audit could not: **does an ensemble of
decorrelated members clear the gate that every single member fails?**

## 3. Which members are actually decorrelated

Correlation of each member's **error** with the deployed line's error:

```
member          pooled   corr(err, deployed)
dwt            10.2891        0.8679          <- genuinely different mechanism
pf             11.0563        0.8305          <- genuinely different mechanism
base            9.2987        0.9737
s_54844628      8.8626        1.0000          <- deployed
s_54878409      8.6825        0.9702
s_a20_w25       8.6790        0.9721
base_k96        9.2555        0.9667
s_k96_aniso     8.6547        0.9636
topk96_l75      8.5070        0.9445
```

DWT and PF are the only genuinely decorrelated axis (0.83–0.87); the structural-field variants are
near-duplicates of each other (0.96–0.97). Mixing those is the "average near-duplicates" the task forbids,
and both classes were included so the distinction is **measured rather than asserted**.

## 4. Result — 355 arms, and none clears the gate

Arms: every member pair at 9 weights, equal-weight triples, per-row median over 3 and 5, and a 5-member
mean — 355 in all.

```
=== top arms by pooled RMSE ===
('pair', ('s_54844628','topk96_l75', 0.1))   8.4984   +0.3642 vs deployed
('pair', ('s_a20_w25','topk96_l75', 0.2))    8.5008   +0.3618
('pair', ('pf','topk96_l75', 0.1))           8.5015   +0.3612
('single','topk96_l75')                      8.5070   +0.3556
```

```
=== NESTED across all 355 arms, splits BY WELL ===
  picks: pair(s_a20_w25, topk96_l75, 0.1) / pair(pf, topk96_l75, 0.1)
  selected 8.5281  vs deployed 8.8626  gain +0.3346
  helps 58.8% of held-out wells
  3-WELL bootstrap 5th -1.3687  50th +0.1759  95th +1.9578  P(>0) 0.6108
```

| gate condition | required | observed | verdict |
|---|---|---|---|
| nested gain over deployed | > 0 | **+0.3346** | PASS |
| helps a majority of wells | > 50% | **58.8%** | PASS |
| 3-well bootstrap 5th | > 0 | **−1.3687** | **FAIL** |

Two of three pass — the best result any candidate has produced against this gate — and the third still
fails.

### The variance hypothesis is refuted, and the structure says why

```
arms with 3-well 5th > 0:  0 of 355
```

Not one. And the ordering is the informative part — the arms with the **least negative** 5th percentile are
the ones that change the deployed line **least**:

```
arm                                          3w 5th   helps%   pooled
('single','s_54844628')                     +0.0000     0.0%   8.8626   <- deployed vs itself
('pair', (s_54844628, s_a20_w25, 0.9))      -0.0684    56.8%   8.8224
('pair', (s_54844628, s_54878409, 0.9))     -0.0709    54.6%   8.8213
('pair', (s_54844628, s_k96_aniso, 0.9))    -0.0780    62.5%   8.8134
('pair', (s_54844628, topk96_l75, 0.9))     -0.1103    64.6%   8.7843
```

**The 3-well 5th percentile is maximised by not changing the deployed line at all**, and degrades
monotonically with the size of the change — in *both* directions, including changes that improve pooled
RMSE and help ~65% of wells. Averaging did not buy the variance reduction the hypothesis predicted.

The arithmetic explains it: with per-well gain mean ≈ 0.35 and std ≈ 1.3, a 3-well mean has 5th percentile
≈ 0.35 − 1.645 × 1.3/√3 ≈ **−0.88**. To clear zero at n=3 a candidate would need mean gain ≳ 1.2 — more
than three times the best pooled gain available anywhere in this space.

### The apparent ensemble gain is really member substitution

Best ensemble **8.4984** vs best single member `topk96_l75` **8.5070** → the ensemble adds **+0.0086**.
The nested +0.3346 is almost entirely *"use `topk96_l75` instead of `s_54844628`"*, not *"ensemble"*. So
even the passing conditions are not an ensembling result, and member substitution was already closed by
the 07-22 audit for failing this same gate.

## 5. Exact reason for closing

**No candidate passes**, and the reason is structural rather than a near miss:

1. **0 of 355 arms have a 3-well bootstrap 5th percentile > 0**, and the maximum over the space is
   attained by leaving the deployed line unchanged.
2. **The gate is unreachable at n=3 for this effect size** — clearing it needs a mean per-well gain ≳ 1.2
   against a best available of ~0.36.
3. **Ensembling contributes +0.0086** over the best single member, so the mechanism this task was created
   to test contributes essentially nothing here.
4. Submission criteria are not met either: nothing has an expected public effect > 0.115 (Q33's bar), and
   nothing changes final-slot logic (Q53 showed slot 1 turns on a question no public evidence can settle).

## 6. One observation recorded, not recommended

`topk96_l75` is **0.3556 better than the deployed honest line on 760-well OOF and has never been
submitted**. It is not proposed as a candidate: it fails the 3-well gate (5th −1.946 per the 07-22 audit),
its error correlates 0.9445 with the deployed line so it adds little diversity for slot 2, and N4 measured
OOF→public transfer at 1.659× rather than 1:1. Recorded so the option is visible to the owner rather than
silently dropped.

## 7. Limits

- The honest+frontier arm is **untested**, not negative — §1.
- Ensembles are over 9 stored prediction columns; a member built specifically to decorrelate from the
  deployed line was not constructed and might behave differently.
- Weights are global. Per-well or gated weights were **not** tested: those are the hard-selection class the
  ledger has closed repeatedly, and Q40 additionally showed per-step directional terms compound.
- The 3-well bootstrap resamples train wells with replacement as a proxy for the competition's 3 wells; it
  is the standing scale check, not the actual test draw.

## 8. Next

`q42_honest_line_error_taxonomy`. `q29_final_slot_candidate_packager` reactivates **2026-08-03**; the
final selection action is due by **2026-08-04** and costs no quota.
