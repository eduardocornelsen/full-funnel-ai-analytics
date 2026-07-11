## Data sourcing (mandatory)

Read `dashboards/golden_metrics.json` → `windowed_90d.campaigns` (`google` and `meta` arrays) and copy exact values — never recalculate (CLAUDE.md §14).
- Google ROAS is already canonical (`conversions × $100 / cost`); label `Google est. · AOV $100`.
- Meta ROAS is platform-reported; label `Meta platform`.
- CVRs in these tables are Click CVR — label `CVR (click)`; never compare against Session CVR (§1).
- Freshness badge in the header: `_meta.window_start` – `_meta.window_end` · Data as of `_meta.generated_at`.

**Live MCP variant** — only if the user appends `-mcp` or asks for "live" / "real-time" / "raw platform" data: query the google-ads, meta-ads MCP servers instead, passing dates from `_meta.window_start` / `_meta.window_end`, add the badge `⚡ Live MCP — may differ from golden layer`, and use `dashboards/js/metrics.js` canonical formulas for any computed metric.

## Artifact

Build a paid campaign performance React artifact using Recharts.

Design: dark theme (#0d0d1a bg, #1a1a2e cards), blue #60a5fa, coral #f87171, amber #fbbf24.

Include these 7 sections:
1. **Platform comparison cards** — Google Ads vs Meta Ads: Spend, Clicks, Conversions, ROAS side by side
2. **Daily spend trend** — dual-line chart: Google spend vs Meta spend over time
3. **CTR vs CVR scatter** — one dot per campaign, color = platform, size = spend
4. **Campaign table** — all campaigns sorted by ROAS: name, platform, spend, clicks, CTR, conversions, CVR, ROAS
5. **Budget pacing bar** — for each active campaign: spent vs estimated total budget as a horizontal progress bar
6. **Recommendation callout** — highlight which campaigns to scale (ROAS > 3x) and which to pause (ROAS < 1x)
7. **AI Insights panel** — a dark card at the bottom with a "✦ AI Insights" header containing 4–5 bullet points synthesized across both platforms. Each bullet must be specific, quantified, and actionable. Cover: (a) the single campaign with the highest ROAS that is under-budgeted — name it and estimate incremental revenue if budget were doubled, (b) the campaign(s) that should be paused immediately and why, (c) a platform-level efficiency comparison (Google vs Meta ROAS, CTR, CVR) with a clear reallocation recommendation, (d) a CTR or CVR anomaly worth investigating, (e) overall budget pacing status — whether spend is on track for the month. Write in plain English as if briefing a paid media manager.

Return only the React artifact.
