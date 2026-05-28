# Full-Funnel AI Analytics — Agent Instructions

This file is loaded automatically at the start of every conversation.
All rules here are **mandatory** when generating dashboards, charts, tables, or any metric output from MCP data.

---

## 1. Canonical Metric Definitions

These are the single source of truth. Never deviate without explicit user instruction.

### CVR — Two valid definitions; always label which one

| Name | Formula | When to use | UI label |
|------|---------|-------------|----------|
| **Session CVR** | `conversions / sessions` | Cross-channel funnel analysis; GA4 data | `CVR (session)` |
| **Click CVR** | `conversions / clicks` | Within-platform campaign comparison (Google Ads, Meta Ads) | `CVR (click)` |

**Rule:** Never mix session CVR and click CVR on the same chart or table without explicit labelling of each.
Session CVR ≈ 2–4% for e-commerce. Click CVR ≈ 5–20%. Values are **not comparable across definitions**.

### ROAS

| Source | Formula | Notes |
|--------|---------|-------|
| **Meta Ads (platform)** | Use `roas` field directly from MCP response | Platform-reported; last-click, 7-day window |
| **Google Ads (estimated)** | `(conversions × AOV) / spend` where `AOV = $100` | Google MCP does not return revenue; use $100 AOV consistently |
| **Blended ROAS** | `total_attributed_revenue / total_spend` | Linear attribution; must label as "Linear · 90d" |

**Rule:** Never use a hardcoded spend multiplier (e.g., `spend × 3.5` or `spend × 0.8`) to estimate ROAS.
Always use `conversions × $100` for Google. Always use platform `roas` field for Meta.

### CTR

`clicks / impressions` — always expressed as a percentage.

### Conversion (funnel stages)

| Stage | Definition | Source |
|-------|-----------|--------|
| Sessions | GA4 session events | GA4 MCP |
| Conversions | GA4 conversion events | GA4 MCP |
| Deals Won | CRM closed-won deals | HubSpot / Salesforce MCP |
| CRM Contacts | All contacts in CRM (all-time) | HubSpot MCP |

**Critical rule:** CRM Contacts is an **all-time, lifetime count**. It must never appear as a funnel step after GA4 Conversions. A funnel step must always be ≤ the step above it. If CRM Contacts > GA4 Conversions, display CRM Contacts as a separate KPI card with label `(HubSpot all-time)`, not as a funnel stage.

### Win Rate

`closed_won_deals / (closed_won_deals + closed_lost_deals)`

---

## 2. Attribution Windows

| Metric | Window | Model | Label to show in UI |
|--------|--------|-------|---------------------|
| Blended ROAS | 90-day query period | Linear | `Linear attribution · 90d` |
| Channel ROAS | 90-day query period | Linear | `Linear attribution · 90d` |
| Platform ROAS (Meta) | 7-day click, 1-day view | Last-click | `Meta platform · 7-day window` |
| Platform ROAS (Google) | 30-day (default) | Last-click | `Google est. · AOV $100` |
| GA4 CVR | Query period | Session-level | `Session CVR` |
| Pipeline / Closed Won (CRM) | All-time by default | N/A | Always label `CRM all-time` |

**Rule:** Every ROAS and CVR KPI card must display its attribution window in the subtitle. Unlabelled ROAS is not acceptable.

---

## 3. Revenue Scopes — These are different things; never conflate them

| Label | Definition |
|-------|-----------|
| `Attributed Revenue (90d)` | GA4-tracked orders within the query period, attributed via linear model across paid channels |
| `Salesforce Closed Won (90d)` | Revenue from SF opportunities closed in the 90-day period |
| `CRM Closed Won (all-time)` | Lifetime closed-won revenue across HubSpot + Salesforce combined |

When a dashboard shows both a pipeline KPI and a revenue attribution chart, explicitly annotate which scope each uses.

---

## 4. Channel Attribution Percentages

Attribution shares across channels must always sum to exactly 100%.
Before rendering any pie/donut chart of channel attribution:
1. Sum all values
2. If sum ≠ 100, normalise: `value = (value / sum) × 100`
3. Round to 1 decimal place

---

## 5. Funnel Integrity Rules

