# Rotation candidate queue — 2026-07-26

Scores are 1–5 (5 = best/cheapest/safest). `quota_cost` is the number of submissions a candidate would
consume if it reached the submit gate.

| id | candidate | state | exp_gain_public | H-hidden robustness | non-homogeneity | impl_cost | provenance risk | quota_cost | smoke_ready | proxy support |
|---|---|---|---|---|---|---|---|---|---|---|
| **G1.2** | frontier OOF-style component validation | **audited** | n/a (no submit) | 5 | n/a | 4 | 5 | 0 | 5 | **5 — done this round** |
| G2.1 | small variant matrix (overlap/mpkg/prefix/bimodal/seed) | static_audited | 2 | 3 | 2 | 3 | 3 | 0–1 | 4 | 4 (intermediates already mapped) |
| G2.2 | well-level selector across variants | not_started | 3 | 4 | 4 | 2 | 3 | 1 | 2 | 2 |
| G3.4 | robust final-selection simulator | not_started | n/a (no submit) | 5 | n/a | 5 | 5 | 0 | 5 | 4 |
| G1.1 | full-fidelity overlap-OFF ownership run | **effectively done** | n/a | 5 | 1 (would duplicate `54968060`) | 5 | 4 | 0 | 5 | 5 |
| G1.3 | dependency/provenance audit | static_audited | n/a | 4 | n/a | 4 | 5 | 0 | 5 | 3 |
| G3.1 | stratigraphic heatmap + top-K path search | not_started | 2 | 4 | 5 | 2 | 5 | 0–1 | 3 | 2 (prior top-K work was negative) |
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
