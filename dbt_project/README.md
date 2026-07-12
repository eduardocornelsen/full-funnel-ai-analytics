# Full-Funnel AI Analytics — Architecture Documentation

> **Branch:** `claude/fix-dynamic-time-filtering-mE86T`  
> **Generated from audit:** May 2026  
> **Covers:** Medallion Architecture layers, MetricFlow semantic models, architecture summary, dbt CLI commands, AI agent internals

---

## Table of Contents

1. [Medallion Architecture Overview](#1-medallion-architecture-overview)
2. [Staging Layer](#2-staging-layer-materialized-as-view)
3. [Intermediate Layer](#3-intermediate-layer-materialized-as-ephemeral)
4. [Marts Layer](#4-marts-layer-materialized-as-table)
5. [MetricFlow Semantic Models](#5-metricflow-semantic-models)
6. [Metric Definitions](#6-metric-definitions)
7. [Architecture Summary Table](#7-architecture-summary-table)
8. [dbt CLI Command Reference](#8-dbt-cli-command-reference)
9. [AI Agent — Querying, Drift Prevention & Validation](#9-ai-agent--querying-drift-prevention--validation)

---

## 1. Medallion Architecture Overview

```
Raw Sources (CSV / DuckDB)
        │
        ▼
┌────────────────────────────────────────────────────────────────┐
│  STAGING  (view)                                               │
│  Typed, renamed, no business logic. One model per source.      │
│  Sources: Olist e-commerce + 6 marketing/CRM mock feeds        │
└────────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────────┐
│  INTERMEDIATE  (ephemeral)                                     │
│  Joins and reshaping. Not persisted — inlined at compile time. │
└────────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────────┐
│  MARTS  (table)                                                │
│  Fact and dimension tables. Business-ready grain.              │
│  Consumed by MetricFlow semantic models and dashboards.        │
└────────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────────┐
│  GOLDEN LAYER  (JSON snapshot)                                 │
│  dashboards/golden_metrics.json                                │
│  Pre-computed by scripts/generate_golden_metrics.py.           │
│  Single source of truth for all dashboard numbers.             │
└────────────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────────┐
│  DASHBOARDS  (HTML / JS)                                       │
│  Read golden_metrics.json. Compute nothing independently.      │
│  Runtime enforcement via dashboards/js/metrics.js              │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. Staging Layer (materialized as `view`)

All staging models sit under `dbt_project/models/staging/`. They cast types, rename columns, and surface clean data — no business logic or joins.

---

### `stg_orders`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_orders.sql` |
| **Source** | `olist.orders` |
| **Materialization** | `view` |
| **Upstream** | Raw `olist` source |
| **Downstream** | `int_customer_orders`, `int_funnel_stages`, `fct_orders` |

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| `order_id` | VARCHAR | Primary key. Unique order identifier. |
| `customer_id` | VARCHAR | FK to `stg_customers`. |
| `order_status` | VARCHAR | Lifecycle status: delivered, shipped, canceled, etc. |
| `order_purchase_timestamp` | TIMESTAMP | Raw purchase datetime. |
| `order_approved_at` | TIMESTAMP | Payment approval timestamp. |
| `order_delivered_carrier_date` | TIMESTAMP | Handed to carrier. |
| `order_delivered_customer_date` | TIMESTAMP | Delivered to customer. |
| `order_estimated_delivery_date` | TIMESTAMP | Estimated delivery. |
| `order_date` | DATE | `order_purchase_timestamp` cast to DATE. Join key for time dims. |
| `order_year` | INTEGER | Extracted year. |
| `order_month` | INTEGER | Extracted month. |
| `delivery_days` | INTEGER | Days from purchase to delivery (warehouse-dialect safe). |
| `is_late_delivery` | BOOLEAN | TRUE when `delivered_date > estimated_date`. |

**dbt Tests:**

| Column | Tests |
|--------|-------|
| `order_id` | `unique`, `not_null` |
| `customer_id` | `not_null` |
| `order_status` | `not_null`, `accepted_values` (8 values) |
| `order_date` | `not_null` |

---

### `stg_customers`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_customers.sql` |
| **Source** | `olist.customers` |
| **Materialization** | `view` |
| **Upstream** | Raw `olist` source |
| **Downstream** | `fct_orders`, `dim_customers`, `fct_lead_scoring_features` |

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| `customer_id` | VARCHAR | Order-scoped ID (one per order, not unique per person). |
| `customer_unique_id` | VARCHAR | Person-scoped ID — joins to `stg_hubspot_contacts`. |
| `customer_zip_code_prefix` | VARCHAR | 5-digit ZIP prefix. |
| `customer_city` | VARCHAR | Lowercased city name. |
| `customer_state` | VARCHAR | Brazilian state code. |

**dbt Tests:** `customer_id` (`unique`, `not_null`), `customer_state` (`not_null`)

---

### `stg_order_items`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_order_items.sql` |
| **Source** | `olist.order_items` |
| **Materialization** | `view` |
| **Downstream** | `fct_orders` |

**Key Columns:** `order_id`, `price`, `freight_value`, `product_id`, `seller_id`

**dbt Tests:** `order_id` (`not_null`), `price` (`not_null`)

---

### `stg_order_payments`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_order_payments.sql` |
| **Source** | `olist.order_payments` |
| **Materialization** | `view` |
| **Downstream** | `fct_orders`, `int_customer_orders` |

**Key Columns:** `order_id`, `payment_value`, `payment_type`

**dbt Tests:** `order_id` (`not_null`), `payment_value` (`not_null`), `payment_type` (`accepted_values`: credit_card, boleto, voucher, debit_card, not_defined)

---

### `stg_order_reviews`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_order_reviews.sql` |
| **Source** | `olist.order_reviews` |
| **Materialization** | `view` |
| **Downstream** | `fct_orders` |

**Key Columns:** `order_id`, `review_score` (1–5)

**dbt Tests:** `order_id` (`not_null`), `review_score` (`not_null`, `accepted_values`: 1, 2, 3, 4, 5)

---

### `stg_products`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_products.sql` |
| **Source** | `olist.products` |
| **Materialization** | `view` |
| **Downstream** | `dim_products` |

**dbt Tests:** `product_id` (`unique`, `not_null`)

---

### `stg_sellers`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_sellers.sql` |
| **Source** | `olist.sellers` |
| **Materialization** | `view` |

**dbt Tests:** `seller_id` (`unique`, `not_null`)

---

### `stg_ga4_sessions`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_ga4_sessions.sql` |
| **Source** | `marketing.ga4_daily_sessions` |
| **Materialization** | `view` |
| **Downstream** | `fct_marketing_daily`, `int_funnel_stages`, `sem: ga4_sessions` |

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| `date` | DATE | Session date. |
| `channel_group` | VARCHAR | GA4 channel grouping (e.g., Organic Search, Paid Social). |
| `device_category` | VARCHAR | Desktop / mobile / tablet. |
| `sessions` | INTEGER | Total sessions. |
| `engaged_sessions` | INTEGER | Sessions with >10s engagement or conversion. |
| `bounce_rate` | FLOAT | Sessions with single pageview. |
| `avg_session_duration_sec` | FLOAT | Mean session length. |
| `pages_per_session` | FLOAT | Mean pages viewed. |
| `new_users` | INTEGER | First-time visitors (top-of-funnel lead proxy). |
| `conversions` | INTEGER | GA4 conversion events (Session CVR numerator). |
| `revenue` | FLOAT | GA4-tracked revenue. |
| `conversion_rate` | FLOAT | Platform-reported CVR (informational; use `Metrics.sessionCVR()` for canonical). |
| `engagement_rate` | FLOAT | `engaged_sessions / sessions × 100` (computed in staging). |

**dbt Tests:** `date` (`not_null`), `channel_group` (`not_null`), `sessions` (`not_null`)

---

### `stg_google_ads_performance`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_google_ads_performance.sql` |
| **Source** | `marketing.google_ads_daily_performance` |
| **Materialization** | `view` |
| **Downstream** | `int_campaign_unified`, `dim_campaigns` |

**Key Columns:** `date`, `campaign_id`, `campaign_name`, `campaign_type`, `impressions`, `clicks`, `cost` (**not** `spend`), `conversions`, `conversion_value`, `ctr`, `avg_cpc`, `cost_per_conversion`, `roas`

> **Note:** Google Ads uses `cost` (not `spend`). Swapping these will silently break ROAS calculations. See CLAUDE.md §7.

**dbt Tests:** `date` (`not_null`), `campaign_id` (`not_null`), `cost` (`not_null`)

---

### `stg_meta_ads_performance`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_meta_ads_performance.sql` |
| **Source** | `marketing.meta_ads_daily_performance` |
| **Materialization** | `view` |
| **Downstream** | `int_campaign_unified`, `dim_campaigns` |

**Key Columns:** `date`, `campaign_id`, `campaign_name`, `objective`, `impressions`, `reach`, `spend` (**not** `cost`), `link_clicks`, `ctr`, `cpc`, `cpm`, `purchases`, `purchase_value`, `cost_per_purchase`, `roas`

> **Note:** Meta uses `spend` and `link_clicks` (not `clicks`). The platform-native `roas` field is the only correct ROAS source for Meta — do not recalculate.

**dbt Tests:** `date` (`not_null`), `campaign_id` (`not_null`), `spend` (`not_null`)

---

### `stg_hubspot_contacts`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_hubspot_contacts.sql` |
| **Source** | `marketing.hubspot_contacts` |
| **Materialization** | `view` |
| **Downstream** | `dim_customers`, `fct_lead_scoring_features` |

**Key Columns:** `contact_id`, `customer_id` (maps to `customer_unique_id`), `email`, `first_name`, `last_name`, `city`, `state`, `create_date`, `lifecycle_stage`, `lead_source`, `num_orders`, `total_revenue`, `first_order_date`, `last_activity_date`

**dbt Tests:** `contact_id` (`unique`, `not_null`), `lifecycle_stage` (`not_null`, `accepted_values`: 7 stages)

> **Critical:** HubSpot contacts are an **all-time count** — never use them as a funnel step after GA4 conversions. Display as a KPI card labelled `(HubSpot all-time)`.

---

### `stg_hubspot_deals`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_hubspot_deals.sql` |
| **Source** | `marketing.hubspot_deals` |
| **Materialization** | `view` |
| **Downstream** | `int_funnel_stages`, `fct_pipeline` |

**Key Columns:** `deal_id`, `order_id`, `deal_name`, `deal_stage`, `pipeline`, `amount`, `create_date`, `close_date`, `deal_type`, `lead_source`, `is_closed_won`

**dbt Tests:** `deal_id` (`unique`, `not_null`), `deal_stage` (`not_null`, `accepted_values`: 7 stages), `amount` (`not_null`)

---

### `stg_salesforce_opportunities`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_salesforce_opportunities.sql` |
| **Source** | `marketing.salesforce_opportunities` |
| **Materialization** | `view` |
| **Downstream** | `int_funnel_stages`, `fct_pipeline` |

**Key Columns:** `opportunity_id`, `order_id`, `opportunity_name`, `stage`, `probability`, `amount`, `created_date`, `close_date`, `lead_source`, `type`, `fiscal_quarter`, `is_won`, `weighted_amount`

**dbt Tests:** `opportunity_id` (`unique`, `not_null`), `stage` (`not_null`, `accepted_values`: 8 stages), `probability` (`not_null`)

---

### `stg_marketing_attribution`

| Property | Value |
|----------|-------|
| **File** | `models/staging/stg_marketing_attribution.sql` |
| **Source** | `marketing.marketing_attribution` |
| **Materialization** | `view` |
| **Downstream** | `int_funnel_stages`, `fct_marketing_attribution`, `sem: orders` (indirect) |

**Columns:**

| Column | Type | Description |
|--------|------|-------------|
| `order_id` | VARCHAR | FK to `stg_orders`. |
| `touchpoint_position` | INTEGER | 1 = first touch, N = last touch. |
| `total_touchpoints` | INTEGER | Total touchpoints in this order's path. |
| `channel` | VARCHAR | Granular channel (e.g., `google_ads_search`, `meta_prospecting`). |
| `platform` | VARCHAR | Platform identifier (`google_ads`, `meta_ads`). |
| `touchpoint_date` | DATE | Date this touchpoint fired. |
| `order_date` | DATE | Date the order converted. |
| `order_revenue` | FLOAT | Total order revenue (used as the weight for attribution credits). |
| `first_touch_credit` | FLOAT | 0 or 1 — 1 only for the first touchpoint. |
| `last_touch_credit` | FLOAT | 0 or 1 — 1 only for the last touchpoint. |
| `linear_credit` | FLOAT | `1 / total_touchpoints` — equal share per touchpoint. |

**dbt Tests:** `order_id` (`not_null`), `channel` (`not_null`)

---

## 3. Intermediate Layer (materialized as `ephemeral`)

Ephemeral models are not persisted to the warehouse. dbt inlines their SQL as a CTE inside any downstream model that references them. They exist purely to reduce duplication and improve readability.

---

### `int_campaign_unified`

| Property | Value |
|----------|-------|
| **File** | `models/intermediate/int_campaign_unified.sql` |
| **Materialization** | `ephemeral` |
| **Upstream** | `stg_google_ads_performance`, `stg_meta_ads_performance` |
| **Downstream** | `fct_marketing_daily`, `fct_channel_performance`, `dim_campaigns` |

**What it does:** `UNION ALL` of Google Ads and Meta Ads daily rows. Normalises column names so downstream models can treat both platforms uniformly. Key normalisation: Meta's `link_clicks` → `clicks`, `spend` → `spend`; Google's `cost` → `spend`.

**Key Columns:** `date`, `platform` (`google_ads` or `meta_ads`), `campaign_name`, `campaign_category`, `impressions`, `clicks`, `spend`, `conversions`, `revenue`, `roas`

---

### `int_customer_orders`

| Property | Value |
|----------|-------|
| **File** | `models/intermediate/int_customer_orders.sql` |
| **Materialization** | `ephemeral` |
| **Upstream** | `stg_orders` (delivered only), `stg_order_payments` |
| **Downstream** | `int_customer_ltv` |

**What it does:** Aggregates order history to one row per customer. Computes LTV building blocks.

**Key Columns:** `customer_id`, `first_order_date`, `last_order_date`, `total_orders`, `total_revenue`, `avg_order_value`, `avg_days_between_orders` (dialect-safe: BigQuery/Postgres/DuckDB branches)

---

### `int_customer_ltv`

| Property | Value |
|----------|-------|
| **File** | `models/intermediate/int_customer_ltv.sql` |
| **Materialization** | `ephemeral` |
| **Upstream** | `int_customer_orders` |
| **Downstream** | `dim_customers`, `fct_lead_scoring_features` |

**What it does:** Applies segmentation rules on top of `int_customer_orders`. Adds `customer_segment` and `is_high_value`.

**Key Columns:** `customer_id`, `total_orders`, `total_revenue`, `avg_order_value`, `first_order_date`, `last_order_date`, `customer_segment` (vip / returning / new), `is_high_value` (1/0)

---

### `int_funnel_stages`

| Property | Value |
|----------|-------|
| **File** | `models/intermediate/int_funnel_stages.sql` |
| **Materialization** | `ephemeral` |
| **Upstream** | `stg_orders`, `stg_marketing_attribution`, `stg_ga4_sessions`, `stg_hubspot_deals`, `stg_salesforce_opportunities` |
| **Downstream** | Previously `fct_pipeline`; after audit rewrite, `fct_pipeline` sources directly from staging — `int_funnel_stages` is currently unreferenced. |

**What it does:** Joins every order to its first attribution touchpoint, HubSpot deal, and Salesforce opportunity. Useful for cross-system funnel analysis.

**Key Columns:** `order_id`, `customer_id`, `order_date`, `attribution_channel`, `attribution_platform`, `touchpoint_date`, `hubspot_deal_id`, `hubspot_stage`, `sf_opportunity_id`, `sf_stage`, `order_status`, `order_purchase_timestamp`

---

### `int_dates`

| Property | Value |
|----------|-------|
| **File** | `models/intermediate/int_dates.sql` |
| **Materialization** | `ephemeral` |
| **Upstream** | None (generates a date range via `range()`) |
| **Downstream** | None (unreferenced — the MetricFlow spine is `metricflow_time_spine`) |

> **Audit note:** This model previously had a stale hardcoded range (2016–2020). After the fix it uses the same `var("time_spine_start")` / `var("time_spine_end")` as `metricflow_time_spine.sql`, but remains unreferenced. It is retained as a utility that intermediate models can optionally join to; it is NOT the MetricFlow spine.

---

## 4. Marts Layer (materialized as `table`)

Mart models are persisted DuckDB tables. They are the direct source for MetricFlow semantic models and the golden-layer Python script.

---

### `fct_orders`

| Property | Value |
|----------|-------|
| **File** | `models/marts/fct_orders.sql` |
| **Materialization** | `table` |
| **Upstream** | `stg_orders`, `stg_order_items`, `stg_order_payments`, `stg_order_reviews`, `stg_customers`, `stg_marketing_attribution` |
| **Downstream** | `fct_daily_revenue`, `sem: orders` |

**Grain:** One row per delivered order.

**Key Columns:** `order_id`, `customer_id`, `order_date`, `order_year`, `order_month`, `order_status`, `delivery_days`, `is_late_delivery`, `item_count`, `items_total`, `freight_total`, `revenue`, `primary_payment_type`, `review_score`, `positive_review`, `customer_city`, `customer_state`, `first_touch_channel`, `last_touch_channel`, `touchpoint_count`

**dbt Tests:** `order_id` (`not_null`), `customer_id` (`not_null`), `order_date` (`not_null`), `revenue` (`not_null`)

---

### `fct_marketing_daily`

| Property | Value |
|----------|-------|
| **File** | `models/marts/fct_marketing_daily.sql` |
| **Materialization** | `table` |
| **Upstream** | `metricflow_time_spine`, `int_campaign_unified`, `stg_ga4_sessions` |
| **Downstream** | `sem: marketing_daily`, `generate_golden_metrics.py` |

**Grain:** One row per calendar day (driven by `metricflow_time_spine` — no gaps on zero-campaign days).

**Window:** spans the full source data range by default (bounds derived from the data — no literal dates). `var("window_start")` / `var("window_end")` remain as explicit overrides for pinned snapshots. Windowing (90d etc.) happens at query time in `generate_golden_metrics.py` / `query_window.py`; an unfiltered `SELECT` or unfiltered MetricFlow query against this mart is ALL-TIME scoped and must be labelled as such.

**Key Columns:** `date`, `total_google_spend`, `total_meta_spend`, `total_spend`, `total_ad_conversions`, `total_conversions`, `ga4_total_sessions`, `ga4_engaged_sessions`, `blended_cac`, `cost_per_session`

**dbt Tests:** `date` (`not_null`), `total_spend` (`not_null`)

---

### `fct_marketing_attribution`

| Property | Value |
|----------|-------|
| **File** | `models/marts/fct_marketing_attribution.sql` |
| **Materialization** | `table` |
| **Upstream** | `stg_marketing_attribution` |
| **Downstream** | `fct_channel_performance`, `generate_golden_metrics.py` (via staging directly for window filtering) |

**Grain:** One row per `order_date × channel` (daily × channel). Previously channel-only; `order_date` added in this audit to enable time filtering.

**Key Columns:** `order_date`, `channel`, `first_touch_revenue`, `last_touch_revenue`, `linear_revenue`, `time_decay_revenue`, `total_orders`

**dbt Tests:** `channel` (`unique`, `not_null`), `first_touch_revenue` (`not_null`), `last_touch_revenue` (`not_null`), `linear_revenue` (`not_null`), `time_decay_revenue` (`not_null`)

---

### `fct_channel_performance`

| Property | Value |
|----------|-------|
| **File** | `models/marts/fct_channel_performance.sql` |
| **Materialization** | `table` |
| **Upstream** | `int_campaign_unified`, `fct_marketing_attribution` |
| **Downstream** | `sem: channel_performance`, `generate_golden_metrics.py` |

**Grain:** One row per `date × channel` (daily × platform). Previously channel-only; `date` added in this audit so MetricFlow can apply time-window filters on `channel_roas`, `channel_spend`, and `customer_acquisition_cost`.

**Key Columns:** `date`, `channel`, `total_spend`, `attributed_revenue`, `total_orders`, `cac`, `roas`

**dbt Tests:** `channel` (`unique`, `not_null`), `total_spend` (`not_null`), `attributed_revenue` (`not_null`)

---

### `fct_pipeline`

| Property | Value |
|----------|-------|
| **File** | `models/marts/fct_pipeline.sql` |
| **Materialization** | `table` |
| **Upstream** | `stg_hubspot_deals`, `stg_salesforce_opportunities` |
| **Downstream** | `sem: pipeline` |

**Grain:** One row per deal / opportunity (deal-level). Previously a pre-aggregated channel summary — completely rewritten in this audit to match the `pipeline` semantic model's expected schema (`deal_id`, `close_date`, `amount`, `stage`, `source`, `lead_source`).

**Key Columns:** `deal_id`, `stage`, `source` (`hubspot` or `salesforce`), `lead_source`, `amount`, `close_date`

**dbt Tests:** `attribution_channel` (`unique`, `not_null`)

---

### `fct_daily_revenue`

| Property | Value |
|----------|-------|
| **File** | `models/marts/fct_daily_revenue.sql` |
| **Materialization** | `table` |
| **Upstream** | `fct_orders` |
| **Downstream** | Standalone reporting |

**Grain:** One row per `order_date`.

**Key Columns:** `order_date`, `order_count`, `total_revenue`, `avg_order_value`, `unique_customers`, `new_customers`

**dbt Tests:** `order_date` (`unique`, `not_null`), `total_revenue` (`not_null`)

---

### `fct_lead_scoring_features`

| Property | Value |
|----------|-------|
| **File** | `models/marts/fct_lead_scoring_features.sql` |
| **Materialization** | `table` |
| **Upstream** | `int_customer_ltv`, `stg_customers`, `stg_hubspot_contacts` |
| **Downstream** | XGBoost lead-scoring ML model (`ml/`) |

**Grain:** One row per customer.

**Key Columns:** `customer_id`, `lead_source`, `total_orders`, `total_revenue`, `avg_order_value`, `customer_segment`, `customer_state`, `is_high_value`

**dbt Tests:** `customer_id` (`unique`, `not_null`), `total_orders` (`not_null`), `is_high_value` (`not_null`)

---

### `dim_campaigns`

| Property | Value |
|----------|-------|
| **File** | `models/marts/dim_campaigns.sql` |
| **Materialization** | `table` |
| **Upstream** | `stg_google_ads_performance`, `stg_meta_ads_performance` |

**Grain:** One row per `campaign_id × platform` combination.

**Key Columns:** `campaign_id`, `campaign_name`, `platform`, `campaign_category`

**dbt Tests:** `campaign_id` (`not_null`)

---

### `dim_customers`

| Property | Value |
|----------|-------|
| **File** | `models/marts/dim_customers.sql` |
| **Materialization** | `table` |
| **Upstream** | `stg_customers`, `int_customer_ltv`, `stg_hubspot_contacts` |

**Grain:** One row per customer.

**Key Columns:** `customer_id`, `customer_unique_id`, `email`, `first_name`, `last_name`, `customer_city`, `customer_state`, `lead_source`, `lead_create_date`, `total_orders`, `total_revenue`, `avg_order_value`, `customer_segment`, `is_high_value`

**dbt Tests:** `customer_id` (`unique`, `not_null`), `customer_state` (`not_null`)

---

### `metricflow_time_spine`

| Property | Value |
|----------|-------|
| **File** | `models/marts/metricflow_time_spine.sql` |
| **Materialization** | `table` |
| **Upstream** | None (generates dates via `generate_series()`) |
| **Downstream** | `fct_marketing_daily`, MetricFlow time-grain aggregation engine |

**Grain:** One row per calendar day from `var("time_spine_start")` to `var("time_spine_end")`.

**Key Columns:** `date_day` (DATE)

**Purpose:** MetricFlow requires this model to perform any time-grain roll-up (week, month, quarter). Without it, `mf query --group-by metric_time__week` fails. Previously used hardcoded `'2024-01-01'` / `'2026-12-31'` literals — now driven by `dbt_project.yml` vars.

**dbt Tests:** `date_day` (`unique`, `not_null`)

---

## 5. MetricFlow Semantic Models

All semantic models live in `dbt_project/models/semantic_models/sem_marketing.yml`.  
MetricFlow time spine reference: `metricflow_time_spine` (column: `date_day`).

---

### `marketing_daily`

```yaml
name: marketing_daily
model: ref('fct_marketing_daily')
defaults:
  agg_time_dimension: date
entities:
  - name: marketing_day
    type: primary
    expr: date
dimensions:
  - name: date
    type: time
    type_params:
      time_granularity: day
measures:
  - name: total_spend         # agg: sum  | expr: total_spend
  - name: total_conversions   # agg: sum  | expr: total_conversions   (GA4 — Session CVR numerator)
  - name: total_sessions      # agg: sum  | expr: ga4_total_sessions  (Session CVR denominator)
  - name: total_ad_conversions# agg: sum  | expr: total_ad_conversions (Click CVR numerator)
  - name: engaged_sessions    # agg: sum  | expr: ga4_engaged_sessions
```

**Metrics backed by this semantic model:** `total_spend`, `total_sessions`, `total_clicks`, `total_engaged_sessions`, `blended_roas` (numerator via `orders`), `session_conversion_rate` (via `orders`), `engagement_rate`, `cost_per_session`

**Time grain support:** `day`, `week`, `month`, `quarter`, `year`

---

### `orders`

```yaml
name: orders
model: ref('fct_orders')
defaults:
  agg_time_dimension: order_date
entities:
  - name: order
    type: primary
    expr: order_id
  - name: customer
    type: foreign
    expr: customer_id
dimensions:
  - name: order_date
    type: time
    type_params:
      time_granularity: day
  - name: last_touch_channel   # type: categorical
  - name: payment_type         # type: categorical
  - name: order_status         # type: categorical
measures:
  - name: revenue      # agg: sum      | expr: revenue
  - name: order_count  # agg: count_distinct | expr: order_id
  - name: avg_order_value # agg: average | expr: revenue
```

**Metrics backed:** `total_revenue`, `total_orders`, `average_order_value`, `blended_roas` (denominator shared with `marketing_daily`)

**Time grain support:** `day`, `week`, `month`, `quarter`, `year`

---

### `channel_performance`  *(time dimension added in this audit)*

```yaml
name: channel_performance
model: ref('fct_channel_performance')
defaults:
  agg_time_dimension: date           # ADDED — was missing; blocked all time filtering
entities:
  - name: channel_date
    type: primary
    expr: "channel || '_' || CAST(date AS VARCHAR)"   # ADDED — composite key for daily×channel grain
dimensions:
  - name: date                        # ADDED — enables MetricFlow time-window queries
    type: time
    type_params:
      time_granularity: day
  - name: channel
    type: categorical
measures:
  - name: channel_spend    # agg: sum | expr: total_spend
  - name: channel_revenue  # agg: sum | expr: attributed_revenue
  - name: channel_orders   # agg: sum | expr: total_orders
```

**Metrics backed:** `channel_spend`, `channel_revenue`, `channel_orders`, `channel_roas`, `customer_acquisition_cost`

**Time grain support:** `day`, `week`, `month`, `quarter`, `year` *(was: none — all-time only before fix)*

---

### `ga4_sessions`

```yaml
name: ga4_sessions
model: ref('stg_ga4_sessions')
defaults:
  agg_time_dimension: date
entities:
  - name: session_day_channel
    type: primary
    expr: "date || '_' || channel_group"
dimensions:
  - name: date
    type: time
    type_params:
      time_granularity: day
  - name: channel_group       # type: categorical
measures:
  - name: sessions            # agg: sum | expr: sessions
  - name: engaged_sessions    # agg: sum | expr: engaged_sessions
  - name: new_users           # agg: sum | expr: new_users
  - name: conversions         # agg: sum | expr: conversions
```

**Metrics backed:** `total_sessions`, `total_new_users`, `total_engaged_sessions`, `session_conversion_rate` (partial)

**Time grain support:** `day`, `week`, `month`, `quarter`, `year`

---

### `pipeline`  *(completely rewritten in this audit)*

```yaml
name: pipeline
model: ref('fct_pipeline')
defaults:
  agg_time_dimension: close_date
entities:
  - name: deal
    type: primary
    expr: deal_id
dimensions:
  - name: close_date
    type: time
    type_params:
      time_granularity: day
  - name: stage         # type: categorical
  - name: source        # type: categorical  (hubspot / salesforce)
  - name: lead_source   # type: categorical
measures:
  - name: pipeline_value  # agg: sum            | expr: amount
  - name: deal_count      # agg: count_distinct | expr: deal_id
```

**Metrics backed:** `total_pipeline_value`, `total_deals`

**Time grain support:** `day`, `week`, `month`, `quarter`, `year` *(was: none — model had wrong schema before fix)*

---

## 6. Metric Definitions

All metrics are defined in `dbt_project/models/metrics/metrics.yml`.

### Simple Metrics

| Metric | Measure | Semantic Model | Description |
|--------|---------|----------------|-------------|
| `total_revenue` | `revenue` | `orders` | Sum of attributed order revenue |
| `total_spend` | `total_spend` | `marketing_daily` | Sum of all paid media spend |
| `total_sessions` | `sessions` | `ga4_sessions` | All GA4 web sessions |
| `total_clicks` | `total_ad_conversions` | `marketing_daily` | Ad-platform conversion proxy |
| `total_new_users` | `new_users` | `ga4_sessions` | First-time visitors |
| `total_engaged_sessions` | `engaged_sessions` | `ga4_sessions` | Sessions with meaningful engagement |
| `total_orders` | `order_count` | `orders` | Count of completed orders |
| `average_order_value` | `avg_order_value` | `orders` | Mean revenue per order |
| `total_pipeline_value` | `pipeline_value` | `pipeline` | Sum of all CRM deal amounts |
| `total_deals` | `deal_count` | `pipeline` | Count of CRM deals/opportunities |
| `channel_spend` | `channel_spend` | `channel_performance` | Spend by paid channel |
| `channel_revenue` | `channel_revenue` | `channel_performance` | Linear-attributed revenue by channel |
| `channel_orders` | `channel_orders` | `channel_performance` | Orders attributed by channel |

### Derived Metrics

| Metric | Formula | UI Label |
|--------|---------|----------|
| `blended_roas` | `total_revenue / NULLIF(total_spend, 0)` | Blended ROAS · Linear · 90d |
| `channel_roas` | `channel_revenue / NULLIF(channel_spend, 0)` | Channel ROAS · Linear · 90d |
| `customer_acquisition_cost` | `channel_spend / NULLIF(channel_orders, 0)` | CAC |
| `cost_per_session` | `total_spend / NULLIF(total_sessions, 0)` | Cost per Session |
| `engagement_rate` | `total_engaged_sessions / NULLIF(total_sessions, 0)` | Engagement Rate |
| `session_conversion_rate` | `total_orders / NULLIF(total_sessions, 0)` | CVR (session) |

All derived metrics use `fill_nulls_with: 0` on component measures (added in this audit) and `NULLIF(denominator, 0)` in `expr` to prevent silent divide-by-zero.

---

## 7. Architecture Summary Table

| Layer | Model | Type | Key Columns | Metrics Exposed | Time Grain Support |
|-------|-------|------|-------------|-----------------|-------------------|
| **Staging** | `stg_orders` | view | order_id, customer_id, order_date, revenue | — | — |
| **Staging** | `stg_customers` | view | customer_id, customer_unique_id, customer_state | — | — |
| **Staging** | `stg_ga4_sessions` | view | date, channel_group, sessions, conversions | — | — |
| **Staging** | `stg_google_ads_performance` | view | date, campaign_id, cost, conversions | — | — |
| **Staging** | `stg_meta_ads_performance` | view | date, campaign_id, spend, purchases, roas | — | — |
| **Staging** | `stg_hubspot_deals` | view | deal_id, deal_stage, amount, close_date | — | — |
| **Staging** | `stg_salesforce_opportunities` | view | opportunity_id, stage, amount, close_date | — | — |
| **Staging** | `stg_marketing_attribution` | view | order_id, channel, touchpoint_date, linear_credit | — | — |
| **Staging** | `stg_hubspot_contacts` | view | contact_id, lifecycle_stage, lead_source | — | — |
| **Intermediate** | `int_campaign_unified` | ephemeral | date, platform, spend, conversions | — | — |
| **Intermediate** | `int_customer_orders` | ephemeral | customer_id, total_orders, total_revenue | — | — |
| **Intermediate** | `int_customer_ltv` | ephemeral | customer_id, customer_segment, is_high_value | — | — |
| **Intermediate** | `int_funnel_stages` | ephemeral | order_id, attribution_channel, hubspot_deal_id | — | — |
| **Intermediate** | `int_dates` | ephemeral | date_day | — | — (unreferenced) |
| **Marts** | `fct_orders` | table | order_id, order_date, revenue, last_touch_channel | `total_revenue`, `total_orders`, `average_order_value` | day → year |
| **Marts** | `fct_marketing_daily` | table | date, total_spend, ga4_total_sessions, total_conversions | `total_spend`, `total_sessions`, `engagement_rate` | day → year |
| **Marts** | `fct_marketing_attribution` | table | order_date, channel, linear_revenue, total_orders | Feeds `fct_channel_performance` | day → year |
| **Marts** | `fct_channel_performance` | table | date, channel, total_spend, attributed_revenue | `channel_roas`, `channel_spend`, `customer_acquisition_cost` | day → year ✅ |
| **Marts** | `fct_pipeline` | table | deal_id, stage, source, amount, close_date | `total_pipeline_value`, `total_deals` | day → year ✅ |
| **Marts** | `fct_daily_revenue` | table | order_date, total_revenue, new_customers | Standalone reporting | — |
| **Marts** | `fct_lead_scoring_features` | table | customer_id, customer_segment, is_high_value | ML feature store | — |
| **Marts** | `dim_campaigns` | table | campaign_id, campaign_name, platform | — | — |
| **Marts** | `dim_customers` | table | customer_id, customer_segment, total_revenue | — | — |
| **Marts** | `metricflow_time_spine` | table | date_day | Time spine for all MetricFlow queries | All grains |
| **Semantic** | `marketing_daily` | — | date (time), marketing_day (entity) | total_spend, total_sessions, engagement_rate | day → year |
| **Semantic** | `orders` | — | order_date (time), order (entity), customer (FK) | total_revenue, total_orders, avg_order_value | day → year |
| **Semantic** | `channel_performance` | — | date (time), channel (categorical) | channel_roas, channel_spend, CAC | day → year ✅ |
| **Semantic** | `ga4_sessions` | — | date (time), channel_group (categorical) | total_sessions, total_new_users | day → year |
| **Semantic** | `pipeline` | — | close_date (time), stage/source (categorical) | total_pipeline_value, total_deals | day → year ✅ |

> ✅ = Time grain support added in this audit (was all-time only before)

---

## 8. dbt CLI Command Reference

### Generate and Serve the Full Docs DAG Locally

```bash
# Step 1 — Generate the docs artefact (JSON catalog + manifest)
dbt docs generate --project-dir dbt_project

# Step 2 — Serve the interactive DAG browser on localhost:8080
dbt docs serve --project-dir dbt_project --port 8080
```

> Opens a browser with the full lineage DAG, model descriptions, column-level docs, and test results. Click any node to see upstream/downstream lineage, SQL, and schema.

---

### Run Only the Semantic Layer Models

```bash
# Materialise only the mart models that back MetricFlow semantic models.
# +tag:semantic would also work if models are tagged.
dbt run --project-dir dbt_project \
    --select fct_marketing_daily fct_orders fct_channel_performance fct_pipeline metricflow_time_spine
```

> Run these before querying with `mf query`. MetricFlow reads from the materialised tables — it does not compile dbt on the fly.

---

### Test Only the Mart Layer

```bash
# Run schema tests only on mart models (not staging or intermediate)
dbt test --project-dir dbt_project --select marts

# Run a specific model's tests
dbt test --project-dir dbt_project --select fct_channel_performance

# Show test results without rerunning (requires a prior dbt build)
dbt test --project-dir dbt_project --select marts --store-failures
```

---

### Show Lineage for a Specific Metric

```bash
# MetricFlow: show what SQL a metric compiles to (validates semantic model config)
mf compile --metrics blended_roas
mf compile --metrics channel_roas
mf compile --metrics customer_acquisition_cost

# dbt: show upstream lineage for a model that backs a metric
dbt ls --project-dir dbt_project --select +fct_channel_performance --output path
# Shows: stg_google_ads_performance → int_campaign_unified → fct_marketing_attribution → fct_channel_performance

# dbt: show all models that depend on fct_marketing_attribution (downstream)
dbt ls --project-dir dbt_project --select fct_marketing_attribution+ --output path
```

> The `+` prefix means "and all upstream"; `+` suffix means "and all downstream".

---

### MetricFlow Query Examples (canonical date-filtered queries)

```bash
# Blended ROAS for the 90-day canonical window
mf query --metrics blended_roas \
    --start-time 2025-12-16 --end-time 2026-03-15

# Channel ROAS broken down by channel and grouped by month
mf query --metrics channel_roas \
    --group-by channel metric_time__month \
    --start-time 2025-12-16 --end-time 2026-03-15

# Session CVR by week
mf query --metrics session_conversion_rate \
    --group-by metric_time__week \
    --start-time 2025-12-16 --end-time 2026-03-15

# Pipeline value by stage and quarter
mf query --metrics total_pipeline_value \
    --group-by stage metric_time__quarter \
    --start-time 2025-12-16 --end-time 2026-03-15

# CAC per channel per month
mf query --metrics customer_acquisition_cost \
    --group-by channel metric_time__month \
    --start-time 2025-12-16 --end-time 2026-03-15
```

---

### Other Relevant dbt Commands

```bash
# Compile all models to SQL (without running) — useful for reviewing generated SQL
dbt compile --project-dir dbt_project

# Run a specific model and all its upstream dependencies
dbt run --project-dir dbt_project --select +fct_channel_performance

# Run with a custom date window (override vars defined in dbt_project.yml)
dbt run --project-dir dbt_project \
    --vars '{"window_start":"2025-06-01","window_end":"2025-09-01"}'

# Freshness check — reports how old the source data is
dbt source freshness --project-dir dbt_project

# Debug project config (profiles, adapters, var resolution)
dbt debug --project-dir dbt_project

# List all metrics defined in the project
mf list metrics

# List all dimensions available for a metric
mf list dimensions --metrics blended_roas

# Validate the MetricFlow semantic graph (catches column mismatches early)
mf validate-configs

# Show MetricFlow query plan without executing (dry-run)
mf explain --metrics channel_roas \
    --group-by channel metric_time__month \
    --start-time 2025-12-16 --end-time 2026-03-15
```

---

### Additional Relevant dbt Properties

Beyond the commands above, these dbt features are relevant to this project:

| Feature | How it applies here |
|---------|---------------------|
| `dbt_project.yml` `vars` | Date windows (`window_start`, `window_end`, `time_spine_start`, `time_spine_end`) centralised here — no hardcoded dates in SQL |
| `+materialized` config | Staging = `view` (no storage cost), Intermediate = `ephemeral` (inlined), Marts = `table` (persisted for MetricFlow) |
| `source freshness` | Sources define `loaded_at_field` and `freshness:` thresholds so `dbt source freshness` alerts on stale feeds |
| `accepted_values` test | Enforces controlled vocabularies on `order_status`, `payment_type`, `deal_stage`, `lifecycle_stage` |
| `ref()` vs `source()` | Staging models use `source()` to reference raw tables; all other models use `ref()` so dbt can build the DAG |
| `--select` graph operators | `+model` (upstream), `model+` (downstream), `model1 model2` (explicit set), `tag:foo` (tagged models) |
| `--store-failures` | Persists failed test rows to a schema for debugging — especially useful for `accepted_values` and `unique` failures |
| `mf validate-configs` | MetricFlow-specific: validates that every semantic model's `model`, `entities`, `dimensions`, and `measures` resolve correctly before any query runs |

---

## 9. AI Agent — Querying, Drift Prevention & Validation

This section answers three questions about how the AI agent interacts with this data system.

---

### 9.1 How the AI Agent Queries the Semantic Layer

The agent operates in **two distinct modes** controlled by a decision tree in `CLAUDE.md §14`:

```
User asks for a dashboard or metric
        │
        ├─ User says "live", "real-time", "bypass golden", or uses a "-mcp" skill?
        │   └─ YES → Path B: Live MCP Query
        │
        └─ NO (default)
            └─ Path A: Read dashboards/golden_metrics.json
```

#### Path A — Golden Layer (Default)

The agent reads `dashboards/golden_metrics.json`, a pre-computed JSON snapshot, and **copies exact values** into dashboard JS constants — it does not recalculate anything.

The file is produced by `scripts/generate_golden_metrics.py`, which queries DuckDB mart tables directly with parameterised date bounds:

```
dbt run
  → materialises tables in data/olist_analytics.duckdb

python scripts/generate_golden_metrics.py
  → reads dbt_project/dbt_project.yml vars (window_start / window_end)
  → queries DuckDB with: WHERE date BETWEEN ? AND ?
  → writes dashboards/golden_metrics.json
```

The JSON has two root sections the agent uses:

| Key | Contents | When to use |
|-----|----------|-------------|
| `windowed_90d` | All metrics scoped to `window_start` → `window_end` | Default 90-day views |
| `all_time` | Metrics over full dataset range | Lifetime / CRM views only |

The `_meta` block records `window_start`, `window_end`, `generated_at`, `schema_version`, and `google_aov` so every snapshot is fully auditable.

> **Why pre-compute instead of query live?**  
> If the agent recalculates from MCP data, floating-point rounding differences and non-deterministic AI arithmetic introduce drift versus the golden layer. Copying pre-computed values guarantees bit-for-bit reproducibility between runs.

#### Path B — Live MCP Query (Opt-in Only)

Triggered by the user saying "query live data", "bypass golden", or running a `-mcp` skill. The agent calls mock MCP server tools (`google-ads`, `meta-ads`, `ga4`, `hubspot`, `salesforce`) with **explicit canonical dates** as arguments:

```
Synthetic dataset:  start_date=2025-12-16, end_date=2026-03-15  (fixed anchor)
Live dataset:       start_date=today()-90,  end_date=today()     (rolling window)
```

Raw MCP responses are then processed through `dashboards/js/metrics.js` canonical functions — never computed inline. The dashboard header shows an `⚡ Live MCP` badge.

---

### 9.2 How the Agent Prevents Metric Drift

Metric drift — the same metric returning different numbers in different places — is blocked at **four independent enforcement layers**, each targeting a different failure mode.

#### Layer 1 — dbt Semantic Layer (Definition Governance)

`dbt_project/models/metrics/metrics.yml` is the single authoritative definition for every metric formula. Example:

```yaml
- name: session_conversion_rate
  type: derived
  type_params:
    expr: "total_orders / NULLIF(total_sessions, 0)"
    metrics:
      - name: total_orders
        fill_nulls_with: 0
      - name: total_sessions
        fill_nulls_with: 0
```

This one definition feeds MetricFlow query validation, the Python golden-layer script, and the `metrics.js` module. `CLAUDE.md §12` mandates: *"When in doubt about a metric formula, read that file."*

#### Layer 2 — Golden Layer Pre-computation (Arithmetic Freeze)

`generate_golden_metrics.py` computes each metric once with a fixed date window and serialises the result to `golden_metrics.json`. The agent is mandated by `CLAUDE.md §14` to copy those values, never recompute them:

> *"Copy exact values from this file into HTML dashboard JS constants. Do NOT recalculate metrics independently."*

The `_meta` block with `schema_version` and `generated_at` makes each snapshot auditable.

#### Layer 3 — `metrics.js` Runtime Enforcement (Browser-side)

`dashboards/js/metrics.js` is the **mandatory** runtime module — all HTML dashboards must load it before any inline script. It exposes only canonical formula implementations. Dashboards cannot accidentally implement their own CVR or ROAS logic:

```javascript
// Google ROAS: conversions × $100 AOV / cost — NEVER spend × multiplier
function googleROAS(conversions, cost) {
  if (!cost || cost === 0) return 0;
  return parseFloat(((conversions * AOV) / cost).toFixed(2));
}
```

The `labels` object enforces consistent attribution window strings across every KPI card so every dashboard shows the same subtitle text.

#### Layer 4 — CLAUDE.md Hard Rules (Instruction-level Enforcement)

`CLAUDE.md` contains explicit prohibitions loaded into every conversation:

| Rule | Protection |
|------|-----------|
| `§ROAS` | Never use a hardcoded spend multiplier (e.g. `spend × 3.5`) |
| `§CVR` | Never mix session CVR and click CVR on the same chart without labelling |
| `§Channel Attribution` | Attribution shares must normalise to exactly 100% before rendering |
| `§Funnel` | Each funnel step must be ≤ the step above it; CRM Contacts cannot appear as a funnel stage after GA4 Conversions |
| `§Revenue Scopes` | Never divide all-time revenue by 90-day spend (this was the source of the 71.1× ROAS bug) |
| `§Never mix scopes` | `windowed_90d` numbers must never mix with `all_time` numbers in the same calculation |

These are not guidelines — `CLAUDE.md` opens with: *"All rules here are mandatory."*

---

### 9.3 How the Agent Tests and Validates Itself

Testing runs at **four independent checkpoints**, each catching a different class of failure.

#### Checkpoint A — dbt Build + Tests (SQL layer)

```bash
dbt build --select marts
```

Every mart model in `models/marts/schema.yml` has dbt schema tests. Examples:

```yaml
- name: fct_orders
  columns:
    - name: order_id
      tests: [unique, not_null]    # catches duplicate orders
    - name: revenue
      tests: [not_null]            # catches broken payment joins

- name: fct_channel_performance
  columns:
    - name: channel
      tests: [unique, not_null]    # catches channel mapping regressions
```

Staging models additionally use `accepted_values` tests on `order_status`, `payment_type`, `deal_stage`, and `lifecycle_stage`. These run on every `dbt build` and fail loudly before any downstream model is materialised.

#### Checkpoint B — MetricFlow Compile Validation (Semantic layer)

```bash
mf validate-configs
mf compile --metrics blended_roas
mf compile --metrics channel_roas
```

MetricFlow validates before executing:
- The measure exists in the referenced semantic model
- Entity join keys are defined
- `agg_time_dimension` exists as a `time` type dimension on the model
- `fill_nulls_with` is set before ratio arithmetic across sparse time windows

If any semantic model is misconfigured (e.g., a column mismatch like the `fct_pipeline` issue found in the audit), MetricFlow raises a compile error before any SQL reaches the warehouse.

#### Checkpoint C — `metrics.js` `validateFunnel()` Runtime Check

Every dashboard that renders a funnel calls `Metrics.validateFunnel(steps)` before drawing:

```javascript
// metrics.js
function validateFunnel(steps) {
  const issues = [];
  for (let i = 1; i < steps.length; i++) {
    if (steps[i].val > steps[i - 1].val) {
      issues.push(
        `Funnel integrity error: "${steps[i].label}" (${steps[i].val.toLocaleString()}) ` +
        `> "${steps[i - 1].label}" (${steps[i - 1].val.toLocaleString()})`
      );
    }
  }
  return issues;
}
```

`issues.length > 0` means the funnel violates the ordering constraint (each step ≤ the step above). The dashboard surfaces the error rather than rendering a broken chart. This catches runtime data anomalies even after the data has passed dbt tests.

#### Checkpoint D — `normaliseAttribution()` Auto-correction

Before rendering any attribution pie or donut chart, the agent calls:

```javascript
const normalised = Metrics.normaliseAttribution(channels);
// Input:  [{label:'Google', val:55.3}, {label:'Meta', val:44.9}]  → sum = 100.2
// Output: [{label:'Google', val:55.1}, {label:'Meta', val:44.9}]  → sum = 100.0
```

This is not just a test — it is a silent auto-correction that re-normalises shares to exactly 100% with 1 decimal place, compensating for any rounding that accumulated during intermediate calculations (`CLAUDE.md §4`).

---

### 9.4 Date Source Linkage (Single Source of Truth)

After the dynamic time filtering audit, the date configuration flows in one direction:

```
dbt_project/dbt_project.yml  (vars: window_start, window_end, time_spine_start, time_spine_end)
        │
        ├──▶  dbt SQL models (via var() references)
        │       metricflow_time_spine.sql, fct_marketing_daily.sql
        │
        └──▶  scripts/generate_golden_metrics.py (via _load_dbt_vars())
                │
                └──▶  dashboards/golden_metrics.json  (AI reads this)
                        └──▶  Dashboards render from _meta.window_start / _meta.window_end
```

**To change the analysis window for the entire system, edit `dbt_project.yml` once.**  
Run `dbt build` then `python scripts/generate_golden_metrics.py` — everything updates automatically.