A valid funnel requires each step ≤ the step above it:
- Sessions > Engaged Sessions > Conversions > Deals Won

If any data violates this (e.g., a CRM count > GA4 conversions), do not include it in the funnel. Instead:
- Display it as a separate KPI card
- Label its scope clearly (e.g., "all-time", "different source")

---

## 6. Data Freshness

Every generated dashboard must include a data freshness indicator showing the query period.
Format: `[Start date] – [End date] · Data as of [today]`

Default query period: last 90 days.

---

## 7. Spend Field Mapping

| Platform | MCP field | Notes |
|----------|-----------|-------|
| Google Ads | `cost` | In USD |
| Meta Ads | `spend` | In USD |

Use `cost` for Google, `spend` for Meta. Never swap them.

---

## 8. AOV Assumption

Average Order Value (AOV) = **$100** for all Google ROAS estimates.

This is derived from Meta platform data: average revenue per conversion across Meta campaigns ≈ $99–$101.
This assumption must be used consistently. If the user provides a different AOV, update it everywhere in the same response.

---

## 9. Queried Date Range (Default)

### Synthetic Dataset (this project's default)

The original synthetic dataset has a **fixed boundary** — it does not update:

| Variable | Value | Notes |
|----------|-------|-------|
| `ANCHOR_DATE` | **2026-03-15** | Dataset end — never use `today()` |
| `WINDOW_START` | **2025-12-16** | 90 days before anchor |
| `WINDOW_END`   | **2026-03-15** | Anchor date |

**Rule for synthetic data:** Always use these exact dates. Never compute
`today() - 90 days`. Using `today()` produces a different window every day,
making dashboards non-reproducible.

**How to identify synthetic data:** The dataset is in use when sourcing from
`data/olist_analytics.duckdb` or `data/mock_marketing/*.csv`.

### Available Pre-Computed Windows

`golden_metrics.json` (schema v2.2) contains these sections:

| JSON key | Window | Label |
|----------|--------|-------|
| `windowed_7d` | 2026-03-09 → 2026-03-15 | Last 7 days |
| `windowed_30d` | 2026-02-14 → 2026-03-15 | Last 30 days |
| `windowed_60d` | 2026-01-15 → 2026-03-15 | Last 60 days |
| `windowed_90d` | 2025-12-16 → 2026-03-15 | **Canonical 90-day window** |
| `windowed_180d` | 2025-09-17 → 2026-03-15 | Last 180 days |
| `month_2026_03` | 2026-03-01 → 2026-03-15 | March 2026 (partial) |
| `month_2026_02` | 2026-02-01 → 2026-02-28 | February 2026 |
| `month_2026_01` | 2026-01-01 → 2026-01-31 | January 2026 |
| `all_time` | 2024-07-16 → 2026-03-15 | Full dataset range |

For live data, windows roll forward from today. The scheduled refresh
(`scheduled-refresh.yml`) regenerates all windows daily at 06:00 UTC.

### On-Demand Queries — Any Date Range

For windows NOT listed above (e.g., last 45 days, Q1 2026, a custom range),
use `scripts/query_window.py`. It queries the CSV source files directly via
DuckDB and returns the same schema as a `golden_metrics.json` section.

```bash
python scripts/query_window.py --last-days 45
python scripts/query_window.py --last-days 1          # yesterday (anchor-relative)
python scripts/query_window.py --month 2025-11        # November 2025
python scripts/query_window.py --year 2025            # full year
python scripts/query_window.py --start 2025-10-01 --end 2026-03-15
python scripts/query_window.py --last-days 60 --output metrics_60d.json
```

**Python API:**
```python
from datetime import date
from scripts.query_window import query_window
section = query_window(date(2026, 1, 1), date(2026, 3, 15))
print(section["blended_roas"])   # same schema as golden_metrics.json
```

**Labelling rule:** Any dashboard built from `query_window.py` output must display:
> ⚡ Ad-hoc query · not from golden layer

This distinguishes it from zero-drift golden layer dashboards.

**CRM data is always all-time** regardless of the query window — it is a
lifetime count (see §1 and §5). `query_window.py` labels this with `_note`.

