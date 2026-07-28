# Rotation candidate queue — 2026-07-26

Scores are 1–5 (5 = best/cheapest/safest). `quota_cost` is the number of submissions a candidate would
consume if it reached the submit gate.

| id | candidate | state | exp_gain_public | H-hidden robustness | non-homogeneity | impl_cost | provenance risk | quota_cost | smoke_ready | proxy support |
|---|---|---|---|---|---|---|---|---|---|---|
| **G1.2** | frontier OOF-style component validation | **audited** | n/a (no submit) | 5 | n/a | 4 | 5 | 0 | 5 | **5 — done this round** |
| G2.1 | SP45-only variant | **submitted → 6.690** | — | — | — | — | — | 1 used | — | settled: post-SP45 stages earn their place |
| G2.2 | well-level selector across variants | **closed** | — | — | — | — | — | 0 | — | oracle margin +0.0000; proxy inverts within-family |
| G3.4/H | final-selection simulator (3 criteria) | **audited** | n/a (no submit) | 5 | n/a | 5 | 5 | 0 | 5 | 5 — all criteria converge |
| G1.1 | full-fidelity overlap-OFF ownership run | **effectively done** | n/a | 5 | 1 (would duplicate `54968060`) | 5 | 4 | 0 | 5 | 5 |
| G1.3 | dependency/provenance audit | static_audited | n/a | 4 | n/a | 4 | 5 | 0 | 5 | 3 |
| G3.1 | stratigraphic heatmap + top-K path search | **closed** | — | — | — | — | — | 0 | — | DP converges to flat-anchor from above; emission adds no info |
| G3.5 | honest prefix calibration for `54844628` | not_started | 2 | 4 | 3 | 3 | 5 | 0–1 | 3 | 2 (heel explains ~5% of toe bias) |
| G3.2 | learned local alignment scorer + DP | not_started | 1 | 3 | 4 | 2 | 5 | 0–1 | 3 | 1 (NCC baseline 0.52; ~34× scale mismatch) |
| G3.3 | multi-hypothesis trajectory model | not_started | 2 | 4 | 5 | 1 | 5 | 0–1 | 2 | 2 |

## Notes that change the default order

- **G1.1 is effectively already satisfied.** `54968060` *is* a full-fidelity overlap-OFF run executed
  from our account (`joezzzzz/rogii-kaiwalya-overlap-off-full` v1), with the notebook, patch and metadata
  tracked in this repo. Re-running it would produce a homogeneous output and is not scheduled.
- **G1.2 completed without a Kaggle run** — the frontier writes its own masked-split component reports;
  they were read from the completed full run. This is the round's main result.
- **G2.1's intermediates are already mapped** (A3/A4/A5, 2026-07-25): model-package = bounded ~1.1 ft
  top-up; prefix-aggressiveness and bimodal are inert on the visible wells. A new variant matrix has low
  expected information beyond what those diffs already showed, so it drops below G3.4.
- **G3.4 rises**: it costs no quota, needs no GPU, and directly serves the final-2 decision, which is the
  binding question with ~10.9 days left.

## Execution order for round 2

1. **G3.4** robust final-selection simulator (no quota, directly decision-relevant).
2. **G1.3** dependency/provenance audit (closes the one open reservation about `54968060` as slot 2).
3. G2.2 well-level selector — only if G1.2/G3.4 surface a well-level signal worth selecting on.

## Re-prioritisation after round 2 (`54990075` = 6.690)

The SP45-only result removes the main reason to keep exploring frontier stage-truncation variants: the
post-SP45 stages are net-positive on the leaderboard, so removing components is not a productive axis.
Combined with the earlier A3/A4/A5 finding (model-package is a bounded ±2 ft top-up; prefix-aggressiveness
and bimodal are inert on the visible wells), **G (small variant matrix) drops to the bottom** — the
remaining knobs are either inert or already shown to be net-positive as configured.

Revised order:
1. **G2.2 well-level selector** — the one remaining way to combine existing scored outputs without a new
   pipeline. Local-only first.
2. **G3.1 heatmap + top-K path search** — a genuinely different alignment formulation.
3. **G3.5 honest prefix calibration** — improves the fully-owned hedge, which all three selection
   criteria now place in slot 2.
4. G3.2 / G3.3 — higher cost, weaker prior support.
5. G (variant matrix) — deprioritised per above.

## 2026-07-28 update

- **G3.5 honest prefix calibration — closed on evidence.** Deployment-honest prefix-cut signal explains
  3.5% (CUT 0.70) / 0.5% (CUT 0.50) of toe-bias variance, in-sample upper bound; the apparent 43.4% was a
  same-run confound. Weaker than the raw heel level (~5–17%) already exploited by the deployed anchor.
  0 quota used. Report: `reports/g35_honest_prefix_calibration_2026-07-28.md`.
- Next runnable: **`g13_dependency_provenance_audit`** (priority 20, no GPU, `can_submit=false`) — closes
  the one open reservation about the frontier line's third-party dataset dependencies.

