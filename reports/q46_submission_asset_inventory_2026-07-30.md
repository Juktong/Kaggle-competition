# Q46 — submission asset inventory: every field resolved, and one slot-1 artifact found to be unarchivable by API

Date: 2026-07-29 23:55 UTC
Task: `q46_submission_asset_inventory` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Artifacts produced: `reports/submission_outputs/` (5 verified submission files + provenance README)
Outcome: **inventory complete. No submission. Quota 0/5.**
**Headline: `54922806` — the score-first slot-1 candidate — cannot have its submitted output retrieved by
API, because its kernel now returns a different artifact. Evidence in §4; owner action in §6.**

## 1. Method — every field resolved from an authority, not from memory

Prior rounds recorded much of this in prose (Q30 §4, Q38 §2). This round resolves each field from a live
source and labels it, so nothing rests on an earlier report's assertion:

| field | authority |
|---|---|
| ref, public score, date, account, team | `api.competition_submissions()` — live |
| **kernel slug + scriptVersionId** | the submission object's `url` field, e.g. `/code/joezzzzz/rogii-frontier-hedgeoff-full?scriptVersionId=338650633` |
| dataset_sources | `kernel-metadata.json` of the pulled package |
| output submission file | `api.kernels_output(slug)`, then verified against `sample_submission.csv` |
| git commit | parsed from the submission description, then `git cat-file -t` against this repo |

**The `url` field is the material improvement over Q38.** Q38 recovered slug + `scriptVersionId` for the
teammate submissions by a separate route and left our own side implicit. The submission object carries both
directly, for every submission, so all seven candidates are now **known** rather than inferred.

## 2. The inventory

| ref | public | account | kernel slug | scriptVersionId | repo package | datasets | git commit | output archived |
|---|---|---|---|---|---|---|---|---|
| `54922806` | **6.563** | leemarc223 | `leemarc223/rogii-public-pf-frontier-rerun-20260723` | **337355891** | `reports/teammate_kernels/rogii-public-pf-frontier-rerun-20260723` | 7 | **MISSING** | **NO — §4** |
| `54968060` | 6.643 | joezzzzz | `joezzzzz/rogii-kaiwalya-overlap-off-full` | 337787958 | `kaggle_kernel_kaiwalya_overlap_off_full` | 9 | `9857c3a` ✔in repo | **yes, verified** |
| `54844628` | 7.891 | joezzzzz | `joezzzzz/rogii-struct-field-blend-codex` | 336599680 | `kaggle_kernel_struct_field_blend` | 1 | `d972986` ✔in repo | **yes, verified** |
| `55064411` | 6.695 | joezzzzz | `joezzzzz/rogii-frontier-hedgeoff-full` | 338650633 | `kaggle_kernel_frontier_hedgeoff_full` | 9 | `f491826` ✔in repo | **yes, verified** |
| `54990075` | 6.690 | joezzzzz | `joezzzzz/rogii-frontier-sp45-only-full` | 337982098 | `kaggle_kernel_frontier_sp45only_full` | 9 | `dd4e79e` ✔in repo | **yes, verified** |
| `54896975` | 6.669 | leemarc223 | `leemarc223/rogii-kaiwalya-public-tvt-6-626-repro` | 337097140 | `reports/teammate_kernels/rogii-kaiwalya-public-tvt-6-626-repro` (+ `origin/main` `a589fa8`) | 9 | **MISSING** | **yes, verified** |
| `54923144` | 6.678 | leemarc223 | `leemarc223/rogii-gr-sigma-1-0-frontier-20260723` | 337362917 | `reports/teammate_kernels/rogii-gr-sigma-1-0-frontier-20260723` | 7 | **MISSING** | **NO — §4** |

All seven are on team **`lee Marc223`**, `submitted_by` split **4 joezzzzz / 3 leemarc223**.

### Field status (task step 3)

| field | known | inferred | missing | inaccessible |
|---|---|---|---|---|
| ref, score, date, account, team | **7/7** | — | — | — |
| kernel slug | **7/7** | — | — | — |
| scriptVersionId | **7/7** | — | — | — |
| code in repo | **7/7** (4 own packages, 3 pulled teammate packages) | — | — | — |
| dataset_sources | **7/7 for the CURRENT kernel version** | 7/7 for the *submitted* version — see the limit in §5 | — | — |
| git commit | 4/7 | — | **3/7** — the teammate submissions carry no commit id, and this repo is not where they were run | — |
| output submission file | **5/7 verified** | — | **2/7** (`54922806`, `54923144`) | the *submitted-version* output is not reachable by API — §4 |

## 3. The outputs are archived and independently verified

`api.kernels_output()` was used to retrieve each candidate's output; every file was checked against
`data/rogii/sample_submission.csv` — **14,151 rows, id set equal, id order equal, all finite** for all seven.
Five are archived in `reports/submission_outputs/` with a provenance README.

Verification did not stop at "the file parses". Each archived file is tied to its submission by a number
recorded **at submission time**, independently of this round:

```
pairwise RMSE between archived outputs (ft)
             54844628  54896975  54968060  54990075  55064411
54844628        0.000     4.020     2.537     2.601     1.878
54896975        4.020     0.000     3.105     2.989     2.582
54968060        2.537     3.105     0.000     1.640     1.756
54990075        2.601     2.989     1.640     0.000     1.457
55064411        1.878     2.582     1.756     1.457     0.000
```

- `54990075`'s description records *"rmse 1.640 vs 54968060"* → measured **1.640** ✔
- `55064411`'s description records *"rmse 1.756 vs 54968060"* → measured **1.756** ✔
- `54968060`'s description records *"rmse 3.1"* vs the overlap-ON family and *"rmse 2.54"* vs `54844628`
  → measured **3.105** and **2.537** ✔
