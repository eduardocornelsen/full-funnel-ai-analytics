---
description: Compare different attribution models for revenue credit.
---

# /attribution [query]

Analyze how revenue is attributed to different marketing channels using First-Touch, Last-Touch, and Linear models.

## Steps
1. Call `dbt-semantic-layer.get_metrics` for `first_touch_revenue`, `last_touch_revenue`, and `linear_revenue`.
2. Group by `channel`.
3. Highlight the channel with the biggest discrepancy between models (e.g., strong at first-touch but weak at last-touch).
4. Recommend spend adjustments based on top-funnel vs bottom-funnel performance.
