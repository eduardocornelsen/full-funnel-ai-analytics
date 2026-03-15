---
description: Analyze the sales pipeline from HubSpot and Salesforce.
---

# /pipeline [query]

Visualize and analyze the health of the sales pipeline, from leads to closed-won deals.

## Steps
1. Call `hubspot.get_deal_pipeline_summary`.
2. Call `salesforce.get_opportunity_pipeline`.
3. Call `dbt-semantic-layer.get_metrics` for `win_rate` and `pipeline_velocity`.
4. Provide a conversion funnel: Leads -> Opportunities -> Closed Won.
5. Identify bottlenecks in specific stages.