### Live / Real Dataset (open-source swap-in)

This project is open source. If the user connects a real marketing data source
(live MCP, BigQuery, Supabase, Snowflake, or any daily-refreshed dataset),
use the rolling window instead:

- `end_date`: **today** (`date.today()`)
- `start_date`: **90 days before today** (`today - 90 days`)

**How to identify live data:** User says "connect my real data", "use BigQuery",
"use production", or configures a non-DuckDB dbt target.

Always pass explicit dates to MCP tools. Never use open-ended queries.

---

## 10. Dashboard Generation Rules

When generating any HTML dashboard or React artifact from MCP data:

1. **Always read the data first**, then compute metrics. Never hardcode values that should come from MCP.
2. **Label every metric** with its formula basis (session vs click CVR, attribution window on ROAS).
3. **Do not use synthetic multipliers** to estimate revenue for Google Ads. Always use `conversions × $100`.
4. **Validate funnel stage ordering** before rendering. Fix any stage-ordering violations.
5. **Normalise attribution percentages** to 100% before rendering pie/donut charts.
6. **Separate CRM lifetime data from 90-day attributed data** — use different section headings or KPI cards.
7. **Include a data freshness badge** in the dashboard header.

---

## 11. Skill Quick Reference

Each skill has two modes: **golden** (default, reads `golden_metrics.json`) and
**-mcp** (live, queries mock MCP servers directly). The golden mode guarantees
zero metric drift; the -mcp mode shows raw real-time platform data.

### Golden Layer Skills (default — read `dashboards/golden_metrics.json`)

| Skill | Data source | Primary metric |
|-------|-------------|----------------|
| `/marketing` | `windowed_90d` + `all_time` sections | Blended ROAS (linear · 90d) |
| `/campaign` | `windowed_90d.campaigns` | Platform ROAS per campaign |
| `/attribution` | `windowed_90d.attribution_by_channel` | Channel revenue share (linear · 90d) |
| `/traffic` | `windowed_90d.ga4_by_channel` | Session CVR by channel |
| `/pipeline` | `all_time.crm` | Win rate, pipeline value (CRM all-time) |

### Live MCP Skills (opt-in — bypasses golden layer)

Triggered by appending `-mcp` to any skill name or by user requesting "live", "real-time", or "raw platform" data.

| Skill | MCP servers queried | Notes |
|-------|--------------------|-|
| `/marketing-mcp` | google-ads, meta-ads, ga4, hubspot, salesforce | Add ⚡ Live MCP badge |
| `/campaign-mcp` | google-ads, meta-ads | Per-campaign raw platform data |
| `/attribution-mcp` | ga4, google-ads, meta-ads | Raw channel attribution |
| `/traffic-mcp` | ga4 | Live session data |
| `/pipeline-mcp` | hubspot, salesforce | Live CRM data |

**Rule for MCP skills:** Pass canonical dates (`start_date=2025-12-16`, `end_date=2026-03-15`)
for synthetic data. Use rolling `today() - 90` for live datasets (see §9).

---

## 12. Dbt Semantic Layer Reference

Canonical metric definitions live in:
`dbt_project/models/metrics/metrics.yml`

When in doubt about a metric formula, read that file. It is the single source of truth for computed metrics.

Key metrics:
- `session_conversion_rate` = `total_orders / total_sessions` ← **canonical cross-channel CVR**
- `blended_roas` = `total_revenue / total_spend` (linear attribution, 90d)
- `channel_roas` = `channel_revenue / channel_spend` (linear attribution, 90d)


---

## 13. Shared Metrics Module (code-level enforcement)

`dashboards/js/metrics.js` is the **mandatory** runtime enforcement of all metric rules.

All new HTML dashboards MUST load it before any inline script block:
```html
<script src="js/metrics.js"></script>
```

**NEVER compute CVR, ROAS, or attribution percentages inline.** Use canonical functions:

