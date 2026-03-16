Query hubspot (get_deal_pipeline_summary, get_contacts_summary) and salesforce (get_opportunity_pipeline, get_revenue_by_source) MCP servers.

Build a sales pipeline React artifact using Recharts.

Design: dark theme (#0d0d1a bg, #1a1a2e cards), green #34d399, blue #60a5fa, amber #fbbf24, coral #f87171.

Include:
1. **Pipeline KPI cards** — Total Pipeline Value, Avg Deal Size, Win Rate, Deals in Progress, Forecasted Revenue
2. **Stage progression funnel** — horizontal funnel chart showing deal count and value at each stage (HubSpot + Salesforce merged)
3. **Revenue by lead source** — horizontal bar chart from Salesforce closed-won data
4. **Velocity gauge** — a simple visual showing average days in pipeline vs target (use a progress arc)
5. **Deal age heatmap** — table of stages vs age buckets (0-30d, 31-60d, 61-90d, 90d+) with color intensity
6. **Contacts by lifecycle** — donut chart of HubSpot lifecycle stages

Return only the React artifact.
