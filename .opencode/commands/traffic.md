Query ga4 (get_traffic_by_channel, get_daily_trends) MCP server.

Build a web traffic analytics React artifact using Recharts.

Design: dark theme (#0d0d1a bg, #1a1a2e cards), blue #60a5fa, green #34d399, amber #fbbf24.

Include these 7 sections:
1. **Traffic KPI cards** — Total Sessions, Engaged Sessions, Engagement Rate, Total Conversions, Conversion Rate
2. **Sessions over time** — area chart with daily trend and a 7-day rolling average line
3. **Channel breakdown table** — sessions, engaged sessions, conversions, engagement rate, CVR per channel with sparkline column
4. **Conversion funnel by channel** — grouped bar: sessions vs conversions per channel
5. **Device split** — if data available, pie chart of mobile/desktop/tablet; otherwise show channel share
6. **Anomaly callout** — flag any day where sessions dropped or spiked >30% vs prior 7-day average
7. **AI Insights panel** — a dark card at the bottom with a "✦ AI Insights" header containing 4–5 bullet points synthesized from GA4 traffic data. Each bullet must be specific, quantified, and actionable. Cover: (a) the highest-converting channel and whether it is receiving proportional traffic investment, (b) the channel with the most sessions but lowest CVR — what this suggests and what to test, (c) the most significant traffic anomaly detected and its likely cause, (d) engagement rate patterns that point to content or landing page issues, (e) a concrete recommendation for improving overall session CVR. Write in plain English as if briefing a growth or content team.

Return only the React artifact.
