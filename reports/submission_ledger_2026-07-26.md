# ROGII submission ledger — 2026-07-26

Team = "lee Marc223" (`joezzzzz` + `leemarc223`), quota 5/day team-wide.
**Today (2026-07-26 UTC) used: 1 of 5 → 4 remaining.** Live-checked 15:09 UTC.
Deadline **2026-08-05 23:59 UTC** (~10.9 days).

## Board

| ref | date | public | side | role |
|---|---|---|---|---|
| `54922806` | 07-23 | **6.563** | teammate | best-public (frontier overlap-ON) — slot 1 |
| `54990075` | 07-26 | 6.690 | **ours** | frontier SP45-only — settled the post-SP45 question |
| `54968060` | 07-25 | **6.643** | **ours** | frontier overlap-OFF (validated no-retrieval) |
| `54896975` | 07-22 | 6.669 | teammate | frontier overlap-ON |
| `54923144` | 07-23 | 6.678 | teammate | frontier GR-sigma branch |
| `54844628` | 07-20 | 7.891 | ours | fully-owned honest — slot-2 provenance-first fallback |
| `54878409` | 07-21 | 7.953 | ours | excluded (regression) |

## Round 1 (2026-07-26)

**No submission.** Rotation infrastructure built and G1.2 completed with zero quota and zero GPU
(the frontier's own masked-split reports were reused). Round-2 candidate identified:
SP45-projection-only (non-homogeneous, best proxy RMSE) — needs smoke → full before the gate applies.

`54968060` was validated this round as a **genuine no-retrieval run** (`alpha=0.0`, `applied_wells=0`
in the selected prefix profile, plus `guarded_overlap_override: False`), so its 6.643 is a clean
measurement of the frontier without any train-copy lookup.

## Round 2 result (2026-07-26)

**`54990075` = 6.690 COMPLETE** (G2.1 SP45-projection-only, kernel
`joezzzzz/rogii-frontier-sp45-only-full` v1, commit `9f0d6a4`). Today 1/5 used, 4 remaining.

Pre-registered reading resolved to the `> 6.678` branch: **the frontier's post-SP45 stages earn their
place** on the leaderboard, and the local train-copy proxy that favoured SP45-only pointed the wrong way
— an independent confirmation of the G1.2 §3 saturation finding. The submission did its job: it answered
a question that no local evidence could settle.

Slot recommendation after this result (all three criteria converge):
**slot 1 `54922806` (6.563) + slot 2 `54844628` (7.891)** — see
`reports/final_slot_package_corrected_gate_2026-07-26.md`.

## 2026-07-28 (autopilot rounds 4–5)

**Quota used today: 0 of 5.** No submission. Board unchanged since `54990075` (6.690, 07-26).
Deadline 2026-08-05 23:59 UTC.

- Round 4 `live_refresh_and_decision`: state refreshed, queue advanced.
- Round 5 `g35_honest_prefix_calibration`: **closed on evidence, no submission** — the prefix-cut
  calibration prerequisite does not hold once the same-run confound is removed.

- Round 6 `g13_dependency_provenance_audit`: **completed, no submission**. Quota still **0/5 today**.
- Round 7 `g32_learned_alignment_smoke`: **completed, no submission**. Quota still **0/5 today**.

- Round 8 `g33_multi_hypothesis_smoke`: **closed on evidence, no submission**. Quota still **0/5 today**.

- Round 9 `frontier_variant_matrix_lite`: **no submission**, both live axes HOLD. Quota still **0/5 today**.

- Round 10 `new_direction_search`: **no submission** (`can_submit=false`, `max_submit_cost=0`). Quota still **0/5 today**.

- Round 11 `n4_conformal_well_uncertainty`: **no submission** (`can_submit=false`). Quota still **0/5 today**.

- Round 12 `n2_increment_structural_field`: **no submission** (3-well gate fails for both variants). Quota still **0/5 today**.

- Round 13 `n1_geometry_bounded_alignment`: **no submission** (`can_submit=false`, negative result). Quota still **0/5 today**.

- Round 14 `n3_multiscale_gr_matching`: **no submission** (`can_submit=false`, diagnostic). Quota still **0/5 today**.

- Round 15 `n6_public_solution_audit`: **no submission** (`can_submit=false`, survey; named repo 404, substitute audited). Quota still **0/5 today**.

- Round 16 `n5_typewell_fingerprint_families`: **no submission** (`can_submit=false`, diagnostic). Quota still **0/5 today**.

- Round 17 `n8_azimuth_matched_neighbours`: **no submission** (3-well gate fails at every tolerance). Quota still **0/5 today**.

- Round 18 `n7_q3d_tortuosity_features`: **no submission** (`can_submit=false`, gate failed). Quota still **0/5 today**.

- Round 19 `n9_self_correlation_prefix_template`: **no submission** (`can_submit=false`, gate failed). Quota still **0/5 today**. **Queue exhausted** — 19 rounds on 2026-07-28, zero submissions, quota never spent.

- Round 20 `q10_twh1_scorer_dp_candidate`: **no submission** (beats flat but does not narrow the gap to deployed; gate is an AND). Quota still **0/5 today**.

- Round 21 `q11_twh1_pf_seed_ranker`: **no submission** (every ranker arm loses to the PF mean default). Quota still **0/5 today**.

- Round 22 `q12_coverage_gated_self_template`: **no submission** (coverage does not stratify the effect). Quota still **0/5 today**.

- Round 23 `q13_twh1_self_hybrid_emission`: **no submission** (emission gain reverses sign through the DP). Quota still **0/5 today**.

- Round 25 `q14 collect + submit`: **SUBMITTED ref `55064411`** — frontier hedge-OFF
  (`_BH_CAP 2.00 -> 0.00`), kernel `joezzzzz/rogii-frontier-hedgeoff-full` v1, commit `f491826`,
  output sha256 `4eec813b1213c94d`. Quota **1/5**. Audit HARD PASS; non-homogeneous (rmse 1.756 vs
  54968060). **Public score still PENDING at hand-off (~45 min).**

  **Operational fact worth carrying:** this is a **kernels-only** competition, so submitting re-runs the
  kernel against the hidden test set. Scoring latency therefore tracks **kernel runtime (~1 hour)**, not
  the few minutes typical of file submissions. A `PENDING` status at 20-45 minutes is normal here and is
  not evidence of a problem — do not resubmit or assume failure on that basis. Poll on an hour-scale
  cadence.

## 2026-07-29 — `55064411` still PENDING; Q16 round consumed no quota

**Quota: 1/5 used for the day. No submission was made this round.** `q16_honest_twh1_residual_router`
closed on its prerequisite (signed-residual CV R^2 **-0.0802** by well; 3-well bootstrap 5th **-0.9333**)
and therefore never reached a submittable artifact — see
`reports/q16_honest_twh1_residual_router_2026-07-29.md`.

**`55064411`** (Q14 hedge-OFF; kernel `joezzzzz/rogii-frontier-hedgeoff-full` v1; commit `f491826`;
output sha256 `4eec813b1213c94d`) re-checked this round: **`SubmissionStatus.PENDING`, 2 h 20 m+** after
the 2026-07-28 20:30:17 UTC submission, `public_score` empty. This is now **past** the ~1 h
kernel-runtime expectation recorded in `41bb65f`. The carry-forward rule is unchanged — in a
kernels-only competition scoring re-runs the kernel, so PENDING is not itself a failure and is not a
reason to resubmit — but the latency is longer than the recorded expectation and that is worth noting
rather than smoothing over. A background poller remains armed; the score is the FIRST action of the
next round.

Standing scored references for the decision when it lands:

| ref | public | note |
|---|---|---|
| 54922806 | **6.563** | best scored frontier |
| 54968060 | 6.643 | overlap-OFF diagnostic |
| 54896975 | 6.669 | Kaiwalya PF bimodal midpoint repro |
| 54923144 | 6.678 | GR sigma 1.0 PF frontier |
| 54990075 | 6.690 | G2.1 SP45-projection-only |

If `55064411` lands at or below **6.563** it becomes an own-account frontier competitive with the
teammate's best, and the slot-1 recommendation should be re-evaluated on **provenance**.

**Tooling fact recorded for the next round's score check:** the `kaggle` package was missing from the
environment and was reinstalled with `python3 -m pip install --user --break-system-packages kaggle`
(PEP 668 environment). Credentials resolve from `~/.kaggle/access_token`. The API returns **snake_case**
attributes — `s.public_score`, `s.private_score`, `s.status` — not the camelCase names.
