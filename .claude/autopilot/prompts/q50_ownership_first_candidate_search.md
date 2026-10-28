---
id: q50_ownership_first_candidate_search
priority: 690
status: queued
requires_gpu: false
can_submit: true
max_submit_cost: 1
---

# Q50 Ownership-First Candidate Search

Find whether any our-account candidate can replace teammate `54922806` without losing meaningful expected score.

Required execution:

1. Treat current ownership-first pair as 54968060 + 54844628.
2. Search only candidates that are:
   - our account;
   - provenance documented;
   - not a near duplicate of already submitted candidates unless they close an ownership/provenance gap.
3. Consider:
   - reproducible Mark/frontier package from our account;
   - frontier dependency cleanup only if no prediction change is expected and disclosure improves;
   - transition-prior candidate if Q40/Q49 finds one.
4. Do not submit if the candidate is expected to land inside the 0.115 floor and does not improve provenance.
5. If no candidate exists, state that ownership-first already has its best available pair.

Write `reports/q50_ownership_first_candidate_search_2026-07-30.md`.
