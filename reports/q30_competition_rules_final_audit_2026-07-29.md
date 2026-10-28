# Q30 — competition rules and provenance final audit

Date: 2026-07-29 07:15 UTC
Task: `q30_competition_rules_final_audit` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Outcome: **audit complete. No submission — the task forbids one. Quota untouched at 0/5.**
**One time-critical finding (§2) and one correction to standing project language (§4.1).**

## 1. What was and was not accessible

- **Official rules page** — `https://www.kaggle.com/competitions/.../rules` returned only the page title.
  It is an authenticated JavaScript SPA, so the rules text is **not machine-readable from here**.
  Recorded as a blocker rather than worked around; the same limitation is already noted in
  `reports/lessons_and_strategy_2026-07-08.md` §15 ("rules page JS/auth-gated").
- **Competition metadata via the API** — fully accessible and authoritative for the operational rules.
- **Repo rule notes** — `reports/external_data_ssl_direction_2026-07-15.md` carries the previously
  transcribed rule basis, and `reports/frontier_dependency_provenance_audit_2026-07-28.md` (G1.3) the
  dependency audit. Both were re-read.

## 2. TIME-CRITICAL — two deadlines fall **today**

```
merger_deadline        2026-08-05 -> NO: 2026-07-29 23:59
new_entrant_deadline                    2026-07-29 23:59
submission deadline                     2026-08-05 23:59
```

**Team-merger and new-entrant deadlines are 2026-07-29 23:59 UTC — about 16.7 hours from now.** After
today, team composition is frozen for the remainder of the competition. This is surfaced because it is
irreversible and expires today; no action is recommended here, it is the owner's call, but it cannot be
taken after tonight.

## 3. Operational rules, from the API (authoritative)

| field | value | our compliance |
|---|---|---|
| `is_kernels_submissions_only` | **True** | all submissions via `competition_submit_code` — compliant |
| `max_daily_submissions` | **5** | matches the Q33 budget; 0/5 used today |
| `max_team_size` | 5 | n/a |
| `deadline` | 2026-08-05 23:59 | Q33 plan targets selection by 08-04 |
| `evaluation_metric` | **"Mean Squared Error"** | see the caveat below |
| `category` / `reward` | Featured / 50,000 USD | Winner's Obligations apply — see §6 |
| `team_count` | **5,886** | |
| `user_rank` | **1277** | |

### 3.1 Our precise standing

**Rank 1277 of 5886 teams.** Q19 could only establish "outside the top 200" because the leaderboard API
caps a page at 200 rows. This is the exact figure and supersedes that bound.

### 3.2 A caveat on the metric label

The API labels the metric **"Mean Squared Error"**, while every project report treats the leaderboard
number as being on the same scale as our local **RMSE**. The empirical correspondence says the reports
are right and the label is loose:

```
candidate                       local (RMSE)   public
DWT deterministic base              9.487       9.823
DWT+PF honest blend                 9.2969      8.080
honest + structural field           8.8626      7.891
```

If the leaderboard were a true squared error, public would be roughly the square of these (≈ 78), not
within ~1 of them. So comparing local RMSE against public scores on one axis — which the ledger and the
final-slot package both do — is **sound**. Recorded because the label discrepancy would otherwise be a
latent trap for anyone reading the API field literally.

## 4. Candidate audit

### 4.1 `54844628` — honest line, public 7.891, our account

**A correction to standing project language.** The final-slot package and several reports describe this
candidate as **"fully owned"**. Its kernel (`joezzzzz/rogii-struct-field-blend-codex`) attaches one
third-party public dataset, and that dataset is **load-bearing, not vestigial**:

```json
"dataset_sources": ["ravaghi/wellbore-geology-prediction-artifacts"],
"enable_internet": false
```

```python
assert (CFG.artifacts_path/'models'/'lightgbm-1').exists(), 'artifacts models not found under /kaggle/input'
assert (CFG.artifacts_path/'data'/'train.csv').exists(),   'artifacts data/train.csv not found (would trigger 7GB rebuild)'
```

Hard asserts — the run fails without it. It supplies prebuilt LightGBM/DWT artifacts and a cached
`data/train.csv` so the kernel fast-loads instead of retraining.

The accurate description is therefore:

| aspect | status |
|---|---|
| pipeline code | **fully owned** — built and audited in this repo |
| validation | **fully owned** — 760-well nested OOF + bootstrap, 100% positive |
| runtime dependency | **one** third-party public Kaggle dataset, **required** |

This does **not** change the slot recommendation, and it is **not** a rules problem — the dataset is
public and equally accessible, which is the operative criterion. It changes only how the candidate should
be *described*: "fully owned pipeline with one shared public artifact dependency", not "fully owned".

**Risk category: public-derived but documented (low residual risk).**

### 4.2 `54968060` (6.643) and `55064411` (6.695) — frontier, our account

Both run `joezzzzz/rogii-kaiwalya-overlap-off-full` / `joezzzzz/rogii-frontier-hedgeoff-full`, each
attaching **9 datasets**, `enable_internet: false`. Per G1.3, the surface is much narrower than 9:

