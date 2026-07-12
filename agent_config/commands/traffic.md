## Data sourcing (mandatory)

Read `dashboards/golden_metrics.json` → `windowed_90d.ga4_by_channel` and `windowed_90d.sessions`; copy exact values — never recalculate (CLAUDE.md §14).
- All CVRs here are Session CVR — label `CVR (session)` (§1).
- Validate funnel ordering before rendering any funnel (§5).
- Freshness badge in the header: `_meta.window_start` – `_meta.window_end` · Data as of `_meta.generated_at`.

**No file access?** (e.g. Claude Desktop): the `analytics` MCP server serves the same golden layer — `get_metric(metric, window)` returns governed values with formula/scope/window envelopes, `get_funnel(window)` validates funnel ordering server-side, `get_precomputed_window(window)` returns full sections. Same zero-drift guarantee as the file.

**Live MCP variant** — only if the user appends `-mcp` or asks for "live" / "real-time" / "raw platform" data: query the ga4 MCP servers instead, passing dates from `_meta.window_start` / `_meta.window_end`, add the badge `⚡ Live MCP — may differ from golden layer`, and use `dashboards/js/metrics.js` canonical formulas for any computed metric.

## Artifact

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
