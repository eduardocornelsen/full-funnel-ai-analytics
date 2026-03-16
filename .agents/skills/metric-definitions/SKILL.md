---
name: metric-definitions
description: >
  Returns the canonical metric definitions for this project: CVR formula (session vs click),
  ROAS calculation (Google AOV-based vs Meta platform-native), attribution windows,
  revenue scopes, funnel integrity rules, and channel attribution normalisation.
  Use this skill before generating any dashboard or when a metric discrepancy is reported.
---

# Metric Definitions — Full-Funnel AI Analytics

All definitions here are enforced by `CLAUDE.md` at the project root and documented in
`dbt_project/models/metrics/metrics.yml`.

---

## CVR (Conversion Rate)

Two definitions are valid. **Never mix them on the same surface without labelling both.**

| Definition | Formula | Denominator | Typical range | UI label |
|-----------|---------|-------------|---------------|----------|
| **Session CVR** | `conversions / sessions` | GA4 sessions | 1–5% e-commerce | `CVR (session)` |
| **Click CVR** | `conversions / clicks` | Paid ad clicks | 5–20% paid campaigns | `CVR (click)` |

**When to use each:**
- Cross-channel funnel, GA4 tables → **Session CVR**
- Google Ads / Meta Ads campaign tables → **Click CVR**
- Never compare session CVR to click CVR as if they measure the same thing

---

## ROAS (Return on Ad Spend)

| Scope | Formula | Attribution model | Window | UI label |
|-------|---------|-------------------|--------|----------|
| **Meta (platform)** | `roas` field from MCP response | Last-click | 7-day click / 1-day view | `Meta platform · 7d` |
| **Google (estimated)** | `(conversions × $100) / cost` | Last-click (estimated) | 30-day | `Google est. · AOV $100` |
| **Blended** | `total_attributed_revenue / total_spend` | Linear | 90-day query period | `Linear attribution · 90d` |
| **Channel** | `channel_revenue / channel_spend` | Linear | 90-day query period | `Linear attribution · 90d` |

**AOV assumption:** $100 per conversion for all Google ROAS estimates.
Derived from Meta platform data: average revenue/conversion across Meta campaigns ≈ $100.

**Never use:** `spend × multiplier` to estimate Google revenue. This produces synthetic, non-reproducible values.

---

## CTR

`clicks / impressions` — always as a percentage.
Source: platform MCP response fields (Google: `ctr`, Meta: `link_clicks / impressions`).

---

## Blended CVR (cross-channel funnel)

`total_orders / total_sessions` — uses GA4 sessions as denominator.
This is the canonical definition per `session_conversion_rate` in `metrics.yml`.

---

## Attribution Windows

| Metric | Default window | Attribution model |
|--------|---------------|-------------------|
| Blended ROAS | 90-day | Linear |
| Channel ROAS | 90-day | Linear |
| Meta platform ROAS | 7-day click, 1-day view | Last-click |
| Google estimated ROAS | 30-day | Estimated last-click |
| GA4 CVR | 90-day | Session-level |
| CRM pipeline / closed won | All-time | N/A |

---

## Revenue Scopes

Three distinct scopes exist in this project. **Label each one explicitly.**

| Label | What it measures |
|-------|-----------------|
| `Attributed Revenue (90d)` | GA4-tracked orders in query period, linear attribution across paid channels |
| `Salesforce Closed Won (90d)` | SF opportunity revenue closed in the 90-day period |
| `CRM Closed Won (all-time)` | Lifetime HubSpot + Salesforce combined closed-won revenue |

---

## Funnel Stage Rules

Valid funnel ordering (each step must be ≤ the step above):

```
Sessions (GA4)
  └── Engaged Sessions (GA4)
        └── Conversions (GA4 events)
              └── Deals Won (CRM, 90-day)
```

**CRM Contacts is NOT a funnel stage.** It is an all-time lifetime count that will typically
exceed GA4 conversion counts because it spans all time and all sources.
Display CRM Contacts as a standalone KPI card labelled `(HubSpot all-time)`.

---

## Channel Attribution Normalisation

Attribution shares (pie/donut charts) must always sum to 100%.

```js
// Required before rendering
const total = attrData.reduce((s, d) => s + d.val, 0);
const normalised = attrData.map(d => ({
  ...d,
  val: parseFloat(((d.val / total) * 100).toFixed(1))
}));
```

---

## Spend Field Mapping

| Platform | MCP field name | Notes |
|----------|---------------|-------|
| Google Ads | `cost` | USD |
| Meta Ads | `spend` | USD |

---

## Reference Files

- `CLAUDE.md` (project root) — enforced rules for all dashboard generation
- `dbt_project/models/metrics/metrics.yml` — dbt metric definitions
- `dbt_project/macros/attribution_models.sql` — time-decay attribution macro (7-day half-life)
