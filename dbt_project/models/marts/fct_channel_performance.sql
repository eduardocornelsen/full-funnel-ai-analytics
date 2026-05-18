-- Channel performance fact table — daily × channel grain.
--
-- Previously this model produced one row per channel (all-time totals) with no date
-- column, making it impossible for MetricFlow to apply any time-window filter on
-- channel_roas, channel_spend, or customer_acquisition_cost metrics.
--
-- Fix: both the spend CTE (from int_campaign_unified) and the revenue CTE (from
-- fct_marketing_attribution, which now outputs order_date) include a date column.
-- The FULL OUTER JOIN is now on (date, channel), yielding a daily × channel fact table
-- that MetricFlow can aggregate over any time grain.

WITH spend AS (
    -- Daily spend aggregated to platform level (google_ads / meta_ads).
    -- int_campaign_unified already has a date column (day × campaign grain);
    -- we GROUP BY date and platform to collapse campaigns within a platform per day.
    SELECT
        date,                                 -- calendar date of the campaign activity
        platform AS channel,                  -- platform identifier: 'google_ads' or 'meta_ads'
        SUM(spend) AS total_spend             -- total paid-media spend for this date × platform
    FROM {{ ref('int_campaign_unified') }}
    GROUP BY 1, 2                             -- 1 = date, 2 = platform
),

revenue AS (
    -- Daily attributed revenue at granular channel level.
    -- fct_marketing_attribution now outputs order_date after Issue 3 fix;
    -- we alias it to 'date' for clarity in the subsequent JOIN.
    SELECT
        order_date AS date,                   -- order_date = event date (matches spend.date)
        channel,                              -- granular channel (e.g. 'google_ads_search')
        linear_revenue,                       -- canonical linear-attributed revenue
        total_orders                          -- attributed order count for this date × channel
    FROM {{ ref('fct_marketing_attribution') }}
),

-- Normalise granular attribution channel names to platform-level names so they
-- match the 'channel' values produced by the spend CTE.
-- e.g. 'google_ads_search' → 'google_ads', 'meta_prospecting' → 'meta_ads'
revenue_mapped AS (
    SELECT
        date,                                                           -- preserve date through the mapping step
        CASE
            WHEN channel LIKE 'google_ads%' THEN 'google_ads'          -- all Google sub-channels → 'google_ads'
            WHEN channel LIKE 'meta_%'      THEN 'meta_ads'            -- all Meta sub-channels → 'meta_ads'
            ELSE channel                                                -- pass-through for any other channel
        END                              AS channel,
        SUM(linear_revenue)              AS linear_revenue,            -- re-aggregate after collapsing sub-channels
        SUM(total_orders)                AS total_orders               -- re-aggregate order count after collapsing
    FROM revenue
    GROUP BY 1, 2                                                       -- 1 = date, 2 = mapped channel
)

SELECT
    -- Coalesce date from both sides of the FULL OUTER JOIN.
    -- A spend-only day (no revenue) keeps the spend date; a revenue-only day keeps the order date.
    COALESCE(s.date, r.date)                                           AS date,

    -- Coalesce channel from both sides.
    COALESCE(s.channel, r.channel)                                     AS channel,

    -- Zero-fill spend when revenue exists but no campaign ran that day on this platform.
    COALESCE(s.total_spend, 0)                                         AS total_spend,

    -- Zero-fill revenue when spend exists but no attributed orders were recorded.
    COALESCE(r.linear_revenue, 0)                                      AS attributed_revenue,

    -- Zero-fill order count for the same reason as attributed_revenue.
    COALESCE(r.total_orders, 0)                                        AS total_orders,

    -- CAC = spend / orders. NULLIF guards against divide-by-zero on zero-order days.
    -- Result is zero (not NULL) via outer COALESCE so MetricFlow sums cleanly.
    COALESCE(s.total_spend / NULLIF(r.total_orders, 0), 0)             AS cac,

    -- ROAS = revenue / spend. NULLIF guards against divide-by-zero on zero-spend days.
    COALESCE(r.linear_revenue / NULLIF(s.total_spend, 0), 0)           AS roas

FROM spend s
FULL OUTER JOIN revenue_mapped r
    ON  s.date    = r.date      -- join on date to maintain the daily grain
    AND s.channel = r.channel   -- join on channel to maintain the channel grain

-- Exclude phantom rows where both sides of the join have no channel value
-- (can happen if NULL channels exist in upstream staging models).
WHERE COALESCE(s.channel, r.channel) IS NOT NULL