- `54896975`'s description records *"SHA b192d3"* → archived sha256 is **`b192d3f348ae…`** ✔

So five archived artifacts are confirmed to be the submitted ones, by evidence written before this round
existed.

## 4. The finding — `54922806`'s submitted output is not retrievable, and its kernel has moved

`54922806`, `54896975` and `54923144` scored **6.563 / 6.669 / 6.678**. Their kernels' currently-retrievable
outputs are **byte-identical to each other**:

```
b192d3f348ae00680dc4df942b95cef5fd708c636a741f77dfb6b6e89b9ded4a   54896975  (matches its recorded SHA)
b192d3f348ae00680dc4df942b95cef5fd708c636a741f77dfb6b6e89b9ded4a   54922806  <- cannot be its artifact
b192d3f348ae00680dc4df942b95cef5fd708c636a741f77dfb6b6e89b9ded4a   54923144  <- cannot be its artifact
```

Three different public scores cannot come from one prediction file. The SHA match identifies the shared file
as **`54896975`'s**, so the copies retrieved under the other two refs are **post-submission re-runs**, not
submitted artifacts. They were deleted rather than archived, because a file named `54922806_submission.csv`
that is not `54922806`'s output is worse than no file at all.

**This answers, with evidence, the question Q38 left open.** Q38's message to the teammate asked: *"Have any
of these kernels been edited or re-run after the submissions below?"* The three kernels now converging on one
output is direct evidence that at least two of them have been. It does not require a reply to establish.

**Why it matters beyond bookkeeping.** `54922806` is the **score-first slot-1 candidate**. Under Winner's
Obligations the submitted artifact and the code that produced it must be disclosable, and right now:

- the *code* is archived (Q38 pulled it; Q39 diffed it — pristine base + `*1.3` on the GR sigma at cell 29);
- the *submitted output* is not, and `api.kernels_output` cannot return it because it serves only the latest
  version;
- the specific `scriptVersionId` **337355891** is known, so the artifact is not lost — it is one UI action
  away, but that action is the owner's.

This does **not** change the slot recommendation. Q44 already found the two slot-1 options tied on
measurement, with ownership as the tie-breaker; this adds one more, independent, ownership-flavoured
consideration on the same side, and it is recorded as such rather than presented as decisive.

## 5. Limits

- **`dataset_sources` is read from the current kernel package, not from the submitted version.** Kaggle's API
  exposes metadata for the latest version only. Given §4 shows at least two teammate kernels have moved since
  submission, the dataset list for *those* submitted versions is inferred, not known. For the four `joezzzzz`
  kernels the archived output was verified as the submitted artifact (§3), which makes the current package a
  much safer proxy — but it is still a proxy.
- The three teammate submissions carry **no git commit**, and there is no reason they should: they were not
  run from this repo. The repo package is the substitute, and for `54896975` `origin/main` `a589fa8` also
  holds it.
- `54853492` is excluded by standing instruction. `54777533` is noted only because Q38 recorded its kernel
  belongs to a **third-party account** (`qwer556617123/rogii-prvs-oof-meta-direct-fast`) — a disclosure item
  if it were ever selected, which it is not.
- The archive is 2.3 MB for 5 files; it is committed deliberately, since the whole point is that the artifact
  exists locally and is auditable without a network call.
- `total_bytes` on a submission object (~31 MB) is the **output bundle**, not the CSV (~464 KB). Recorded so
  a future round does not read a size mismatch as corruption.

## 6. Owner actions required (task step 4)

Ordered by how much they matter for the final slots. None can be done by an agent — each needs the owner's
Kaggle session or the teammate.

1. **Retrieve `54922806`'s submitted output** — Kaggle → `leemarc223/rogii-public-pf-frontier-rerun-20260723`
   → Version history → **scriptVersionId 337355891** → Output → download `submission.csv`, and drop it in
   `reports/submission_outputs/`. This is the only missing asset attached to a **recommended slot-1
   candidate**. *(If `54968060` is chosen for slot 1 instead, this becomes optional — its artifact is already
   archived and verified.)*
2. **Ask the teammate to confirm the post-submission state of the three kernels** — Q38's question, now with
   §4's evidence attached: three kernels that scored differently currently emit one identical file. Worth
   asking specifically whether `rogii-public-pf-frontier-rerun-20260723` still contains the `*1.3` GR-sigma
   token that Q39 measured in its pulled source.
3. **Do nothing for `54923144`** unless it becomes a slot candidate. Its artifact has the same gap but it is
   not recommended under any of the four selection views.
4. **Winner's-obligation disclosure lists are already prepared** in Q30 §6 and unchanged by this round:
   `54844628` needs `ravaghi/wellbore-geology-prediction-artifacts`; the frontier candidates need all 9
   attached datasets plus the derivation from the public notebook `kaiwalyaatulraut/rogii-public-tvt-solution`;
   `54922806` needs those plus the teammate-supplied kernel version — **which item 1 above now supplies**
   (scriptVersionId 337355891, recorded here).
5. **One provenance item remains unverified from Q30 §7 and is not closed by this round:**
   `ravaghi/wellbore-geology-prediction-artifacts` ships a `data/train.csv` described in our own kernel as a
   cache. It is required by **both** slots, so it is a team-level disclosure item, not a slot-selection input.

## 7. Next

`q47_final_selection_ui_checklist` is next by priority. `q58_honest_kernel_backward_smoothing` has its NS=64
producer in flight (ETA ~02:50 UTC) and will be collected when it lands.
`q29_final_slot_candidate_packager` reactivates **2026-08-03**; the final selection is due **2026-08-04** and
costs no quota.
