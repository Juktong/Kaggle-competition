# PF-frontier submission source audit — `54896975` / `54922806` / `54923144` (2026-07-23)

Task 2 of the 2026-07-23 queue. Question: where did these three submissions come from, are they
compliant, and are they reproducible from our side?

## Search performed

- Exact refs + keywords (`Kaiwalya`, `b192d3`, `PF frontier`, `hidden-runtime`, `GR sigma`,
  `bimodal midpoint`) across `/home/ubuntu/workstation/JoeProject`, `/home/ubuntu/.claude/projects`,
  `/home/ubuntu/.claude/jobs`, shell history, recent files (−2 days), and the account kernel list.
- Result: the ONLY filesystem hits are **self-references** — this session's own `state.json` /
  transcript, which contain the user's instruction text quoting the refs. **No local artifact, script,
  notebook, or output for any of the three exists on this machine.**
- `joezzzzz` kernel list ends at `rogii-struct-aniso-codex` (2026-07-21 13:13) — **no new kernels** on
  our account after our `54878409`. In a kernels-only competition, these submissions therefore did not
  originate from this account's kernels.

## Origin established

- Leaderboard team entry: **team "lee Marc223", members `joezzzzz` + `leemarc223`**, team best public
  **6.669**, SubmissionCount 69. `competitions submissions` lists TEAM submissions.
- The three new refs follow the teammate's established Codex naming pattern (`Codex … SHA xxxxxx`), the
  same as prior teammate submissions `54777533` and `54853492`.
- `leemarc223`'s recent kernels are **[Private Notebook]** (plus 4 old public forks from June). The
  submitting kernels are private and **cannot be pulled from our side**.

**Conclusion: all three are teammate-side (leemarc223) Codex submissions from private kernels.**

## The claimed source of `54896975` (public 6.669) — located and characterised

Description: `Codex verified Kaiwalya PF bimodal midpoint reproduction SHA b192d3`.

The public notebook exists: **`kaiwalyaatulraut/rogii-public-tvt-solution`** (KAIWALYA RAUT, 104 votes,
last run 2026-07-22 04:50 — ~2.5 h before the submission). Content matches the description: `bimodal`
×140, `midpoint` ×12, `particle` ×44. Pulled copy sha256[:6] `d61a88` (≠ `b192d3`, which presumably
hashes the teammate's pulled version/normalisation; versions change between runs).

Mechanism (from source):
- PF ("gold" profile) + **visible-prefix calibration** (`run_visible_prefix_calibration=True`,
  `visible_prefix_cut_fracs=(0.50,0.65,0.75)`) — self-calibrates on the test wells' known heel prefix;
- **`run_guarded_overlap_override=True` in every profile** — the guarded **overlap** family (exploits
  the test wells being duplicated in train), same family as `54174151`/`54289934`;
- bimodal detector + midpoint handling (midpoint of PF modes under bimodal posteriors — the RMSE-optimal
  choice under mode uncertainty);
- optional "model package correction" from third-party artifacts.
- `enable_internet: false`; **9 external Kaggle dataset_sources**, including other competitors' shared
  model artifacts (`pilkwang/rogii-model-package`, `chesnikovleonid/rogii-v50-dwt-phaseb-modelonly`,
  `fleongg/rogii-claude-models-pub`, `nina2025/rogii-03`, `thbdh5765/rogii-v10/v11`,
  `needless090/rogii-tabicl-mirror`, `phongnguyn23021656/koolbox-offline`, plus the standard artifacts
  dataset). No pip installs / network fetches.

## The two pending (`54922806`, `54923144`)

Descriptions: `Codex public PF frontier independent hidden-runtime rerun 20260723` and
`Codex GR sigma 1.0 PF frontier independent hidden-runtime branch 20260723`. The public-kernel scene now
contains a dense "public frontier" family (e.g. `ROGII Public Score Frontier Lab`, `Ultimate PF GS130
Public Repro`, `Public 6.451 Base`, `6.594 PF branch continuation`, `P100 Cap2.5 Measured 6.667`,
`CTRL … Branch Shape Exact`), several of which use **runtime-branch** constructions (behave differently
in the hidden rerun). The pending pair are teammate Codex reruns/branches of that family. Their exact
private kernels are not visible; still PENDING at 10:25 UTC (submitted 08:03 / 08:21).

## Compliance and reproducibility assessment

| question | answer |
|---|---|
| kernels-only path | yes (all team submissions are kernel-backed by construction) |
| external data | **public Kaggle datasets only** (9 third-party artifact datasets; no internet). Public sharing is the standard Kaggle-legal channel; our project rule requires noting this dependency explicitly. |
| overlap usage | yes — `run_guarded_overlap_override=True`; LB-legal, private-transfer is the known open risk of the overlap family |
| runtime-branch ("hidden-runtime") | present in the pending pair's descriptions; this family conditions on the rerun environment. LB-common in this competition; flagged as a **compliance-gray** construction to be confirmed by the final-selection owner |
| reproducible bit-exact from our side | **No** (private teammate kernels; SHA refers to their copy) |
| reproducible in substance | **Yes** for `54896975`: the public Kaiwalya notebook + its 9 public dataset deps are pullable and rerunnable from our account |
| relation to this repo/PR | none — no commits, files, or kernels of ours are involved |

## Disposition

- `54896975` (6.669) is the **team's current best-public**; treated as teammate-line, substance-
  reproducible, LB-legal, with the overlap family's known private-transfer risk.
- The pending pair are polled (watcher running; results go to `reports/submission_ledger_2026-07-23.md`).
- Per the standing directive, our honest line does not build decisions *around* teammate submissions;
  the final-slot implications are recorded in `reports/final_slot_package_corrected_gate_2026-07-23.md`.
