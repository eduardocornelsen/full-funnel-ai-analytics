Query google-ads (get_campaign_performance, list_campaigns) and meta-ads (get_campaign_insights, list_campaigns) MCP servers.

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
