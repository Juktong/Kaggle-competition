# Final Selection Context

Recommended final submissions:

1. `54922806`
   - Public score: `6.563`.
   - Current best public frontier-family submission from the teammate account.

2. `54844628`
   - Public score: `7.891`.
   - Selected for diversity, not public rank.
   - This is the decorrelated honest line and is intended to reduce private-set risk in the best-of-2 final selection.

## Why Not Public Top 2 Only

The high-public frontier submissions are more homogeneous. The second final slot should not only maximize public score; it should also reduce correlated private failure risk.

Our Q44/Q45 final-slot analysis estimated that `54844628` has meaningful best-of-2 value as the decorrelated slot, approximately `0.46 ft` mean and `0.94 ft` tail value versus using only homogeneous frontier submissions.

## Artifact / Version Note For `54922806`

For submission `54922806`, Kaggle API output retrieval may return the latest kernel output, not necessarily the exact submitted `scriptVersionId` output.

If `54922806` is selected, the exact submitted output should be downloaded or verified from Kaggle UI version history for the submitted version.

## Fallback If Teammate Confirmation Is Not Available

If teammate confirmation or the exact `54922806` submitted output cannot be obtained before the deadline, use the owned fallback pair:

- `54968060`
- `54844628`

This fallback keeps both selected submissions under the `joezzzzz` account with locally archived artifacts and repository commits. It gives up the `0.080` public-score edge of `54922806` over `54968060`, but avoids depending on a teammate-side version-history artifact at the deadline.

## Operational Note

When selecting final submissions in Kaggle, choose by exact submission ref ID, not by row order, file name, public rank, or recency:

- `54922806`
- `54844628`

Owned fallback if needed:

- `54968060`
- `54844628`
