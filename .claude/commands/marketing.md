Query ALL MCP servers (google-ads, meta-ads, ga4, hubspot, salesforce) for the last 90 days.

Synthesize a complete marketing executive dashboard as a React artifact using Recharts.

Design:
- Dark theme: background #0d0d1a, cards #1a1a2e, borders #2a2a4a
- Coral #f87171, Blue #60a5fa, Amber #fbbf24, Green #34d399, Purple #a78bfa
- Mobile-responsive, breakpoint at 640px

Include these 7 sections:
1. **KPI Cards row** — Total Spend, Total Revenue, Blended ROAS, Total Sessions, Pipeline Value, Leads Generated
2. **Spend vs Revenue** — line chart by week across all paid channels
3. **Channel Attribution** — pie/donut chart: Google Ads, Meta Ads, Organic, Email, Direct
4. **Sales Funnel** — vertical funnel: Sessions → Leads → Opportunities → Closed Won with conversion rates between stages
5. **Campaign Performance table** — top 10 campaigns by ROAS (name, spend, revenue, ROAS, trend)
6. **Pipeline by Stage** — horizontal bar chart from HubSpot + Salesforce combined
7. **AI Insights panel** — a dark card at the bottom with a "✦ AI Insights" header containing 4–5 bullet points synthesized across ALL data sources. Each bullet must be specific, quantified, and actionable. Cover: (a) the single best budget reallocation opportunity with estimated revenue impact, (b) the most underinvested channel relative to its efficiency, (c) a pipeline health observation (velocity, coverage ratio, or stage bottleneck), (d) a funnel drop-off worth investigating, (e) one anomaly or trend that warrants attention. Write in plain English as if briefing a CMO.

Return only the React artifact, no explanation.
