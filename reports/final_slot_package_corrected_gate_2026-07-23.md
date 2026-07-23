# Final-slot package — updated for the PF-frontier situation (2026-07-23)

Supersedes the 2026-07-22 package. Final selection is best-of-2 across the team's submissions.

## Current facts

| ref | public | side | role |
|---|---|---|---|
| **`54896975`** | **6.669** | teammate | **team best-public** (Kaiwalya PF frontier reproduction; overlap + prefix-calibration + bimodal midpoint family) |
| `54922806` / `54923144` | PENDING | teammate | PF-frontier reruns/branches; watcher polling |
| **`54844628`** | **7.891** | ours | **honest slot** — fully owned, fully reproducible, no overlap/runtime constructions |
| `54878409` | 7.953 | ours | **excluded** (measured regression) |
| `54853492` | 7.360 | teammate | earlier hidden-mode architecture |
| `54174151` / `54289934` | 7.182 / 7.212 | overlap line | superseded on public by 54896975 |

## Recommendation structure (two slots, two evidence types)

- **Slot 1 (team best-public line): `54896975`** — or the better of the pending pair if one completes
  below 6.669. Rationale: best measured public; substance-reproducible from a public notebook; its
  private robustness depends on the H-visible/H-hidden question (see the candidate audit) — under
  H-hidden its overlap component goes inert and it reverts toward its fallback pipeline; under
  H-visible its public advantage carries.
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

1. A pending ref completes **below 6.669** → it becomes slot-1 candidate; ledger + this file update.
2. Resolution of H-visible vs H-hidden (e.g. organizer clarification or teammate's rerun evidence) →
   if H-visible is confirmed, the frontier family's public advantage is more likely to carry to private
   and slot 2's hedge value drops; if H-hidden, slot 2's weight rises.
3. An our-side candidate passing the corrected gate AND the post-54878409 policy (large local margin or
   structural distinctness) — none exists today.
