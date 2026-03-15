---
description: Perform full-funnel marketing analytics using Google Ads, Meta Ads and GA4.
---

# /marketing [query]

Analyze marketing performance across all digital channels. Use this command to calculate blended CAC, ROAS, and volume trends.

## Steps
1. Call `google-ads.get_campaign_performance` for the requested time period.
2. Call `meta-ads.get_campaign_insights` for the same period.
3. Call `ga4.get_traffic_by_channel` to get session and conversion volume.
4. Join the data on campaign name or channel group.
5. Provide a summary including:
   - Total Spend (Google + Meta)
   - Total Conversions (GA4)
   - Blended CAC (Total Spend / Total Conversions)
   - Blended ROAS (Total Revenue / Total Spend) - Note: Get Revenue from `Salesforce.get_revenue_by_source`.
