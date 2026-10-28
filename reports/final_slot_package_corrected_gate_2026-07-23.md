# Final-slot package — updated for the PF-frontier situation (2026-07-23)

Supersedes the 2026-07-22 package. Final selection is best-of-2 across the team's submissions.

## Current facts

| ref | public | side | role |
|---|---|---|---|
| **`54922806`** | **6.563** | teammate | **team best-public** (PF frontier "independent hidden-runtime rerun"; promoted per the pre-registered rule) |
| `54896975` | 6.669 | teammate | superseded on public by 54922806 (same frontier family) |
| `54923144` | 6.678 | teammate | frontier "GR sigma 1.0" branch; does not supersede |
| **`54844628`** | **7.891** | ours | **honest slot** — fully owned, fully reproducible, no overlap/runtime constructions |
| `54878409` | 7.953 | ours | **excluded** (measured regression) |
| `54853492` | 7.360 | teammate | earlier hidden-mode architecture |
| `54174151` / `54289934` | 7.182 / 7.212 | overlap line | superseded on public by 54896975 |

## Recommendation structure (two slots, two evidence types)

- **Slot 1 (team best-public line): `54922806` (6.563)** — promoted from the pending pair per the
  pre-registered rule (completed below 6.669). Same PF-frontier family as `54896975` (which remains the
  family's fallback candidate at 6.669); private robustness still hinges on H-visible/H-hidden — under
  H-hidden the family's visible-set components go inert and it reverts toward its fallback pipeline;
  under H-visible its public advantage carries. Its "hidden-runtime rerun" construction remains the
  compliance-gray point flagged to the final-selection owner.
- **Slot 2 (honest/conservative line): `54844628`** — the strongest fully-owned candidate with
  760-well OOF validation and no visible-set-specific constructions. Under H-hidden (private = novel
  wells), this evidence type is exactly matched to the private task; it hedges the frontier line's risk.

This pairing maximises coverage of the two scoring hypotheses rather than betting both slots on one.
(*Final say on slot 1 belongs to the teammate line's owner; per standing directive our decisions do not
build around teammate submissions — this package records the structure, not a unilateral choice.*)

## Excluded

- `54878409` (7.953): measured public regression vs 7.891; stays excluded.
- All unsubmitted our-side candidates: none passes the corrected gate
  (`reports/corrected_gate_candidate_reaudit_2026-07-22.md`).

## Conditions that would change this package

1. ~~A pending ref completes below 6.669~~ — happened: `54922806` = 6.563, promoted (this revision).
2. Resolution of H-visible vs H-hidden (e.g. organizer clarification or teammate's rerun evidence) →
   if H-visible is confirmed, the frontier family's public advantage is more likely to carry to private
   and slot 2's hedge value drops; if H-hidden, slot 2's weight rises.
3. An our-side candidate passing the corrected gate AND the post-54878409 policy (large local margin or
   structural distinctness) — none exists today.
