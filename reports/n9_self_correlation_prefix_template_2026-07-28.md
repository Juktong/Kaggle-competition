# N9 — self-correlation: the lateral's own known zone as the matching template, 2026-07-28

Autopilot task `n9_self_correlation_prefix_template` (`requires_gpu=false`, `can_submit=false`,
`max_submit_cost=0`). Script: `scripts/n9_self_correlation.py`. Log:
`reports/logs/n9_self_correlation_2026-07-28.log`. No submission; quota untouched at 0/5.
Diagnostic only — no DP and no trajectory were built, per the task.

**Result: the self template carries genuine signal, but it is clearly weaker than the typewell and adds
nothing in combination. Gate fails; direction closed.** The round does isolate exactly where the
mechanism works and where it back-fires.

## 1. Step 4 first — does the prefix even cover the toe's TVT levels?

This gates everything: if the known prefix never visited the toe's stratigraphic levels, the mechanism
cannot apply. Measured over 200 wells / 963,869 toe rows, using each toe row's **true** TVT:

```
prefix row within  0.5 ft of the toe row's true TVT : mean 0.6348   median 0.7132   >0.5 in 66.0% of wells
                    1.0 ft                          : mean 0.6480   median 0.7384   >0.5 in 67.0%
                    2.0 ft                          : mean 0.6741   median 0.7831   >0.5 in 70.5%
                    5.0 ft                          : mean 0.7534   median 0.8819   >0.5 in 78.0%
                   10.0 ft                          : mean 0.8479   median 1.0000   >0.5 in 89.0%
toe rows inside the prefix TVT RANGE at all         : mean 0.6183   median 0.6728
wells with under 10% of toe rows in range           : 13.0%
```

**Coverage is ample** — 63.5% of toe rows have a prefix row within half a foot of their true TVT. The
mechanism is not blocked, so the test is worth running. The 13% of wells with almost no overlap are a
recorded caveat, not a blocker.

## 2. One-factor comparison

Everything is held at N3's protocol — same candidate state grid (from the typewell's TVT range), same
pair sampling, same features, same tiny MLP, same `TWH=1`, splits **by well** (60 train / 40 validation,
disjoint). The only change is where the profile comes from:

- `typewell` — profile is the typewell GR interpolated at each state (the control)
- `self` — profile is the mean GR of **prefix** rows whose known TVT falls in that state's bin
- `both` — the two feature blocks concatenated

One deliberate departure from N3: **only toe rows are scored**. Prefix rows would be trivially
self-matching under the `self` arm. This makes the in-run `typewell` arm the valid control rather than
N3's all-row figure — and the two agree closely (0.7706 here vs N3's banked 0.7655 ± 0.0030), which is a
useful consistency check on the harness.

## 3. Results — held-out-well AUC

```
arm          LEARNED      level    cov frac   AUC|covered   AUC|uncovered
typewell      0.7706     0.7522      0.5833        0.7710          0.7774     <- control
self          0.6628     0.6175      0.5833        0.7174          0.4548
both          0.7649        --       0.5833        0.7680          0.7354

seed stability of `both`: 0.7649 0.7641 0.7524 -> mean 0.7605, std 0.0057
```

- **The self arm loses by −0.108** against the control (0.6628 vs 0.7706) — roughly 19× the seed-noise
  scale of 0.0057. Not close.
- **`both` does not beat `typewell` alone** (0.7605 ± 0.0057 vs 0.7706). Adding the self block costs a
  little rather than adding; there is no complementary information to harvest.

### The covered/uncovered split is the informative part

The self arm reaches **0.7174 on states the prefix actually covers** but **0.4548 — below chance — on
states it does not**. That is the mechanism behaving exactly as predicted: it works where the prefix has
data, and actively misleads where the profile had to be interpolated across a gap. The typewell arm shows
no such asymmetry (0.7710 vs 0.7774), because a typewell is a continuous log with no gaps.

So the honest summary is: **self-correlation is real but partial**, and its interpolation fallback is
harmful. Even restricted to the 58.3% of covered states, it still trails the typewell (0.7174 vs 0.7710).

## 4. Why the level-offset advantage did not pay off

The premise was sound — the prefix shares one instrument and one baseline with the toe rows, so it removes
the cross-instrument level offset that N3 showed dominates the cue. That advantage is real but is
outweighed by two disadvantages:

- **Coverage.** The typewell spans the full stratigraphic column continuously; the prefix samples only the
  levels the well happened to traverse (58.3% of candidate states), and the gaps must be filled by
  interpolation, which the covered/uncovered split shows is worse than useless.
- **Sampling quality.** The typewell's GR at a given TVT comes from a clean vertical section. The prefix's
  GR at that TVT comes from a horizontal traverse at some lateral displacement, so it carries the well's
  own lateral heterogeneity as noise on the level cue.

The level-offset problem was worth removing; it simply is not the binding constraint.

## 5. Verdict

- The task's gate — *the self arm must beat the typewell arm* — is **not met** (0.6628 vs 0.7706), and
  the combined arm does not beat the control either. **Direction closed.**
- **Banked positive worth keeping:** on covered states the self template reaches 0.7174 from a source
  completely independent of the typewell. If a future formulation ever needs an emission that does not
  depend on the typewell at all — for instance to test whether the typewell is the limiting factor — this
  is the measured fallback, and it must be gated on the coverage mask rather than interpolated.
- Diagnostic only, as instructed: no DP, no trajectory, no submission. N1 already established that the
  alignment gap is in the transition model rather than the emission, so a weaker emission was never going
  to change that.
