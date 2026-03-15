{% macro time_decay_credit(touchpoint_date, order_date, half_life_days=7) %}
    POWER(2.0, -1.0 * 
        {% if target.type == 'bigquery' %}
            DATE_DIFF(CAST({{ order_date }} AS DATE), CAST({{ touchpoint_date }} AS DATE), DAY)
        {% elif target.type == 'postgres' %}
            EXTRACT(DAY FROM (CAST({{ order_date }} AS DATE) - CAST({{ touchpoint_date }} AS DATE)))
        {% else %}
            DATEDIFF('day', CAST({{ touchpoint_date }} AS DATE), CAST({{ order_date }} AS DATE))
        {% endif %}
        / {{ half_life_days }}.0
    )
{% endmacro %}
