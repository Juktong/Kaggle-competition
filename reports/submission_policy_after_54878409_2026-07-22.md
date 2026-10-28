# Submission policy after `54878409` (2026-07-22)

Codifies the lessons from the `54878409` miss (public 7.953 vs banked 7.891) into standing rules.

## What went wrong

A candidate with a large 760-well OOF gain (+0.18) and a "stably positive" 760-well bootstrap
(5th +0.049, 99% positive) scored **worse** on public. Two independent causes:

1. **Wrong bootstrap scale.** The competition scores 3 wells; a 760-well resample does not constrain a
   3-well outcome. At 3-well scale the same effect is negative in ~42% of draws.
2. **Truth-space gap.** Local RMSE is computed against train-copy TVT; the leaderboard is a different
   scale (3.68 local vs 7.891 public) and rank is not preserved for ~0.1-margin differences. Local
   accuracy predicts the leaderboard only for *large* (≳0.5 local) differences.

## Standing rules

1. **No large-N-OOF-only submissions.** A 760-well OOF gain, however large or "stable", is not a
   submission criterion. Every gate uses the **3-well scale** (`scripts/eval_three_well_gate.py`).
2. **The visible-well check is a sanity check only** — format, finiteness, range, gross error. It is
   *not* independent confirmation of transfer (it reuses the train copies whose truth space does not
   match the leaderboard at fine scale).
3. **Public and private are row splits of the same 3 wells.** Public is the best available estimate of
   private, but only weakly for small margins (block-split corr ~0.10). Treat a public loss as
   informative, not as noise to be argued away.
4. **A candidate is submittable only if it is EITHER** (a) large in local space (≳0.5 OOF, where local
   predicts the leaderboard) **OR** (b) structurally distinct with an independent reason to expect
   transfer — **AND** passes the pre-submit HARD checks, kernel bit-exactness, and smoke. The 3-well
   5th>0 bar is retained but is understood to be nearly unreachable for small-margin candidates, which
   is the point: those should not be submitted.
5. **Kernels-only path is mandatory** (`competition_submit_code`, `kernel_version=N`); file submit
   returns 400. Record ref / public / commit / kernel version / slot number / why.
6. **Do not spend slots to "try" a candidate that fails the corrected gate.** With 5/day and a
   2026-08-05 deadline, slots are for candidates with a defensible transfer argument.

## Current standing

- **Honest slot: `54844628` (public 7.891).** The best real leaderboard signal on the actual test wells.
- **`54878409` (7.953): excluded** from the final honest slot — it is a measured regression.
- No candidate currently meets rule 4. **No submission is warranted today** beyond what has been done
  (1 slot used on `54878409` on 2026-07-21; 0 used on 2026-07-22).