| Function | Formula | When to use |
|----------|---------|-------------|
| `Metrics.googleROAS(conv, cost)` | `conv × $100 / cost` | All Google Ads ROAS |
| `Metrics.metaROAS(platformRoas)` | pass-through | Meta platform roas field |
| `Metrics.sessionCVR(conv, sessions)` | `conv / sessions × 100` | Cross-channel, GA4 |
| `Metrics.clickCVR(conv, clicks)` | `conv / clicks × 100` | Platform campaign tables |
| `Metrics.normaliseAttribution(channels)` | normalises `val` to sum 100% | Any pie/donut/attribution bar |
| `Metrics.validateFunnel(steps)` | returns `issues[]` | Before rendering any funnel |

Use `Metrics.labels.*` for canonical KPI subtitle strings (attribution windows, CVR basis).

Existing dashboards that already use `metrics.js`:
- `attribution_dashboard.html`
- `marketing_full_funnel_dashboard.html`
- `full_funnel_marketing_dashboard.html`

---

## 14. Golden Layer First — Mandatory Data Sourcing

This project's purpose is **zero metric drift** between dbt and dashboards.
The following rules are mandatory.

### Default: Read `dashboards/golden_metrics.json`

1. **Before generating any dashboard**, read `dashboards/golden_metrics.json`.
2. This file is pre-computed from the dbt golden layer (DuckDB mart tables).
3. **Copy exact values** from this file into HTML dashboard JS constants.
   Do NOT recalculate metrics independently.
4. Check `_meta.available_windows` to see which windows are pre-computed.
5. Use `windowed_90d` for the canonical 90-day view.
6. Use `all_time` only when explicitly showing lifetime data.
7. For any other window (30d, monthly, custom range) — see §9 `query_window.py`.

**Why:** If you recalculate metrics from MCP data, rounding differences and
non-deterministic AI arithmetic will cause drift versus the golden layer.
Reading pre-computed values guarantees bit-for-bit reproducibility.

### Exception: Live MCP Querying (explicit opt-in only)

Only bypass golden_metrics.json when the user explicitly says one of:
- "query live data" / "get real-time data" / "use MCP"
- "show raw platform data" / "bypass golden layer" / "live from MCP"

When in Live MCP mode:
1. Pass **canonical dates**: `start_date=2025-12-16`, `end_date=2026-03-15`
2. Add to the dashboard header badge: `⚡ Live MCP — may differ from golden layer`
3. Still use `metrics.js` canonical functions for all calculations
4. For HubSpot/Salesforce, pass the same dates to `get_deal_pipeline_summary()`
   and `get_opportunity_pipeline()` — these servers now support date filtering.

### Never Mix Scopes

- Never divide all-time revenue by 90-day spend (this was the source of the
  nonsensical 71.1× Blended ROAS bug)
- If using `windowed_90d`: ALL numbers must come from that section only
- If using `all_time`: ALL numbers must come from that section only
- Label every ROAS and CVR with its scope per §2 Attribution Windows rules

### Data Source Decision Tree

```
User asks for data or a dashboard
  │
  ├─ Skill ends in "-mcp"  OR  user says "live", "real-time", "raw platform"?
  │   ├─ YES → Use MCP servers
  │   │         · Synthetic:  dates = 2025-12-16 → 2026-03-15
  │   │         · Live/real:  dates = today()-90d → today()
  │   │         · Add ⚡ Live MCP badge
  │   │         · Use metrics.js for all calculations
  │   └─ NO  → Use golden layer (default)
  │
  └─ What date window does the user want?
      │
      ├─ 90d (default), 7d, 30d, 60d, 180d, or a recent calendar month?
      │   └─ Read dashboards/golden_metrics.json
      │       · Check _meta.available_windows for the exact key
      │       · Copy exact values — no recalculation
      │       · Use all_time only for lifetime/CRM views
      │
      ├─ Any other window (45d, last quarter, Q1, custom range, etc.)?
      │   └─ Run python scripts/query_window.py
      │       · --last-days N  |  --month YYYY-MM  |  --year YYYY
      │       · --start YYYY-MM-DD --end YYYY-MM-DD
      │       · OR: from scripts.query_window import query_window
      │       · Label dashboard: ⚡ Ad-hoc query · not from golden layer
      │       · CRM data is still all-time in the result
      │
      └─ Does golden_metrics.json exist?
          ├─ YES → Use it
          └─ NO  → Tell user: python scripts/generate_golden_metrics.py
```
