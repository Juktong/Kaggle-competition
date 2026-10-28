# Frontier variant matrix (lite) — 2026-07-28

Autopilot task `frontier_variant_matrix_lite` (`requires_gpu=false`, `can_submit=true`,
`max_submit_cost=1`). Static diff and local proxy only, per the task rules — no plain-frontier rerun.
**No submission this round; 0 quota used.** The round's main product is a corrected map of which
post-SP45 axes are actually active, including **a correction to a claim published on 2026-07-25**.

## Static diff — every intermediate variant vs the submitted `54968060`

All files come from the completed overlap-OFF full run, so this costs no GPU and no quota.

```
file                                       rmse vs 54968060   max|d|   %rows>1ft   non-homogeneous (>=0.50)
submission_model_package_only.csv                    18.143    31.97      99.5%    YES
submission_gold_prefix_aggressive.csv                 1.996     5.73      49.0%    YES
submission_gold_prefix_conservative.csv               1.287     3.05      40.1%    YES
submission_model_package_gated_004..020.csv     1.108-1.131   2.01-2.06   30.4%    YES
submission_before_branch_hedge.csv                    1.103     2.00      30.4%    YES
submission_before_model_package.csv                   1.103     2.00      30.4%    YES
submission_gold_prefix_balanced.csv                   1.103     2.00      30.4%    YES
submission_sp45_learned_w0.50..0.60.csv         1.083-1.103   2.00-2.82   30.4%    YES
submission_audit_copy.csv                             0.000     0.00       0.0%    no
```

## Correction — the bimodal hedge is NOT inert

Every "before X" intermediate sits exactly 1.103 ft from the final output, with `max|d| = 2.00` on
exactly **30.4%** of rows. 30.4% × 14,151 = **4,301 rows = the whole of well `00e12e8b`**. Direct check:

```
final - before_branch_hedge:
  000d7d20  n=3836  rows changed 0      mean_d +0.0000
  00bbac68  n=6014  rows changed 0      mean_d +0.0000
  00e12e8b  n=4301  rows changed 4301   mean_d +2.0000   max|d| 2.000

pf_seed_branch_hedge_report (identical in FAST smoke and full run):
  000d7d20  skip_separation  separation  0.280  shift 0.0  moved_rows 0
  00bbac68  skip_separation  separation  3.594  shift 0.0  moved_rows 0
  00e12e8b  applied          separation 29.439  shift 2.0  moved_rows 4301
```

**The PF bimodal branch hedge applies a +2.0 ft shift to all 4,301 rows of `00e12e8b`** — it is the
single largest post-SP45 effect in the deployed configuration.

**What I got wrong on 2026-07-25 (A5).** I compared `before_branch_hedge` against
`before_model_package`, found them identical, and recorded that as "the bimodal hedge contributes zero".
Those two files *are* identical — but they are both *upstream* of the hedge, so the comparison could not
have detected it. The correct comparison is `final` vs `before_branch_hedge`. The claim propagated into
`reports/kaiwalya_modelpkg_prefix_bimodal_ablations_2026-07-25.md` (A5) and into the wording of G1.3 and
G2.1; all three are corrected here.

**Knock-on to the G1.3 attribution.** G1.3 stated that `54990075` (SP45-only, 6.690) and `54968060`
(6.643) "differ only in the learned-trajectory blend", and attributed the 0.047 public difference to
`fleongg/rogii-claude-models-pub`. That difference in fact spans **two** active stages — the
learned-trajectory blend **and** the bimodal hedge. The dependency *structure* in G1.3 is unaffected
(still one prediction-affecting third-party dataset), but **≈0.047 is a joint upper bound for both
stages, not a clean measurement of the fleongg dataset alone.**

## Which axes are actually live

| axis | status in the deployed config | non-duplicate variation available |
|---|---|---|
| **bimodal hedge strength** | **ACTIVE** — +2.0 ft on 1 of 3 wells (separation 29.4 ft) | yes — largest single post-SP45 effect |
| **prefix calibration strength** | selected profile `balanced` applied `alpha = 0.0`; conservative would move 0.38 ft, aggressive 0.95 ft | yes — aggressive 1.996 / conservative 1.287 rmse vs final |
| model-package blend weight | **guard-rejected** (`p95 29.464 > 25.000`, `selected=False` at every weight) | between weights only ~0.02 rmse — no information |
| SP45/learned weight | active at w=0.60 | between 0.50 and 0.60 only ~0.02 rmse; the extreme was already tested as `54990075` |
| uncertainty/range clipping, per-well confidence gating | not exposed as profile knobs | would need new code — out of scope for a "lite" round |

## Promotion decision — none this round, with the reason

The two live axes were assessed against the submit gate's information-value condition:

- **prefix-aggressive** (largest non-duplicate delta, 1.996). Tests whether stronger self-calibration on
  the well's own known prefix helps. Today's G3.5 result measured that signal at **3.5% / 0.5%** of
  toe-bias variance once the same-run confound is removed, and the frontier's own selector independently
  chose `balanced` (`alpha = 0`, i.e. no movement) over conservative and aggressive. Two independent
  lines therefore already predict this variant is not an improvement, so a slot spent on it would mostly
  re-confirm G3.5 rather than resolve an open question.
- **bimodal hedge strength**. Newly identified as the largest live axis, but it fires on **1 of 3 wells**,
  so any public delta would be a single-well effect measured against a ~0.115 config-variance floor — not
  resolvable by the leaderboard.

Neither clears "clear public-score, private-risk, final-slot, or non-homogeneity information value" in a
way that justifies a slot. **HOLD both.** Quota preserved at 0/5.

## What would change this

The bimodal axis becomes worth a slot if a variant can be constructed that changes **more than one well** —
for example lowering the `skip_separation` threshold so the hedge also fires on `00bbac68`
(separation 3.594 ft, currently skipped). That is a single-line profile change and is recorded as the
concrete next variant if this line is revisited; it was not run here because the task caps promotion at
1–2 variants with clear information value, and a one-well effect does not qualify.
