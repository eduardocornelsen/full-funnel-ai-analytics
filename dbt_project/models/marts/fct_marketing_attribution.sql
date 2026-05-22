-- Marketing attribution fact table — daily × channel grain.
--
-- Previously this model GROUP BY channel only, producing all-time totals with no
-- date column. That made it impossible for MetricFlow to filter attribution metrics
-- by time window (e.g., "channel revenue for last 90 days" returned all-time revenue).
--
-- Fix: add order_date to the SELECT and GROUP BY so the model is now at
-- the order_date × channel grain. fct_channel_performance.sql joins on both
-- date AND channel to preserve this grain through to the semantic layer.
--
-- Attribution model reference (see macros/attribution_models.sql):
--   first_touch  — 100% credit to the channel of the first touchpoint
--   last_touch   — 100% credit to the channel of the last touchpoint
--   linear       — equal credit split across all touchpoints (CANONICAL)
--   time_decay   — exponential decay by recency; half-life = 7 days (macro default)

WITH stg AS (
    -- Pull every attribution touchpoint row from the staging model.
    -- One row per (order_id × touchpoint_position); contains credit weights
    -- (first_touch_credit, last_touch_credit, linear_credit) pre-computed upstream.
    SELECT * FROM {{ ref('stg_marketing_attribution') }}
)

SELECT
    -- Date dimension: order_date is the event date that aligns with GA4 conversion events.
    -- Using order_date (not touchpoint_date) so that revenue is booked on the date of purchase,
    -- consistent with how fct_orders.sql and fct_marketing_daily.sql record conversions.
    order_date,

    -- Channel dimension: granular attribution channel (e.g. 'google_ads_search', 'meta_prospecting').
    -- fct_channel_performance.sql maps these to platform-level names ('google_ads', 'meta_ads').
    channel,

    -- First-touch revenue: multiply each touchpoint's first_touch_credit (0 or 1) by order_revenue.
    -- Only the first touchpoint in the path receives credit; all others get 0.
    -- COALESCE handles edge cases where all rows in a group have NULL revenue (returns 0 instead of NULL).
    COALESCE(SUM(first_touch_credit * order_revenue), 0)                              AS first_touch_revenue,

    -- Last-touch revenue: same logic but credit goes to the final touchpoint in the path.
    COALESCE(SUM(last_touch_credit * order_revenue), 0)                               AS last_touch_revenue,

    -- Linear revenue: every touchpoint in the path receives 1/N of the order revenue,
    -- where N = total_touchpoints. This is the CANONICAL attribution model for this project.
    COALESCE(SUM(linear_credit * order_revenue), 0)                                   AS linear_revenue,

    -- Time-decay revenue: touchpoints closer to conversion receive exponentially more credit.
    -- The macro time_decay_credit() computes POWER(2, -days_to_conversion / half_life_days).
    -- half_life_days defaults to 7 (one week) — touchpoint 7 days before conversion gets 50% weight.
    COALESCE(SUM({{ time_decay_credit('touchpoint_date', 'order_date') }} * order_revenue), 0) AS time_decay_revenue,

    -- Distinct order count for this date × channel combination.
    -- Used as the denominator for channel-level CVR and CAC calculations.
    COUNT(DISTINCT order_id)                                                          AS total_orders

FROM stg

-- Group by order_date AND channel (previously channel only).
-- This is the critical change: adding order_date enables MetricFlow time filtering.
GROUP BY 1, 2   -- 1 = order_date, 2 = channel
