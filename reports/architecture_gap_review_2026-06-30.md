# Architecture Gap Review - 2026-06-30

## Leaderboard Gap

Source: Kaggle API public leaderboard snapshot downloaded at `2026-06-30 11:58 UTC`.

| item | value |
| --- | ---: |
| public leaderboard rows | `3993` |
| current team | `lee Marc223` |
| team members | `joezzzzz, leemarc223` |
| current public rank | `145` |
| current public score | `7.182` |
| first place public score | `5.285` |
| absolute RMSE gap to first | `1.897` |
| our RMSE relative to first | `+35.89%` |
| our MSE relative to first | `1.8467x` |
| MSE reduction needed to match first | `45.85%` |

Rank landmarks:

| target | score | RMSE improvement needed | MSE reduction needed |
| --- | ---: | ---: | ---: |
| first place | `5.285` | `1.897` | `45.85%` |
| rank 5 | `5.813` | `1.369` | `34.49%` |
| rank 10 | `6.333` | `0.849` | `22.25%` |
| rank 50 | `6.989` | `0.193` | about `5.3%` |
| rank 100 | `7.164` | `0.018` | about `0.5%` |

The current pending SP45 submission `54198676` is still `PENDING` as of the latest checked submissions list, so the public leaderboard has not yet incorporated that experiment.

## Competition Interpretation

This is a per-well sequence reconstruction problem, not a normal row-wise tabular regression problem.

Inputs:

- horizontal well sequence with `MD`, `X`, `Y`, `Z`, `GR`, and partial `TVT_input`;
- typewell sequence with `TVT` and `GR`;
- train rows also contain true `TVT` and formation columns;
- submission rows are suffix positions where `tvt` must be predicted.

The public visible sample has 3 test wells and `14,151` submission rows, but hidden rerun can replace those wells. Therefore row count alone is not evidence of hidden compatibility.

The winning signal is likely the hidden TVT trajectory for each well. Useful methods reconstruct that trajectory from:

- known prefix `TVT_input` anchors;
- GR curve alignment against typewell;
- physical constraints in TVT/MD/Z;
- particle filtering, beam search, DTW/NCC, or similar path-search;
- per-well routing and smoothing;
- learned residual or drift correction trained with group-aware pseudo-hidden validation.

## Public Architecture Research

Public kernels with strong votes or useful claimed scores cluster around the same themes:

| public notebook | claimed/observed theme |
| --- | --- |
| `degnonguidi/public-score-rogii-lb-7-159` | dual pipeline: ridge-SP45 branch plus Fleongg/PF/GBM branch, then blend |
| `baidalinadilzhan/rogii-lb-7-201` | PF, beam search, NCC/GR matching, Ridge/CatBoost/LightGBM, public artifact blend |
| `bernubritz/rogii-lb7295-public-rebuild` | same broad dual-pipeline family as Baidalin |
| `pilkwang/rogii-target-free-tvt-geosteering` | target-free geosteering, DTW/NCC alignment, gates, exact-match/overlap guards |
| `romantamrazov/rogii-super-solution-lb-top-3` | early strong physical + LGBM/CatBoost stack with beam/NCC/spatial imputation |
| `shinyanagai123/triple-signal-beam-search-dual-pf-lightgbm` | beam search, dual particle filters, spatial ANCC, LightGBM |
| `mitchgansemer/drift-targeting-ncc-tree-based-rogii-wellbore` | drift prediction rather than absolute TVT; GR cross-correlation and GroupKFold |

The common pattern is structural trajectory inference plus model/routing layers. The public code does not suggest that a plain global blend-weight sweep is enough to reach the top of the leaderboard.

## Current Architecture Assessment

Current confirmed useful score:

- `7.182`: active-account reproduction of the public 7.235-ish physics/PF stack.

Current local families:

- baseline physics/PF stack;
- SP45 projection branch;
- SP45+Fleongg blend sweep;
- Fleongg standalone learned branch;
- light GR/typewell correction candidates;
- sparse plateau quantile information candidates;
- artifact-stack attempts, currently negative or risky.

Observed official calibration:

- Fleongg standalone scored `7.787`, clearly worse than the active baseline.
- Henry/TabICL artifact retry scored `13.453`, a negative calibration.
- Static replay notebooks produced blank public scores, so static visible-test replay is not safe.
- The best public-reference family available to us, the 7.159/7.201-style branch, is still only around the `7.1` band when it works.

Current local validation says:

- simple plateau rules can beat `last_value` in pseudo-test CV only narrowly and sparsely;
- relaxed GR/typewell candidates are plausible replacement information, but not proven high-upside;
- many SP45+Fleongg variants are highly redundant and should only be used as a deliberate low-dimensional calibration sweep.

## Can Current Architecture Beat First Place?

Short answer: not by parameter tuning alone.

The gap to first is too large:

- matching first requires reducing current MSE by about `45.85%`;
- matching rank 10 requires about `22.25%` MSE reduction;
- the known public family near `7.159` improves our current `7.182` by only `0.023` RMSE.

That means:

- global blend weights, SP45/Fleongg weight sweeps, smoothing constants, and light GR shifts can plausibly find `0.02-0.30` RMSE;
- a lucky structural branch could move more, but current candidates do not provide evidence for a `1.9` RMSE jump;
- reaching the first-place public score likely requires a stronger hidden-well inference architecture or a powerful public-split insight not present in the current stack.

The current architecture can still be useful for:

- stabilizing rank around the current public-good band;
- learning which public reference families transfer under the active account;
- moving toward top 100/top 50 if a pending SP45 or replacement branch improves.

It is not enough, as currently organized, to credibly target first place.

## Strategic Pivot

The next architecture should be built around per-well trajectory inference and routing:

1. Generate multiple candidate TVT paths per well:
   - last-value baseline;
   - PF variants;
   - beam-search variants;
   - DTW/NCC GR-alignment variants;
   - SP45/geometric projection;
   - learned residual/drift candidate.
2. Score candidates locally on pseudo-hidden suffixes using GroupKFold by well and prefix-length splits.
3. Train or hand-code a per-well router:
   - inputs: prefix length, GR missingness, GR/typewell correlation, Z span, known-prefix residuals, path smoothness, anchor consistency;
   - output: candidate family or low-dimensional mixture.
4. Add per-row uncertainty/gating:
   - only apply aggressive corrections where diagnostics show high confidence;
   - fallback to stable PF/physical path otherwise.
5. Use public submissions to calibrate only low-dimensional decisions:
   - route family yes/no;
   - one or two blend weights;
   - not a high-complexity model trained directly on leaderboard feedback.

## Near-Term Decision

Keep the current operational plan while `54198676` is pending:

- if SP45 scores close to or better than `7.182`, submit one SP45+Fleongg calibration point and analyze direction;
- if SP45 is weak, stop spending redundant SP45 blend slots and promote replacement candidates;
- in parallel, start designing the per-well path-router architecture because first-place chasing requires that structural upgrade.
