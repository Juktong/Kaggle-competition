# Q47 — final selection checklist: doing nothing loses the honest slot under *every* plausible default

Date: 2026-07-30 00:05 UTC
Task: `q47_final_selection_ui_checklist` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Outcome: **checklist below. No submission, no selection made. Quota 0/5.**
**Headline: `54844628` ranks 9th of our 20 submissions by public score, so both plausible Kaggle
auto-selection rules exclude it. Q44 priced that exclusion at +0.40 ft mean / +0.87 ft tail. The selection is
a manual UI action and it is the single highest-value zero-cost action left in this competition.**

## 1. The mechanism — UI only, and its state is not readable by API

Probed rather than assumed. The installed Kaggle API exposes **no final-selection endpoint**: the only
selection-shaped symbols are `_select_models_interactively` (a private helper for model uploads, unrelated),
`competition_leaderboard_*`, and `competition_team_submissions(team_id: int)`. Nor is there any flag to read
the current state — `ApiSubmission` carries exactly:

```
date, description, error_description, file_name, private_score, public_score, ref, status,
submitted_by, submitted_by_ref, team_name, total_bytes, url
```

**There is no `selected` / `is_final` field.** `team_public_submission_fields` is `['id','dateSubmitted','publicScore']` — also no selection flag.

Two consequences, both stated as limits rather than worked around:

1. **The selection cannot be made by an agent or by CLI.** It is a browser action by the owner. (Q47 step 4
   also forbids an agent doing it, so this is not a blocker — but it does mean no automation can stand in.)
2. **The selection cannot be verified programmatically.** Nothing in this repo, and no command in this
   session, can confirm which two submissions are currently marked. **The owner must confirm visually.** Any
   future report claiming "selection verified" without a screenshot or the owner's word is unfounded.

Competition facts refreshed live at 2026-07-30 00:00 UTC:

```
deadline                     2026-08-05 23:59:00 UTC
is_kernels_submissions_only  True
max_daily_submissions        5        submissions_disabled  False
max_team_size                5        team_count  5930      our rank  1354
```

## 2. THE WARNING — the default excludes our slot-2 line under either rule

Kaggle's competition rules language (surfaced via search; the competition's own `/rules` page is behind a
login wall and could not be retrieved) defines a Final Submission as *"the Submission selected by the user,
**or automatically selected by Kaggle in the event not selected by the user**"*. So an automatic selection
**will** happen if the owner does nothing.

The exact default criterion is **not** established from an authoritative source — community answers say
best-public-score, and that is marked here as unverified. **It does not matter**, because both candidate
rules produce the same failure:

```
"best public 2"   -> 54922806 (6.563) + 54968060 (6.643)     both FRONTIER family
"most recent 2"   -> 55064411 (2026-07-28) + 54990075 (2026-07-26)   both FRONTIER family

54844628 (7.891) ranks 9th of our 20 submissions by public score
```

**Under either default, `54844628` is not selected.** That is the whole risk in one line, and it is robust
to the ambiguity about which rule applies.

### What that costs, measured

Q44 evaluated pairs under the draw rather than as point estimates (H-hidden, measured cell):

| pair | mean | p95 (bad tail) |
|---|---|---|
| `54922806` + `54844628` (diverse — recommended) | **6.1818** | **8.5017** |
| `54922806` + `54968060` (**the best-public default**) | 6.5783 | 9.3671 |
| **cost of accepting the default** | **+0.3965** | **+0.8654** |

For scale, the entire slot-1 dispute this project has spent three rounds on is worth **≤ 0.077 ft**. The
default-vs-diverse gap is **five times larger**, and it is avoidable at zero quota cost by clicking twice.

The mechanism, from Q44: best-of-2 keeps the *better* of the two on private, so it is a call option on
variance — two frontier members fail together (family diversity 0), while `54844628` is the only submission
we hold whose error is decorrelated from the crowd (2.54 ft output disagreement; it beats the frontier on
~29% of random 3-well draws). A second frontier member is worth −0.060 against slot 1 alone; the honest line
is worth −0.456.

## 3. Owner checklist

**Deadline**

| | UTC | Beijing (UTC+8) |
|---|---|---|
| hard deadline (selection must be done before this) | **2026-08-05 23:59** | **2026-08-06 07:59** |
| recommended completion (Q33: a full day early) | **2026-08-04 12:00** | **2026-08-04 20:00** |

**Steps**

1. Open the competition **Submissions** page:
   `https://www.kaggle.com/competitions/rogii-wellbore-geology-prediction/submissions`
   Make sure you are on the **team** view (team `lee Marc223`) — the pair must include one `leemarc223`
   submission if you choose the score-first policy, and teammate submissions only appear in the team list.
2. Find the two target rows by **ref id** (the table also shows the description; match on the id, not the
   score, since several scores are close). Refs and their identifying descriptions:
   - `54844628` — *"DWT+PF blend + group-anchored cross-well structural field (gated)"*, public 7.891
   - `54968060` — *"overlap-OFF diagnostic … guarded_overlap_override FORCED OFF"*, public 6.643
   - `54922806` — *"Codex public PF frontier independent hidden-runtime rerun 20260723"*, public 6.563
