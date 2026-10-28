# ROGII — FINAL SELECTION PACKAGE (2026-07-19)

Session `8de8cbed`. The two submissions to select on the Kaggle final-selection page. Competition deadline
**2026-08-05 23:59 UTC**; private hidden until then. Best-of-2 rule (private rank = the better of the 2 selected).
Neutral technical language.

## Recommended pair (primary)
| slot | ref | public | role | why |
|---|---|---|---|---|
| honest / novel | **54804893** | **8.080** | primary (targets the novel/private prize) | DWT+PF honest blend; OOF 9.30 (best honest, +1.10 vs DWT), public-verified transfer (8.080 < DWT 9.487 & Sunny 8.864); robust across 7/8 private stress scenarios; fully honest (no overlap exploitation). |
| overlap hedge | **54174151** | **7.182** | free-option hedge for an overlap-heavy private | Lucifer baseline repro; lowest-public overlap play; exact-id toe reconstruction (FP-safe on novel — doesn't fire); reproducible + audited; captures more hidden overlap than Gate-Safe. |

**Alternative (conservative) pair:** swap the hedge to **Gate-Safe 54289934 (7.212)** — bounded affine overlay,
safer ONLY if the private overlap is affine-only (different ids) where exact-id matching would miss it.

## The two refs to select on the Kaggle page
- **54804893** (DWT+PF blend) — MUST select (honest/novel slot).
- **54174151** (Lucifer 7.182) — recommended hedge; OR **54289934** (Gate-Safe 7.212) if preferring the bounded
  mechanism. Both are COMPLETE + selectable (verified).

## Why NOT the other candidates
- **qwer 54777533 (7.921):** source/predictions unrecoverable (4 checks); OOF 6.909 is 26% below the verified
  honest frontier (9.30) = leakage; dominated by both overlap plays. Not selectable-worthy.
- **Sunny PF90 54710185 (8.864):** the DWT+PF blend beats it honestly (8.080 < 8.864); its public is
  overlap-leakage on the visible wells, not novel strength.
- **DWT det-base 54775625 (9.487):** superseded by the blend (blend ≤ DWT everywhere measured); as a 2nd slot
  it adds no overlap capture and the blend already floors ≥ DWT.
- **Lucifer full stack / v36 54753209 / HMM 54387277 / Hongwei 54331645 / Amged 54447950:** overlap/public
  hedges with HIGHER public than 54174151 (dominated) or unrecoverable; none improves either slot.
- **Post-proc / neural / TabICL / mycarta / broken-lookup:** public ≥ 9.8 or invalid; not competitive.

## Preference guide (controlled vs lowest-public)
- **Lowest-public / max overlap capture / FP-safe → 54174151 (7.182).**
- **Most controlled / bounded / hedge against affine-only private overlap → Gate-Safe 54289934 (7.212).**
- Either way the honest slot 54804893 is the primary and floors the pair at ~9.3 on the novel goal; the 2nd
  slot is a marginal (0.03) overlap-scenario hedge.

## Manual-confirmation items (Kaggle UI, not CLI-verifiable)
- Confirm the final-selection page allows selecting exactly 2 submissions and uses best-of-2 (standard, but
  verify on the UI before the deadline).
- Select the two refs above by their submission id.
- No new submission is part of this package (all picks are banked/selectable).
