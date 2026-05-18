-- CRM pipeline fact table — one row per deal / opportunity.
--
-- Previously this model was a pre-aggregated channel summary (one row per channel)
-- with columns: attribution_channel, total_touches, total_leads, total_opportunities,
-- closed_won, total_conversions. That structure was completely mismatched with the
-- 'pipeline' semantic model in sem_marketing.yml, which declared:
--   - primary entity: deal_id
--   - agg_time_dimension: close_date
--   - measures: pipeline_value (sum of amount), deal_count (count_distinct deal_id)
--
-- Fix: rewrite as a deal-level UNION of HubSpot deals and Salesforce opportunities.
-- This matches the semantic model's expected schema exactly, enabling MetricFlow to:
--   - filter pipeline by close_date range
--   - group pipeline_value by stage, source, or lead_source
--   - count deals with count_distinct on deal_id
--
-- Source models (both are staging views):
--   stg_hubspot_deals          → deals with deal_id, stage, amount, close_date, lead_source
--   stg_salesforce_opportunities → same columns (opportunity_id aliased to deal_id)

WITH hubspot AS (
    -- HubSpot deals: one row per deal.
    -- All column names are already normalised in the staging model.
    SELECT
        deal_id,                        -- primary key; MetricFlow entity key for deal_count
        deal_stage    AS stage,         -- funnel stage: prospecting → closed_won / closed_lost
        'hubspot'     AS source,        -- CRM system that owns this record
        lead_source,                    -- marketing channel that generated the lead (categorical dim)
        amount,                         -- deal value in USD; MetricFlow sums this as pipeline_value
        close_date                      -- agg_time_dimension for the 'pipeline' semantic model
    FROM {{ ref('stg_hubspot_deals') }}
),

salesforce AS (
    -- Salesforce opportunities: one row per opportunity.
    -- opportunity_id is aliased to deal_id to unify key names across the UNION.
    SELECT
        opportunity_id AS deal_id,      -- opportunity_id aliased to match HubSpot's deal_id column name
        stage,                          -- Salesforce stage: Prospecting → Closed Won / Closed Lost
        'salesforce'   AS source,       -- CRM system that owns this record
        lead_source,                    -- marketing channel that sourced the opportunity
        amount,                         -- opportunity value in USD
        close_date                      -- agg_time_dimension; same semantics as HubSpot close_date
    FROM {{ ref('stg_salesforce_opportunities') }}
)

-- Combine both CRM systems into a single unified deal-level fact table.
-- UNION ALL (not UNION) preserves all rows including potential duplicates;
-- deal_ids are system-scoped so HubSpot and Salesforce IDs never collide.
SELECT * FROM hubspot
UNION ALL
SELECT * FROM salesforce
