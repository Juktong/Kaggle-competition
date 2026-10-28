# Q12 — coverage-gated self-correlation template, 2026-07-29

Autopilot task `q12_coverage_gated_self_template` (`requires_gpu=false`, `can_submit=true`,
`max_submit_cost=1`). Script: `scripts/q12_coverage_gated_self.py`. Log:
`reports/logs/q12_coverage_gated_2026-07-29.log`.

**Result: the coverage gate does not stratify the effect. There is no coverage band in which the self
template wins, so there is nothing to gate on.** No submission; quota untouched at **0/5**.

## 1. What N9 had already settled, and what was actually left open

N9 measured, at the **state** level: self AUC **0.7174** on prefix-covered states vs **0.4548** on
uncovered ones — so interpolation across gaps is harmful. But it also measured that *even restricted to
covered states* self (0.7174) trails the typewell (0.7710), and `both` on covered states (0.7680) is still
below typewell alone.

So the state-level gate was already tested by N9 and does not rescue the template. The one form left open
was a **well-level** gate: N9 pools coverage across wells, so a subpopulation of high-coverage wells could
favour self without appearing in the pooled figure. That is the only thing Q12 can add, and it is what was
tested.

The gate is test-available: per-well prefix coverage = the fraction of candidate TVT states the well's own
known prefix visits, from `TVT_input` alone, no truth.

Design is identical to N9 — same grid, sampling, features, MLP, `TWH=1`, toe rows only, splits **by well**
(60 train / 60 eval, disjoint). The only change is that AUC is computed **per well** and stratified.

## 2. Result — 60 held-out wells

```
pooled (mean of per-well AUC):   typewell 0.7472   self 0.6439   both 0.7484

coverage band     n   typewell     self     both   self-typewell   both-typewell
0.56-0.72        12     0.7695   0.6374   0.7665         -0.1320         -0.0030
0.72-0.75        12     0.7560   0.6480   0.7512         -0.1079         -0.0048
0.75-0.78        12     0.7332   0.6108   0.7136         -0.1224         -0.0196
0.78-0.82        12     0.7161   0.7108   0.7563         -0.0053         +0.0403
0.82-0.92        12     0.7613   0.6124   0.7546         -0.1489         -0.0067

cov >=     wells   self-typewell   both-typewell
0.00          60         -0.1033         +0.0012
0.60          59         -0.1004         +0.0015
0.70          52         -0.1006         +0.0004
0.80          22         -0.0792         +0.0149

wells where self beats typewell: 21.7%    both beats typewell: 51.7%
corr(coverage, self - typewell) = 0.0867
corr(coverage, both - typewell) = 0.0604
```

## 3. Reading

- **`self` never wins in any band.** Its deficit ranges from −0.005 to −0.149 and is negative in all five.
- **`both` is indistinguishable from typewell alone** — pooled +0.0012, with 51.7% of wells favouring it.
  A coin flip.
- **Coverage does not stratify the effect.** The correlation between a well's coverage and the self
  advantage is **0.0867**; for `both` it is **0.0604**. Both are ≈ 0. This is the finding that closes the
  task: a gate can only help if the gating variable predicts where the treatment works, and this one
  does not.
- **The one apparently-positive cell is not a coverage effect.** Band 0.78–0.82 shows `both` at +0.0403,
  but the *highest*-coverage band (0.82–0.92) is −0.0067 and the second-highest is −0.0196. If coverage
  drove the effect the ordering would be monotone; it is not. With 12 wells per cell and band-to-band
  swings of ±0.04, that cell is noise. Selecting the `cov ≥ 0.80` threshold post hoc on the same data
  would be the sweep-not-a-validation pattern the ledger has repeatedly closed.

### Why the state-level and well-level results are both true

N9's state-level split (0.7174 covered vs 0.4548 uncovered) is a **within-well** contrast: inside a given
well, the states its prefix visited are scored better than the states it did not. Q12's well-level result
is a **between-well** contrast: a well's overall coverage fraction does not predict whether self beats the
typewell *for that well*. Both hold simultaneously, and only the second one could have supported a gated
candidate.

This is the same between-unit / within-unit decomposition that the N6 audit flagged as a general lesson —
*when a correlation motivates a per-unit gate, check whether it is a within-unit or a between-unit
effect.* Here it is within-unit, and the gate needs a between-unit effect.

## 4. Verdict

- Task step 5 asks whether this "improves any well family without worsening uncovered wells". It does
  not: no coverage band favours self, `both` is a coin flip, and the gating variable carries no
  stratifying information. Step 6 therefore never triggers. **No submission.**
- **Direction closed**: coverage-gated self-correlation, at both the state level (N9) and the well level
  (Q12). Together with N9 this closes the self-template line entirely.
- **Retained**: N9's banked fallback stands unchanged — a typewell-independent emission at 0.7174 on
  covered states, usable if a future line needs to test whether the typewell is the limiting factor. What
  Q12 adds is that it cannot be *selectively deployed* by coverage, so it would have to be used wholesale
  or not at all.
- Slot recommendation unchanged: `54922806` + `54844628` under all three criteria.
