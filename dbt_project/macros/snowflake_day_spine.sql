{#
  One row per calendar day, from start_date to end_date inclusive, on Snowflake.

  DuckDB builds the spine with range()/generate_series(), which Snowflake does
  not have. GENERATOR needs a constant row count, so we generate a fixed
  20,000 days (about 54 years) and cut at the end date. ROW_NUMBER() over
  SEQ4() instead of SEQ4() alone, because SEQ4() may leave gaps.

  end_date = none keeps the project rule from metricflow_time_spine.sql: the
  spine runs to one year past the build date, never to a literal date.
#}
{% macro snowflake_day_spine(start_date, end_date=none) %}
SELECT date_day
FROM (
    SELECT DATEADD(day, ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1, '{{ start_date }}'::DATE) AS date_day
    FROM TABLE(GENERATOR(ROWCOUNT => 20000))
)
WHERE date_day <= {% if end_date %}'{{ end_date }}'::DATE{% else %}DATEADD(year, 1, CURRENT_DATE()){% endif %}
{% endmacro %}
