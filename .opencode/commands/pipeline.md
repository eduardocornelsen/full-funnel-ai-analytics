## Data sourcing (mandatory)

Read `dashboards/golden_metrics.json` → `all_time.crm` (HubSpot + Salesforce) and copy exact values — never recalculate (CLAUDE.md §14).
- All CRM figures are lifetime — label every KPI `CRM all-time` (§2); never mix with 90-day attributed revenue (§3).
- Win rate = closed_won / (closed_won + closed_lost) (§1).
- Freshness badge in the header: `Data as of _meta.generated_at · CRM all-time scope`.

**Live MCP variant** — only if the user appends `-mcp` or asks for "live" / "real-time" / "raw platform" data: query the hubspot, salesforce MCP servers instead, passing dates from `_meta.window_start` / `_meta.window_end`, add the badge `⚡ Live MCP — may differ from golden layer`, and use `dashboards/js/metrics.js` canonical formulas for any computed metric.

## Artifact

Build a sales pipeline React artifact using Recharts.

Design: dark theme (#0d0d1a bg, #1a1a2e cards), green #34d399, blue #60a5fa, amber #fbbf24, coral #f87171.

Include these 7 sections:
1. **Pipeline KPI cards** — Total Pipeline Value, Avg Deal Size, Win Rate, Deals in Progress, Forecasted Revenue
2. **Stage progression funnel** — horizontal funnel chart showing deal count and value at each stage (HubSpot + Salesforce merged)
3. **Revenue by lead source** — horizontal bar chart from Salesforce closed-won data
4. **Velocity gauge** — a simple visual showing average days in pipeline vs target (use a progress arc)
5. **Deal age heatmap** — table of stages vs age buckets (0-30d, 31-60d, 61-90d, 90d+) with color intensity
6. **Contacts by lifecycle** — donut chart of HubSpot lifecycle stages
7. **AI Insights panel** — a dark card at the bottom with a "✦ AI Insights" header containing 4–5 bullet points synthesized across HubSpot and Salesforce data. Each bullet must be specific, quantified, and actionable. Cover: (a) the stage with the biggest conversion drop-off and what it signals about the sales process, (b) pipeline velocity vs target — whether the team is on track and what is causing lag if not, (c) the lead source generating the highest-value closed-won deals and whether it is being prioritized, (d) any deal age concentration risk (large value stuck in late stages for too long), (e) a forecast accuracy observation — how weighted pipeline compares to closed-won run rate. Write in plain English as if briefing a sales leader or VP of Revenue.

Return only the React artifact.
