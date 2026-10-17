-- One-time Snowflake setup for the full-funnel-ai-analytics dbt project.
--
-- Run once as ACCOUNTADMIN (Snowsight → Projects → Worksheets → paste → Run All).
-- Safe to re-run: every statement is IF NOT EXISTS / idempotent.
--
-- What it creates:
--   ANALYTICS_WH       X-SMALL warehouse that suspends after 60 s idle, so a CI
--                      run costs seconds of compute, not an hour
--   OLIST_ANALYTICS    database with schemas RAW (CSV loads) and ANALYTICS (dbt)
--   TRANSFORMER        role that owns both schemas and uses the warehouse
--   CI_USER            service user for GitHub Actions, granted TRANSFORMER
--
-- Before running: replace <CHOOSE_A_STRONG_PASSWORD>. Never commit the real value;
-- it goes only into the GitHub secret SNOWFLAKE_PASSWORD (or use key-pair auth).

USE ROLE ACCOUNTADMIN;

CREATE WAREHOUSE IF NOT EXISTS ANALYTICS_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'full-funnel-ai-analytics: dbt + loader + CI';

CREATE DATABASE IF NOT EXISTS OLIST_ANALYTICS;
CREATE SCHEMA IF NOT EXISTS OLIST_ANALYTICS.RAW;
CREATE SCHEMA IF NOT EXISTS OLIST_ANALYTICS.ANALYTICS;

CREATE ROLE IF NOT EXISTS TRANSFORMER;
GRANT ROLE TRANSFORMER TO ROLE SYSADMIN;

GRANT USAGE, OPERATE ON WAREHOUSE ANALYTICS_WH TO ROLE TRANSFORMER;
GRANT USAGE ON DATABASE OLIST_ANALYTICS TO ROLE TRANSFORMER;
-- The loader runs CREATE SCHEMA IF NOT EXISTS, and dbt may create custom schemas.
GRANT CREATE SCHEMA ON DATABASE OLIST_ANALYTICS TO ROLE TRANSFORMER;
GRANT ALL PRIVILEGES ON SCHEMA OLIST_ANALYTICS.RAW TO ROLE TRANSFORMER;
GRANT ALL PRIVILEGES ON SCHEMA OLIST_ANALYTICS.ANALYTICS TO ROLE TRANSFORMER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA OLIST_ANALYTICS.RAW TO ROLE TRANSFORMER;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA OLIST_ANALYTICS.RAW TO ROLE TRANSFORMER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA OLIST_ANALYTICS.ANALYTICS TO ROLE TRANSFORMER;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN SCHEMA OLIST_ANALYTICS.ANALYTICS TO ROLE TRANSFORMER;
GRANT ALL PRIVILEGES ON FUTURE VIEWS IN SCHEMA OLIST_ANALYTICS.ANALYTICS TO ROLE TRANSFORMER;

-- LEGACY_SERVICE: a non-human user that may still sign in with a password, so it
-- is not caught by the MFA requirement for people. Snowflake is phasing out
-- password-only sign-in for these users as well; the key-pair block below is the
-- durable option (docs/guides/snowflake.md → "Key-pair auth").
CREATE USER IF NOT EXISTS CI_USER
    TYPE = LEGACY_SERVICE
    PASSWORD = '<CHOOSE_A_STRONG_PASSWORD>'
    DEFAULT_ROLE = TRANSFORMER
    DEFAULT_WAREHOUSE = ANALYTICS_WH
    DEFAULT_NAMESPACE = OLIST_ANALYTICS.ANALYTICS
    MUST_CHANGE_PASSWORD = FALSE
    COMMENT = 'GitHub Actions: warehouse-deploy.yml';
GRANT ROLE TRANSFORMER TO USER CI_USER;

-- Key-pair auth (recommended): paste the public key generated with openssl, then
-- drop the password. The private key goes into the GitHub secret SNOWFLAKE_PRIVATE_KEY.
-- ALTER USER CI_USER SET TYPE = SERVICE RSA_PUBLIC_KEY = '<MIIBIjANBgkqh...>';
-- ALTER USER CI_USER UNSET PASSWORD;

-- Optional guard rail for a trial: stop the warehouse if monthly use passes 5 credits.
CREATE RESOURCE MONITOR IF NOT EXISTS ANALYTICS_WH_MONITOR
    WITH CREDIT_QUOTA = 5
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS ON 80 PERCENT DO NOTIFY
             ON 100 PERCENT DO SUSPEND;
ALTER WAREHOUSE ANALYTICS_WH SET RESOURCE_MONITOR = ANALYTICS_WH_MONITOR;

-- Check: should list ANALYTICS_WH as X-Small, suspended, auto_suspend 60.
SHOW WAREHOUSES LIKE 'ANALYTICS_WH';
