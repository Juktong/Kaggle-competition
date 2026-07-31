---
id: q46_submission_asset_inventory
priority: 650
status: queued
requires_gpu: false
can_submit: false
max_submit_cost: 0
---

# Q46 Submission Asset Inventory

Build the final asset map required for winner obligations and reproducibility.

Required execution:

1. For each serious submission candidate, record:
   - ref id;
   - score;
   - account;
   - code location;
   - kernel slug/version if known;
   - dataset_sources;
   - output submission file if available;
   - exact git commit if known.
2. Candidates must include:
   - 54922806, 54968060, 54844628, 55064411, 54990075, 54896975, 54923144.
3. Mark each field as known, inferred, missing, or inaccessible.
4. List the owner actions required to make any missing final-slot asset auditable.
5. Do not submit.

Write `reports/q46_submission_asset_inventory_2026-07-30.md`.