| class | count | datasets |
|---|---|---|
| affects predictions, **shared with our honest line** | 1 | `ravaghi/wellbore-geology-prediction-artifacts` |
| affects predictions, **frontier-specific** | **1** | `fleongg/rogii-claude-models-pub` (learned-trajectory, blend weight 0.40) |
| runtime only (offline pip wheels) | 1 | `phongnguyn23021656/koolbox-offline` |
| loaded, contribution **guard-rejected at runtime** | 1 | `pilkwang/rogii-model-package` |
| **vestigial** — zero source references, zero log appearances | 5 | `nina2025/rogii-03`, `thbdh5765/rogii-v10-fresh-artifacts`, `thbdh5765/rogii-v11-fresh-artifacts`, `chesnikovleonid/rogii-v50-dwt-phaseb-modelonly`, `needless090/rogii-tabicl-mirror` |

The pipeline derives from the public notebook `kaiwalyaatulraut/rogii-public-tvt-solution`. Reusing a
public Kaggle notebook is ordinary and permitted; it is a **disclosure** item, not a compliance one.

**Risk category: public-derived but documented, with a provenance caveat** (one third-party model
artifact materially affects predictions).

### 4.3 `54922806` — best public 6.563, **teammate account**

Same frontier family. It is a legitimate submission by a member of our own team, so it is selectable.
The gap is that **we have not audited its kernel ourselves** — its exact kernel slug, version, and dataset
list are not in this repo, only its description string.

**Risk category: provenance caveat — actionable.** If this candidate is selected for a final slot, obtain
from the teammate: kernel slug, version number, and the full `dataset_sources` list, and record them in
the ledger. That information would be required under Winner's Obligations (§6) and cannot be reconstructed
after the deadline.

### 4.4 New Q candidates

**None.** Q16 (closed on prerequisite), Q17 (HOLD), Q18 (decision task), Q19 (gate failed), Q21 (closed)
produced no submittable candidate. `q36_gr_sigma_in_blend_oof` is **still in flight** (446/760 wells at
124 min; ~1.5 h remaining) and `q37` remains blocked behind it.

## 5. Risk summary

| candidate | public | account | category |
|---|---|---|---|
| `54844628` | 7.891 | ours | **public-derived but documented** (low) — one required public artifact dataset |
| `54968060` | 6.643 | ours | **public-derived but documented + provenance caveat** |
| `55064411` | 6.695 | ours | same as `54968060`; **enters no slot** (worst frontier on public) |
| `54922806` | 6.563 | teammate | **provenance caveat — actionable**: obtain kernel version + dataset list |
| `54878409` | 7.953 | ours | **not recommended** — measured public regression, already excluded |
| `54853492` | 7.360 | teammate | **excluded from this audit by standing instruction** |

**Nothing is categorised "not recommended" on rules grounds.** Every candidate in the recommended pairs is
compliant under the documented basis: external data and pretrained models are permitted provided they are
publicly available and equally accessible to all participants at no cost, and all attached datasets are
public Kaggle datasets, with every kernel running `enable_internet: false`.

## 6. Winner's Obligations — the disclosure list, prepared now

If the team finishes in the money, all external data, code and model weights must be disclosed. Assembling
this after the deadline would be harder, so the list is recorded now.

**If `54844628` is selected:** `ravaghi/wellbore-geology-prediction-artifacts` (required — prebuilt
LightGBM/DWT artifacts + cached `data/train.csv`); all other code owned and in this repo.

**If `54968060` / `55064411` is selected:** all **9** attached datasets should be disclosed — including
the 5 vestigial ones, since they are attached at runtime even though they affect nothing — plus the
derivation from the public notebook `kaiwalyaatulraut/rogii-public-tvt-solution`.

**If `54922806` is selected:** the above **plus** the teammate-supplied kernel version and dataset list
(§4.3).

**Recommendation on the vestigial datasets:** leave them attached. Removing them would require a fresh
frontier run and a quota slot, and Q33 established that slots buy nothing inside the current noise band.
Disclose all nine instead — that costs nothing and is accurate.

## 7. Open verification item

`ravaghi/...artifacts` ships a `data/train.csv`. It is described in our own kernel as a cache that avoids
a "7GB rebuild", i.e. derived from the competition data. **This was not verified by inspecting the
dataset's contents** — doing so needs a download that was not performed in this round. The item is
low-risk (the dataset is public, widely used, and the file is used to skip retraining) but it is the one
unverified link in the honest line's provenance, and it is recorded rather than assumed.

## 8. Limits

- The official rules text was **not** retrieved this round (§1); §3 rests on API metadata, and the
  external-data clause on the transcription in `external_data_ssl_direction_2026-07-15.md`. If an exact
  clause matters for a decision, it should be read from a logged-in browser.
- Dataset **licence** fields are not exposed by this API version, so licences were not individually
  verified — only that each dataset is public and listable.
- `user_rank` 1277 is the public-leaderboard rank; the private ranking is not visible and is the actual
  objective.

## 9. Next

Collect `q36_gr_sigma_in_blend_oof` (~1.5 h), then `q35_status_summary_for_owner`.
