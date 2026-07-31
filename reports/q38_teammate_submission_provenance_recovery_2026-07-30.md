# Q38 — teammate submission provenance recovery

Date: 2026-07-29 16:30 UTC
Task: `q38_teammate_submission_provenance_recovery` (`requires_gpu=false`, `can_submit=false`, `max_submit_cost=0`)
Outcome: **complete. No submission. Quota 0/5.**

## 0. The owner's question, answered

> *"Do we have all teammate solution data?"*

**Yes.** Every teammate submission's exact kernel slug **and** the `scriptVersionId` that produced it are
exposed by the submissions API, and **every one of those kernels pulls successfully from this account**
(notebook source + `kernel-metadata.json`, including `dataset_sources`). Nothing had to be inferred, and
nothing needs to be requested — with one small confirmation item in §7.

**This corrects Q30.** That audit recorded an "actionable gap — we have not audited `54922806` ourselves;
its kernel slug, version and dataset list are not in this repo, only its description string", and told the
owner to request them from the teammate. The slug and version were available from the API all along, and
the code is directly pullable. The request is unnecessary.

## 1. Live refresh

`git fetch juktong` / `origin` → ok; `origin/main` at `a589fa8`. Kaggle: **20 submissions** on the team
account, split **`joezzzzz` 11 / `leemarc223` 9**. Quota 0/5 used today.

## 2. Evidence table — every teammate-side submission

All four required refs, plus the two other `leemarc223` entries in the scored band, and the one submission
run from a **third-party** account. "Pulled" = notebook + metadata retrieved this round.

| ref | public | submitted_by | kernel slug | scriptVersionId | datasets | code accessible | repo package |
|---|---|---|---|---|---|---|---|
| **`54922806`** | **6.563** | `leemarc223` | `leemarc223/rogii-public-pf-frontier-rerun-20260723` | 337355891 | **7** | **pulled** | no |
| `54896975` | 6.669 | `leemarc223` | `leemarc223/rogii-kaiwalya-public-tvt-6-626-repro` | 337097140 | **9** | **pulled** | **yes** — `origin/main` `a589fa8` |
| `54923144` | 6.678 | `leemarc223` | `leemarc223/rogii-gr-sigma-1-0-frontier-20260723` | 337362917 | **7** | **pulled** | no |
| `54853492` | 7.360 | `leemarc223` | `leemarc223/rogii-safe-mha140-contactmean-v66` | 336687235 | 3 | **pulled** | no |
| `54753209` | 7.482 | `leemarc223` | `leemarc223/rogii-true7182-zero-contact-spatial-balanced` | 335616794 | — | listed | no |
| `54777533` | 7.921 | `leemarc223` | **`qwer556617123/`**`rogii-prvs-oof-meta-direct-fast` | 335598801 | 7 | **pulled** | no |
| `54710185` | 8.864 | `leemarc223` | `leemarc223/rogii-sunny-pf90-beam-mean10-test-only` | 334953497 | — | listed | via `kaggle_kernel_henry_v10_sunny80_blend` |

Note `54777533`: submitted by `leemarc223` but the kernel belongs to a **third-party account**
(`qwer556617123`), not to our team. Recorded for the disclosure list; no decision is taken on it.

`54853492` is included here **only** as provenance bookkeeping, which is what this task asks for. No
decision of any kind is made about it, per the standing instruction.

## 3. Suspected family, per candidate

All of `54922806`, `54896975`, `54923144` are the **Kaiwalya frontier** family. Confirmed structurally,
not guessed — normalised (comments and whitespace stripped) cell-by-cell against our pristine base
`kaggle_kernel_kaiwalya_public_tvt_6626_repro`:

```
54922806 (6.563)   cells base=45 theirs=45 | positionally identical 44
    cell 29  insert   ours=''  theirs='*1.3'
54896975 (6.669)   cells base=45 theirs=45 | positionally identical 45
54923144 (6.678)   cells base=45 theirs=45 | positionally identical 45
```

## 4. The distinction the task asks for — they are **not** the same run

| | `origin/main` 6.626 repro package | our best 6.563 run |
|---|---|---|
| submission | `54896975`, public **6.669** | `54922806`, public **6.563** |
| kernel | `leemarc223/rogii-kaiwalya-public-tvt-6-626-repro` | `leemarc223/rogii-public-pf-frontier-rerun-20260723` |
| scriptVersionId | 337097140 | **337355891** |
| datasets | **9** | **7** |
| code vs pristine base | **identical** | base **+ `*1.3`** |
| in repo | **yes** (`a589fa8`) | **no** |

So the package Mark committed to `origin/main` reproduces the **6.626 public notebook**, and its own run
scored 6.669. It is **not** the 6.563 run. The 6.563 kernel is a different kernel, with a smaller dataset
list, and it carries a one-token modification.

## 5. Headline — our best public submission is the `*1.3` GR-sigma variant

