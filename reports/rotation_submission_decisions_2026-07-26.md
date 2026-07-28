# Rotation submission decisions — 2026-07-26

Every submit/HOLD decision with its reason. Submit gate: quota>0 · HARD sanity pass · not a
near-duplicate (rmse ≥ 0.50 vs every scored reference) · clear public or final-slot information value ·
stated justification · accurate description.

| round | candidate | decision | reason |
|---|---|---|---|
| 1 | G1.2 frontier component validation | **no submit (by design)** | Diagnostic only; produces no new submission artifact. Delivered the round's main findings. |
| 1 | G1.1 full-fidelity overlap-OFF ownership run | **HOLD** | Already satisfied by `54968060` (our account, our kernel, patch tracked in repo). A rerun would be homogeneous with a scored submission. |
| 1 | A3/A4/A5 frontier intermediates | **HOLD** (carried from 07-25) | Homogeneous intermediates of an already-submitted family. |
| 2 | G2.1 **SP45-projection-only** | **SUBMITTED `54990075` → 6.690** | Passed all six gate conditions (quota, HARD sanity, non-homogeneous rmse 1.640 vs `54968060`, clear decision value, documented, accurate description). Result settled the post-SP45 question: the stages earn their place; the proxy pointed the wrong way. |
| 2 | H final-selection simulator upgrade | **no submit (by design)** | Analysis only. Now emits score-first / diversity-first / provenance-first separately; all three converge on `54922806 + 54844628`. |

## Standing constraints

- Never submit a smoke/dummy output.
- Never resubmit a homogeneous plain rerun of the Kaiwalya notebook.
- A small public difference on 3 wells is not by itself a reason to submit (config-variance floor ≈0.115).
- The train-copy proxy **saturates** (near-exact retrieval buys only ~0.080 public), so a proxy gain is
  supporting evidence, never sufficient evidence.

| 5 | G3.5 honest prefix calibration | **no submit (closed on evidence)** | Local smoke prerequisite failed: the deployment-honest prefix-cut signal explains only 3.5%/0.5% of toe-bias variance (in-sample upper bound); the apparent 43.4% was a same-run confound. Submit gate never reached — nothing was carried past the smoke. 0 quota used. |

| 6 | G1.3 dependency/provenance audit | **no submit (by design, `can_submit=false`)** | Analysis only. Narrowed the frontier provenance reservation from "9 third-party datasets" to one quantified dependency (≈0.047 public). Slot recommendation unchanged. 0 quota used. |
| 7 | G3.2 learned alignment scorer | **no submit** | Gate condition 1 met (scorer beats NCC by +0.223) and the DP beats the flat-anchor baseline, but the masked split puts it at 12.527 ft vs the deployed pipeline's ~8.86 — the task's own rule forbids a full Kaggle run unless the masked split supports it. 0 quota used. |

| 8 | G3.3 multi-hypothesis trajectory | **no submit (closed on evidence)** | Smoke checks pass but the whole family sits below a trivial flat-anchor baseline (best achievable 16.877 vs 15.833) and far from the deployed ~8.86. Submit gate never reached. 0 quota used. |

| 9 | frontier variant matrix lite | **no submit (HOLD both live axes)** | prefix-aggressive would mostly re-confirm G3.5 (prefix signal 3.5%/0.5%) and the frontier's own selector already chose alpha=0; the bimodal axis fires on only 1 of 3 wells so any public delta sits under the ~0.115 config-variance floor. Neither clears the information-value condition. 0 quota used. |

| 10 | new direction search | **no submit (task is `can_submit=false`)** | Search/diagnostic task with `max_submit_cost=0`. Five measurements closed three candidate lines before any development cost was spent. The one queued direction with a submission path (`n2_increment_structural_field`) must still clear the 3-well gate and the submit gate. 0 quota used. |

| 11 | N4 conformal per-well uncertainty | **no submit (task is `can_submit=false`)** | Diagnostic with `max_submit_cost=0`. Result is negative on its primary question (conditional intervals carry no per-well information and are wider than marginal at matched coverage), so it produces no candidate. Its 3-well draw distribution (5th 3.49 / 95th 15.14 for a fixed model) tightens the evidence bar for every future submission. 0 quota used. |

| 12 | N2 increment structural field | **no submit (3-well gate fails)** | Both variants fail the corrected gate on the full 760-well split: `struct_increment_iso` 5th -1.7148, median 3-well draw -0.0001, P(gain>0) 0.4602; `struct_increment` 5th -5.5224, P(gain>0) 0.1938. The task's own step 4 ("if and only if the gate passes") therefore does not trigger. 0 quota used. |

| 13 | N1 geometry-bounded alignment | **no submit (task is `can_submit=false`; result negative)** | Diagnostic with `max_submit_cost=0`. The band binds but does not improve: on 40 wells the unbounded control is best (12.518) and nested selection yields DP 13.644 vs flat-anchor 12.722. Task step 5's scale-up condition is not met. 0 quota used. |

| 14 | N3 multi-scale GR matching | **no submit (task is `can_submit=false`; diagnostic)** | `max_submit_cost=0`. No decomposition level met the 0.7242 handoff gate. The one positive (typewell window TWH=1, well-split AUC 0.7655) is an emission-side improvement, and N1 established the same day that the alignment gap is in the transition model — so it produces no candidate. 0 quota used. |

| 15 | N6 public-solution audit | **no submit (task is `can_submit=false`; survey)** | `max_submit_cost=0`, and the audit produces no candidate output. Named target did not exist; a real substitute was audited. The one queued follow-up with a submission path (`n8_azimuth_matched_neighbours`) must still clear the 3-well gate. 0 quota used. |

| 16 | N5 typewell fingerprint | **no submit (task is `can_submit=false`; diagnostic)** | `max_submit_cost=0`. The fingerprint reproduces the deployed group-key neighbour set exactly (13/13, 40/40, 13/13), so it yields no candidate. 0 quota used. |

| 17 | N8 azimuth-matched neighbours | **no submit (3-well gate fails at every tolerance)** | All four variants negative on the 760-well reference (-0.0697 to -0.0789) and failing the corrected gate (5th -0.86 to -0.90, P(gain>0) ~0.49, actual-3-test-well -0.0990). Task step 6 therefore does not trigger. 0 quota used. |
