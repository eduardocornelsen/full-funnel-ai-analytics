-- Daily marketing performance fact table — one row per calendar day.
--
-- Previously the date spine was derived from campaign activity:
--   FROM (SELECT DISTINCT date FROM int_campaign_unified) d
-- This caused silent gaps on days when all campaigns were paused (weekends, budget pauses).
-- MetricFlow weekly and monthly roll-ups silently excluded those days, making spend
-- and session metrics appear higher than actual.
--
-- Fix: drive the date spine from metricflow_time_spine so every calendar day within
-- the configured window appears — even days with zero spend and zero sessions.
-- Campaign and session data LEFT JOIN onto the spine; COALESCE fills missing days with 0.
--
-- The window is controlled by dbt vars (window_start / window_end) defined in
-- dbt_project.yml. Override at runtime with:
--   dbt build --vars '{"window_start":"2025-06-01","window_end":"2025-09-01"}'

WITH ads AS (
    -- Aggregate paid-media metrics to day-level by platform.
    -- int_campaign_unified is a UNION ALL of stg_google_ads_performance and
    -- stg_meta_ads_performance, giving one row per (date × platform × campaign).
    -- Here we collapse campaigns within each platform per day.
    SELECT
        date,                                                                    -- campaign activity date

        -- Split spend by platform for downstream platform-level reporting.
        SUM(CASE WHEN platform = 'google_ads' THEN spend ELSE 0 END)  AS google_spend,  -- Google-only spend
        SUM(CASE WHEN platform = 'meta_ads'   THEN spend ELSE 0 END)  AS meta_spend,    -- Meta-only spend
        SUM(spend)                                                      AS total_ad_spend, -- combined paid spend

        -- Ad-platform conversions: click → purchase as recorded by Google Ads and Meta Ads.
        -- This is the denominator for Click CVR (not cross-channel; use ga4_conversions for Session CVR).
        SUM(conversions)                                               AS ad_conversions
    FROM {{ ref('int_campaign_unified') }}
    GROUP BY 1  -- collapse to day grain
),

sessions AS (
    -- Aggregate GA4 session metrics to day-level (all channels combined).
    -- stg_ga4_sessions is at the date × channel_group grain; SUM collapses channels.
    SELECT
        date,                                                                    -- GA4 session date
        SUM(sessions)          AS total_sessions,          -- all web sessions (Session CVR denominator)
        SUM(engaged_sessions)  AS total_engaged_sessions,  -- sessions lasting >10s or converting
        SUM(conversions)       AS ga4_conversions          -- GA4 conversion events (Session CVR numerator)
    FROM {{ ref('stg_ga4_sessions') }}
    GROUP BY 1  -- collapse to day grain
)

SELECT
    -- ── Date spine ─────────────────────────────────────────────────────────────
    -- Drive from metricflow_time_spine so zero-activity days (paused campaigns,
    -- weekends) still appear as rows. Without this, MetricFlow weekly roll-ups
    -- silently skip those days and inflate per-day averages.
    d.date_day                                                          AS date,

    -- ── Spend columns ──────────────────────────────────────────────────────────
    COALESCE(a.google_spend, 0)                                         AS total_google_spend,  -- zero when Google paused
    COALESCE(a.meta_spend, 0)                                           AS total_meta_spend,    -- zero when Meta paused
    COALESCE(a.total_ad_spend, 0)                                       AS total_spend,         -- combined paid spend

    -- ── Conversion columns ─────────────────────────────────────────────────────
    -- Ad-platform (click-based) conversions: used only for Click CVR per campaign.
    -- Do NOT compare to ga4_total_sessions; use for platform-side reporting only.
    COALESCE(a.ad_conversions, 0)                                       AS total_ad_conversions,

    -- GA4 session-level conversions: numerator for Session CVR (canonical cross-channel metric).
    COALESCE(s.ga4_conversions, 0)                                      AS total_conversions,

    -- ── Session columns ────────────────────────────────────────────────────────
    COALESCE(s.total_sessions, 0)                                       AS ga4_total_sessions,  -- Session CVR denominator
    COALESCE(s.total_engaged_sessions, 0)                               AS ga4_engaged_sessions, -- engagement metric

    -- ── Pre-computed convenience metrics ───────────────────────────────────────
    -- These are included for SQL convenience; MetricFlow should derive its own
    -- aggregations from the raw measures above rather than summing these columns.
    -- NULLIF guards against divide-by-zero on zero-activity days.
    COALESCE(a.total_ad_spend / NULLIF(a.ad_conversions, 0), 0)        AS blended_cac,          -- cost per ad conversion
    COALESCE(a.total_ad_spend / NULLIF(s.total_sessions, 0), 0)        AS cost_per_session       -- cost per web session

FROM {{ ref('metricflow_time_spine') }} d  -- spine drives the date; ensures continuous daily coverage

-- Filter to the canonical 90-day analysis window.
-- Use dbt vars so the window can be changed without editing SQL.
-- Synthetic dataset window: 2025-12-16 → 2026-03-15 (fixed anchor; see CLAUDE.md §9).
WHERE d.date_day BETWEEN '{{ var("window_start", "2025-12-16") }}'
                     AND '{{ var("window_end",   "2026-03-15") }}'

-- LEFT JOIN preserves all spine dates even when campaigns were paused or GA4 had no sessions.
LEFT JOIN ads      a ON d.date_day = a.date   -- join paid-media metrics; NULL → COALESCE to 0
LEFT JOIN sessions s ON d.date_day = s.date   -- join GA4 session metrics; NULL → COALESCE to 0
