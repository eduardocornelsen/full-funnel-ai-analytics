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

Unless the user specifies otherwise:
- `start_date`: 90 days before today
- `end_date`: today

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

| Skill | MCP servers queried | Primary metric |
|-------|--------------------|-|
| `/marketing` | google-ads, meta-ads, ga4, hubspot, salesforce | Blended ROAS (linear · 90d) |
| `/campaign` | google-ads, meta-ads | Platform ROAS per campaign |
| `/attribution` | ga4, google-ads, meta-ads | Channel revenue share (linear · 90d) |
| `/traffic` | ga4 | Session CVR by channel |
| `/pipeline` | hubspot, salesforce | Win rate, pipeline value (CRM all-time) |

---

## 12. Dbt Semantic Layer Reference

Canonical metric definitions live in:
`dbt_project/models/metrics/metrics.yml`

When in doubt about a metric formula, read that file. It is the single source of truth for computed metrics.

Key metrics:
- `session_conversion_rate` = `total_orders / total_sessions` ← **canonical cross-channel CVR**
- `blended_roas` = `total_revenue / total_spend` (linear attribution, 90d)
- `channel_roas` = `channel_revenue / channel_spend` (linear attribution, 90d)
