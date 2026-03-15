WITH ads AS (
    SELECT 
        date,
        SUM(CASE WHEN platform = 'google_ads' THEN spend ELSE 0 END) AS google_spend,
        SUM(CASE WHEN platform = 'meta_ads' THEN spend ELSE 0 END) AS meta_spend,
        SUM(spend) AS total_ad_spend,
        SUM(conversions) AS ad_conversions
    FROM {{ ref('int_campaign_unified') }}
    GROUP BY 1
),
sessions AS (
    SELECT 
        date,
        SUM(sessions) AS total_sessions
    FROM {{ ref('stg_ga4_sessions') }}
    GROUP BY 1
)
SELECT
    d.date,
    COALESCE(a.google_spend, 0) AS total_google_spend,
    COALESCE(a.meta_spend, 0) AS total_meta_spend,
    COALESCE(a.total_ad_spend, 0) AS total_spend,
    COALESCE(a.ad_conversions, 0) AS total_conversions,
    COALESCE(s.total_sessions, 0) AS ga4_total_sessions,
    COALESCE(a.total_ad_spend / NULLIF(a.ad_conversions, 0), 0) AS blended_cac,
    COALESCE(a.total_ad_spend / NULLIF(s.total_sessions, 0), 0) AS cost_per_session
FROM (SELECT DISTINCT date FROM {{ ref('int_campaign_unified') }}) d
LEFT JOIN ads a ON d.date = a.date
LEFT JOIN sessions s ON d.date = s.date
