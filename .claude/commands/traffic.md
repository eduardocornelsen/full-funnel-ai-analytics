Query ga4 (get_traffic_by_channel, get_daily_trends) MCP server.

Build a web traffic analytics React artifact using Recharts.

Design: dark theme (#0d0d1a bg, #1a1a2e cards), blue #60a5fa, green #34d399, amber #fbbf24.

Include:
1. **Traffic KPI cards** — Total Sessions, Engaged Sessions, Engagement Rate, Total Conversions, Conversion Rate
2. **Sessions over time** — area chart with daily trend and a 7-day rolling average line
3. **Channel breakdown table** — sessions, engaged sessions, conversions, engagement rate, CVR per channel with sparkline column
4. **Conversion funnel by channel** — grouped bar: sessions vs conversions per channel
5. **Device split** — if data available, pie chart of mobile/desktop/tablet; otherwise show channel share
6. **Anomaly callout** — flag any day where sessions dropped or spiked >30% vs prior 7-day average

Return only the React artifact.