**`54922806` = pristine Kaiwalya base + `*1.3` on the PF likelihood's GR noise sigma**, in code cell 29 —
*the identical one-token change* Q19 found in the public `leonidzaporozhets/new-strategy-score-6-213`
kernel, and the same knob Q36 measured on our honest line.

Three consequences:

1. **The team has already banked this change on the frontier line.** Our slot-1 candidate *is* the
   GR-sigma variant. Closing `q37_frontier_gr_sigma_public_repro` last round was correct, and for a
   stronger reason than recorded: it would have been a **near-duplicate of `54922806`**, which the submit
   gate forbids outright.
2. `54923144`'s description, "GR sigma **1.0**", is now legible — 1.0 is the *unmodified* multiplier, and
   its code is indeed byte-identical to base. The description was accurate.
3. Q36's rejection of the multiplier is **not** contradicted. Q36 measured it inside our **honest DWT+PF
   blend**; `54922806` applies it inside the **frontier**. Different pipelines, so the results are not in
   conflict.

## 6. A controlled run-to-run pair the team already had, unrecorded

`54896975` and `54923144` are **normalised-identical code** run on different days:

```
54896975  2026-07-22  9 datasets  ->  6.669
54923144  2026-07-23  7 datasets  ->  6.678
                                      -----
run-to-run spread on identical code    0.009
```

The two extra datasets in `54896975` are `thbdh5765/rogii-v11-fresh-artifacts` and
`chesnikovleonid/rogii-v50-dwt-phaseb-modelonly`, both of which G1.3 classified as **vestigial** (zero
source references, zero log appearances) — and the 0.009 spread is consistent with that classification.

Against this pair, the `*1.3` variant scores 6.563, i.e. **0.106–0.115 better**, roughly **12×** the
observed same-code spread.

### This does not overturn Q18, and the two must not be conflated

Two different quantities are involved, and both hold:

- **0.009 = measurement precision** — how tightly the *same code* reproduces on the *same 3 public wells*.
  It says the public number is a precise instrument.
- **Q18's ~45% reversal at gaps ≤ 0.30 = generalisation** — how often *two different models'* ranking
  flips on a *different* 3-well draw. It says the public number does not generalise.

A precise instrument can still measure a quantity that does not transfer. So the frontier's `*1.3` gain of
~0.11 is **real on the public wells** and is still **not evidence about novel wells**.

It does, however, sit awkwardly beside the recorded **config-variance floor of ~0.115** (from A1), which
this pair suggests may be far too large for this pipeline. The two measurements are not the same
experiment and this round does not resolve them; flagged for reconciliation rather than silently replacing
the recorded figure.

## 7. What is still missing, and the message to send

Only one item, and it is a confirmation rather than a gap: **`kernels_pull` returns each kernel's *current*
version**, and it could not be independently confirmed that the current version equals the
`scriptVersionId` that produced each submission (a teammate's private kernel versions are not listable
from this account). If a kernel was edited after its submission, the pulled source would differ from the
submitted source.

Suggested message to the teammate:

> Hi — for the final-submission paperwork I've recovered everything from the Kaggle API and can pull all
> the kernels, so I don't need code or dataset lists from you. One confirmation only:
>
> Have any of these kernels been **edited or re-run after** the submissions below? If so, could you tell me
> the version each one was at on that date (or just leave them untouched until 2026-08-05)?
>
> - `rogii-public-pf-frontier-rerun-20260723` → submission 54922806, 2026-07-23 08:03 UTC (scriptVersionId 337355891)
> - `rogii-kaiwalya-public-tvt-6-626-repro` → submission 54896975, 2026-07-22 07:24 UTC (337097140)
> - `rogii-gr-sigma-1-0-frontier-20260723` → submission 54923144, 2026-07-23 08:21 UTC (337362917)
> - `rogii-safe-mha140-contactmean-v66` → submission 54853492, 2026-07-20 12:32 UTC (336687235)
>
> Also worth knowing: submission 54777533 ran `qwer556617123/rogii-prvs-oof-meta-direct-fast`, a kernel on
> a **third-party account**. If we finish in the money that needs disclosing — do you have its provenance?

## 8. Effect on the final slots — none

The recommendation is unchanged: `54922806` + `54844628` (score-, diversity-, provenance-first) or
`54968060` + `54844628` (our-account-first). What changes is that **slot 1's provenance is now fully
documented**: exact kernel, exact version, exact 7-dataset list, and a structural diff showing it is the
pristine public base plus one token. The Q30 provenance caveat on `54922806` is **closed**.

## 9. Limits

- Version-currency caveat in §7 — the one genuinely open item.
- The `*1.3` finding is a **structural** diff, not a rerun. It was not re-executed to confirm the score.
- Dataset **licences** remain unverified (the API version here does not expose the field); only public
  listability was confirmed.
- The 0.009 pair is **two runs**. It is a direct observation, not a distribution.

## 10. Next

Queue is otherwise empty until `q29_final_slot_candidate_packager` reactivates on **2026-08-03**. The
selection action itself remains due by **2026-08-04** and costs no quota.
