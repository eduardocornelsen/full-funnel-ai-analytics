Query ga4 (get_traffic_by_channel), google-ads (get_campaign_performance), and meta-ads (get_campaign_insights) MCP servers.

Build a channel attribution deep-dive React artifact using Recharts.

Design: dark theme (#0d0d1a bg, #1a1a2e cards), coral #f87171, blue #60a5fa, amber #fbbf24, green #34d399.

Include:
1. **Attribution summary cards** — Sessions, Conversions, Revenue, Avg CPC per channel
2. **Multi-channel waterfall** — grouped bar chart: impressions, clicks, conversions by channel side by side
3. **Efficiency scatter plot** — X axis: spend, Y axis: ROAS, bubble size: conversions. One bubble per campaign.
4. **Top/Bottom performers table** — top 5 and bottom 5 campaigns by ROAS with color-coded badges
5. **Channel mix over time** — stacked area chart showing share of spend by channel week over week
6. **Key insight callout** — a highlighted text box summarizing the single biggest optimization opportunity

Return only the React artifact.