3. On each of the two chosen rows, use the row's **"Use for Final Score"** control — in the current UI this
   is either a checkbox/toggle in the row or an item in the row's **⋮** (three-dot) menu. **The label wording
   changes between Kaggle UI revisions**, so look for the control that mentions *final*, and do not assume a
   specific label.
4. **Verify the count.** The page shows how many are selected (e.g. *"2 of 2 selected"*). It must read **2**,
   and the two highlighted rows must be exactly the intended refs. If a third is marked, un-mark it — Kaggle
   will not let you exceed 2, and a stale earlier selection may already be occupying a slot.
5. **Re-open the page after a hard refresh** and confirm the same two rows are still marked. This is the only
   verification available (§1: no API read), so do it once, deliberately.
6. Record what was selected, with the UTC timestamp, in `reports/submission_ledger_2026-07-26.md`. Nothing in
   this repo can confirm it otherwise.

**Which two refs, by policy**

| policy | slot 1 | slot 2 | note |
|---|---|---|---|
| **score-first** | `54922806` (6.563, teammate) | `54844628` (7.891, ours) | best public number on the board; needs the §4 asset action |
| **diversity-first** | `54922806` **or** `54968060` | `54844628` | Q44: the diverse pair is the largest positive term in the decision |
| **ownership / provenance-first** | `54968060` (6.643, ours) | `54844628` (7.891, ours) | **recommended default** — see §4 |
| ~~Kaggle auto-default~~ | ~~`54922806`~~ | ~~`54968060`~~ | **do not accept** — costs +0.40 mean / +0.87 tail (§2) |

**All three policies put `54844628` in slot 2.** The only open question is slot 1, and Q44 found the two
options tied on measurement (their 0.080 public gap is 2.7 sd of the measured 0.03 noise floor, and its only
resolvable component — the GR-sigma term — was measured by Q36 as helping just 42.1% of wells with a negative
median). So slot 1 is an ownership judgement, not a score judgement.

## 4. Fallback if teammate provenance is unavailable

Q46 found this is **not hypothetical**. The three teammate kernels scored 6.563 / 6.669 / 6.678 yet now
return byte-identical output, so at least two have been re-run since submission, and **`54922806`'s submitted
artifact is not archived and cannot be fetched by API** (`kernels_output` serves only the latest version).

**Fallback, and it is cheap:** choose **`54968060` + `54844628`**. Both are `joezzzzz`, both artifacts are
already archived and verified in `reports/submission_outputs/`, both have a git commit in this repo
(`9857c3a`, `d972986`), and Q44 priced the switch at **+0.0013 ft in the evidence-supported cell** — free to
three decimals — with a worst case of +0.077 across all 24 modelled scenarios.

**If you prefer `54922806` for slot 1**, one action is outstanding before the deadline:
Kaggle → `leemarc223/rogii-public-pf-frontier-rerun-20260723` → **Version history** →
**scriptVersionId 337355891** → **Output** → download `submission.csv` into
`reports/submission_outputs/54922806_submission.csv`. This is needed for Winner's Obligations, not for the
selection itself — **the selection works regardless**; the asset gap is a disclosure risk, not a blocker.

## 5. CLI / screenshot alternatives

- **CLI: none.** §1 established there is no endpoint. `kaggle competitions submissions -c
  rogii-wellbore-geology-prediction` lists submissions and is useful for reading refs and scores, but it
  cannot select and cannot show what is selected.
- **Screenshots: none available.** This session cannot log into the Kaggle web UI, so no screenshot of the
  actual page can be produced. §3 therefore describes what to *look for* rather than asserting exact labels —
  recorded as a limitation instead of inventing a UI walkthrough.

## 6. Limits

- The competition's own `/rules` page could not be retrieved (login wall), so the rules quote in §2 is
  Kaggle's general competition-rules language via search, not this competition's page. **Q30 recorded the
  same gap and it remains open.** What *is* firm: an automatic selection happens if the user does not choose.
- The default *criterion* is unverified (§2). The checklist is built so that this does not matter.
- The UI labels in §3 are from Kaggle's general submissions-page pattern, not from an observed screenshot of
  this competition.
- Selection state is unverifiable from here (§1). Steps 5 and 6 exist because of that.
- Ranks and team counts drift daily: 1277 (Q19) → 1339 (Q45) → **1354** now, with our own score unchanged.

## 7. Next

`q48_reopen_deferred_value_check` is next by priority. `q58_honest_kernel_backward_smoothing`'s NS=64
producer is in flight (ETA ~02:50 UTC) and will be collected when it lands — if it clears the submit gate the
honest line improves, which strengthens slot 2 rather than changing any of the above.
`q29_final_slot_candidate_packager` reactivates **2026-08-03**.

Sources for §2's rules language: [Kaggle competition rules pages](https://www.kaggle.com/competitions/olympiad-guide-1/rules),
[Does Kaggle pick the last submission or the best public LB one as final?](https://www.kaggle.com/discussions/general/19028),
[Getting Started on Kaggle](https://www.kaggle.com/docs/competitions-setup).
