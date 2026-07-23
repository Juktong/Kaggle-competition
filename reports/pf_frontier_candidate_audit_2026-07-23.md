# PF-frontier candidate audit — `54896975` as team best-public (2026-07-23)

Task 4. Why 7.891 → 6.669, what family it is, and what its private risk looks like. Constraints:
the submitting kernels are teammate-private, so a direct prediction/artifact diff is **not possible**
from this machine; this audit is mechanism-level from the located public source
(`kaiwalyaatulraut/rogii-public-tvt-solution`) plus our own measurements.

## Why 7.891 → 6.669 — decomposition by family mechanics

The Kaiwalya-family pipeline adds, relative to our `54844628`:

1. **Guarded overlap override** (`run_guarded_overlap_override=True`): where a test well is identified
   as duplicated in train, override predictions with (guarded) train-derived values. Same family as the
   earlier overlap submissions `54174151` (7.182) / `54289934` (7.212), which already beat our honest
   7.891 on public — establishing that the overlap mechanism alone is worth ≈ 0.7 on public.
2. **Visible-prefix calibration** (`cut_fracs 0.50/0.65/0.75`): self-calibrates each test well on its own
   known heel prefix by simulated cuts — a per-well tune that generic pipelines don't do.
3. **PF with bimodal detection + midpoint**: under a bimodal structural posterior, predicting the mode
   midpoint is the RMSE-optimal point estimate; this removes the large "wrong-branch" losses that a
   unimodal PF incurs.
4. Optional third-party "model package" correction (public shared artifacts).

Steps 1–2 exploit **visible-set structure** (duplication in train, known prefix); step 3 is a genuine
methodological improvement; step 4 is ensemble-with-public-artifacts. The 6.669 therefore mixes
LB-specific mechanisms with real modelling gains, and the mix cannot be separated without their CSV.

## A framework correction this audit forces (recorded honestly)

The pending descriptions ("hidden-runtime rerun/branch") and the public frontier family's constructions
imply the kernels-only **rerun may mount a hidden test set different from the visible `test/` (3
wells)**. That is consistent with the project's standing framing (CLAUDE.md: private ranking = **novel
wells**), and it conflicts with the 2026-07-22 inference — drawn from the visible directory — that
"public/private are row splits of the same 3 wells". Both hypotheses are now on record:

- **H-visible**: scoring = row splits of the 3 visible wells. Supported by: submission row count equals
  exactly those wells' toe rows. Under H-visible, prefix-calibrated/overlap methods calibrate on the
  scored wells themselves, and public ≈ private.
- **H-hidden**: the rerun scores a hidden, larger novel-well set. Supported by: "hidden-runtime" branch
  constructions across the public frontier, the CLAUDE.md framing, and the otherwise-unexplained scale
  gap (our all-visible-rows RMSE 3.68 vs public 7.891, with no row subset reaching 7.891).

Under H-hidden, the local-truth-space puzzle of 2026-07-22 resolves: public is computed on wells we
cannot see, so no visible-row subset reproduces it — and the 760-well OOF regains status as the natural
proxy for the hidden set, while overlap/prefix tricks contribute little there (no duplication for truly
novel wells; the guarded override falls back to the base pipeline).

## Private-risk profile of `54896975`

| risk axis | assessment |
|---|---|
| overlap contribution | Under H-hidden: inert on novel wells (guarded fallback) → private reverts toward the fallback pipeline's quality. Under H-visible: carries over. |
| prefix calibration | Under H-hidden: applies to any well with a known heel (novel wells too) — legitimate transfer. Under H-visible: tuned on scored wells. |
| bimodal midpoint | Transfers under both hypotheses — a genuine RMSE improvement mechanism. |
| third-party artifacts | Public datasets; reproducibility dependency (9 packages), not a scoring risk per se. |
| runtime-branch (pending pair) | Conditions on the rerun environment — compliance-gray; flagged to the final-selection owner. |
| reproducibility | Substance-reproducible from the public notebook + public deps; teammate's exact submission not reproducible from here (private kernel). |

## Disposition

- `54896975` (6.669) is the **team best-public** and, being substance-reproducible and built on public
  materials, is a legitimate final-selection **candidate on the teammate line**. Its private robustness
  hinges on H-visible vs H-hidden, which we cannot resolve locally.
- Our honest line (`54844628`) remains the team's most conservative, fully-owned, fully-reproducible
  candidate; under H-hidden its 760-well OOF validation is exactly the right evidence type.
- No our-side submission is made from this audit. If the pending pair completes with scores materially
  better than 6.669, the ledger and final-slot package get updated by the watcher follow-up.
