## Data sourcing (mandatory)

Read `dashboards/golden_metrics.json` → `windowed_90d.attribution_by_channel` and `windowed_90d.channel_performance`; copy exact values — never recalculate (CLAUDE.md §14).
- Attribution shares must sum to 100% — normalise before any pie/donut (§4).
- Label revenue figures `Linear attribution · 90d`; first/last-touch columns are for model comparison only.
- Freshness badge in the header: `_meta.window_start` – `_meta.window_end` · Data as of `_meta.generated_at`.

**Live MCP variant** — only if the user appends `-mcp` or asks for "live" / "real-time" / "raw platform" data: query the ga4, google-ads, meta-ads MCP servers instead, passing dates from `_meta.window_start` / `_meta.window_end`, add the badge `⚡ Live MCP — may differ from golden layer`, and use `dashboards/js/metrics.js` canonical formulas for any computed metric.

## Artifact

Build a channel attribution deep-dive React artifact using Recharts.

Design: dark theme (#0d0d1a bg, #1a1a2e cards), coral #f87171, blue #60a5fa, amber #fbbf24, green #34d399.

Include these 7 sections:
1. **Attribution summary cards** — Sessions, Conversions, Revenue, Avg CPC per channel
2. **Multi-channel waterfall** — grouped bar chart: impressions, clicks, conversions by channel side by side
3. **Efficiency scatter plot** — X axis: spend, Y axis: ROAS, bubble size: conversions. One bubble per campaign.
4. **Top/Bottom performers table** — top 5 and bottom 5 campaigns by ROAS with color-coded badges
5. **Channel mix over time** — stacked area chart showing share of spend by channel week over week
6. **Key insight callout** — a highlighted text box summarizing the single biggest optimization opportunity
7. **AI Insights panel** — a dark card at the bottom with a "✦ AI Insights" header containing 4–5 bullet points synthesized from attribution data. Each bullet must be specific, quantified, and actionable. Cover: (a) which channel has the best ROAS and is under-allocated relative to spend share, (b) which channel has the worst efficiency and should be cut or restructured, (c) the biggest gap between first-touch and last-touch credit (which channel drives awareness vs closes deals), (d) a CVR anomaly across channels worth investigating, (e) a concrete budget shift recommendation with estimated impact. Write in plain English as if briefing a paid media manager.

Return only the React artifact.
