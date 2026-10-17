-- Every attribution model redistributes an order's revenue across its channels;
-- none may create or lose revenue. Returns a row (fails) for any model whose
-- attributed total differs from total order revenue by more than 0.01%.
--
-- The tolerance is relative, not a cent: the source stores linear_credit rounded
-- to 4 decimals (1/3 -> 0.3333), so linear under-attributes by ~0.003% of revenue.
-- An unnormalised time-decay model misses by tens of percent and still fails.

WITH orders AS (
    SELECT SUM(order_revenue) AS order_revenue
    FROM (
        SELECT DISTINCT order_id, order_revenue
        FROM {{ ref('stg_marketing_attribution') }}
    ) AS o
),

attributed AS (
    SELECT
        SUM(first_touch_revenue) AS first_touch,
        SUM(last_touch_revenue)  AS last_touch,
        SUM(linear_revenue)      AS linear,
        SUM(time_decay_revenue)  AS time_decay
    FROM {{ ref('fct_marketing_attribution') }}
),

compared AS (
    SELECT 'first_touch' AS model, attributed.first_touch AS attributed_revenue, orders.order_revenue FROM attributed, orders
    UNION ALL
    SELECT 'last_touch',  attributed.last_touch,  orders.order_revenue FROM attributed, orders
    UNION ALL
    SELECT 'linear',      attributed.linear,      orders.order_revenue FROM attributed, orders
    UNION ALL
    SELECT 'time_decay',  attributed.time_decay,  orders.order_revenue FROM attributed, orders
)

SELECT *
FROM compared
WHERE ABS(attributed_revenue - order_revenue) > 0.0001 * order_revenue
