# G1.2 — frontier component validation on masked splits (2026-07-26)

Goal: validate the frontier's components on held-out data rather than trusting the public score alone.
**Completed without spending a Kaggle run**: the frontier notebook performs its own masked-split
evaluation internally (`visible_prefix_cut_fracs = 0.50/0.65/0.75` cuts each well's *known* prefix and
scores candidates on the held-out remainder) and writes the per-component reports. These were read from
the completed overlap-OFF full run (`joezzzzz/rogii-kaiwalya-overlap-off-full` v1 = `54968060`, 6.643).

## 1. Masked-split candidate ranking — the decisive table

`gold_prefix_cut_report.csv` (3 wells × 3 cuts, 154 candidates each):

```
well      cut  holdout_rows  best_candidate               best_rmse   default(PF) rmse
000d7d20  .50      721       contact_md_lookup_egfdl        0.0081        4.020
000d7d20  .65      505       contact_md_lookup_astnu        0.0058        1.630
000d7d20  .75      360       contact_md_lookup_astnu        0.0056        0.577
00bbac68  .50      773       contact_md_lookup_ancc         0.0094       26.957
00bbac68  .65      541       contact_md_lookup_ancc         0.0103        5.501
00bbac68  .75      386       contact_md_lookup_egfdl        0.0075        0.787
00e12e8b  .50     1041       contact_md_lookup_astnu        0.0085       39.934
00e12e8b  .65      729       contact_md_lookup              0.0073        4.402
00e12e8b  .75      521       contact_md_lookup_buda         0.0056        3.502
```

**On every well and every cut the winner is a `contact_md_lookup_*` candidate at ~0.008 ft RMSE** —
essentially exact retrieval — versus 0.58–39.9 ft for the best PF candidate. The suffixes
`astnu / ancc / egfdl / buda` are the **train-only structural-surface columns**. So this is the same
retrieval mechanism as the guarded overlap override, reached through the prefix-calibration path.

`gold_prefix_calibration_report.csv` confirms per-well selection with `consistency = 1.0` and
`rank_margin ≈ 1e-13` (the lookup wins by a wide, perfectly consistent margin).

## 2. Did that lookup actually get applied in `54968060`? — No

This matters, because if it had, the "overlap-OFF" label would be wrong.

```
gold_prefix_moves_balanced.csv : alpha = 0.0 for all 3 wells
log 'Visible-prefix selected'  : selected_profile 'balanced', applied_wells 0,
                                 mean_abs_move 0.0, max_abs_move 0.0, contact_override_enabled False
                                 (conservative would have applied 3 wells / 0.38 ft;
                                  aggressive     3 wells / 0.95 ft)
```

The selected `balanced` profile applied **zero movement**. Combined with
`guarded_overlap_override: False`, **`54968060` is a genuine no-lookup run** and its 6.643 stands as a
clean measurement of the frontier without retrieval.

## 3. The saturation finding — proximity to train-copy TVT does not buy public score

Putting §1 and the public results together:

```
contact_md_lookup reaches ~0.008 ft RMSE against the train copy on held-out prefix rows
...yet enabling the retrieval path is worth only ~0.080 public (6.643 -> 6.563)
```

Near-exact retrieval of the **train copy's** TVT converts into almost nothing on the leaderboard. This
independently confirms the 2026-07-22 finding that the scored truth is not the train-copy TVT, and it
quantifies the saturation: **the train-copy proxy is only weakly informative, and it saturates.** Any
local proxy result must be read with that ceiling in mind. (Recorded because it directly limits how much
weight the per-stage table below can carry.)

## 4. Per-stage component contribution inside the overlap-OFF run

Proxy RMSE vs train-copy TVT at each written stage (relative comparison only, per §3):

```
SP45 projection                          2.581
learned trajectory                       4.456   (+1.875)
after prefix-cal (balanced, selected)    3.105   (-1.351)   <- = SP45/learned blend w0.60 + prefix stage
before model-package                     3.105   ( 0.000)
before bimodal hedge                     3.105   ( 0.000)
FINAL = 54968060 (public 6.643)          3.259   (+0.155)   <- model-package correction
--- reference ---
54844628 honest (public 7.891)           3.677
```

Component read-outs:

- **SP45 projection is the strongest single stage on the proxy (2.581)** — better than the final output.
- **The learned-trajectory component is much weaker alone (4.456)**; the w=0.60 SP45/learned blend lands
  between them (3.105).
- **Prefix calibration and the bimodal hedge contribute exactly 0.000** in this configuration (balanced
  profile applied nothing; `pf_seed_branch_hedge_report` shows 2 of 3 wells `skip_separation`, and the
  one applied well moved 2.0 ft on 4301 rows).
- **The model-package correction moves the proxy the wrong way (+0.155)** while consuming the entire
  third-party dataset dependency. Its ft-scale is small and bounded (per A3: max 2.0 ft, 30% of rows).

## 5. What this changes

1. **`54968060` is validated as a genuine no-retrieval frontier run** — the slot-2 candidacy rests on
   solid ground.
2. **The frontier's strength is concentrated in SP45 + PF/beam**, not in the later refinement stages,
   two of which are inert here and one of which is proxy-negative.
3. **A concrete round-2 candidate exists**: an *SP45-projection-only* variant. Audit:
   HARD PASS, proxy RMSE **2.581** (best of any candidate), rmse **1.809 vs `54968060`** → non-homogeneous.
   Its information value is that it tests directly whether the frontier's post-SP45 stages help or hurt
   on the leaderboard — which decides which frontier variant should hold slot 2.
   **Caveat (§3): the proxy saturates, so its 0.68 ft proxy advantage may not transfer.** It is worth one
   submission as an information-bearing test, not as an expected score improvement.

No submission was made this round; §5.3 is queued for round 2 under the normal smoke → full → gate flow.
