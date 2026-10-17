# Running the project on Snowflake

The same dbt project that runs on DuckDB builds on Snowflake: 25 models, 83 tests,
and a parity gate that compares the Snowflake marts with the committed golden
layer generated on DuckDB. This guide takes a fresh trial account to a green
`warehouse-deploy.yml` run.

**Status:** verified locally against [fakesnow](https://github.com/tekumara/fakesnow)
(a Snowflake emulator); the first run against a live account is pending. See
[What has been verified](#what-has-been-verified) for exactly what that covers.

## 1. Create a trial account (5 min)

1. Sign up at <https://signup.snowflake.com>. Pick **Standard** edition and
   any AWS region near you. The trial lasts 30 days with $400 of credits and
   needs no card.
2. In Snowsight, open the account menu (bottom left) → your account →
   **View account details**, and copy the **Account identifier**. It looks like
   `ORGNAME-ACCOUNTNAME` (if it shows a dot, `ORGNAME.ACCOUNTNAME`, use a
   hyphen instead). That is `SNOWFLAKE_ACCOUNT`.

## 2. Run the setup SQL (2 min)

Open **Projects → Worksheets**, paste [`scripts/snowflake_setup.sql`](../../scripts/snowflake_setup.sql),
replace `<CHOOSE_A_STRONG_PASSWORD>`, and **Run All** as `ACCOUNTADMIN`.
It creates:

| Object | What it is |
|---|---|
| `ANALYTICS_WH` | X-Small warehouse, `AUTO_SUSPEND = 60`, `AUTO_RESUME`, created suspended |
| `OLIST_ANALYTICS.RAW` | where `scripts/load_snowflake.py` lands the CSVs |
| `OLIST_ANALYTICS.ANALYTICS` | where dbt builds staging views and mart tables |
| `TRANSFORMER` | role with usage on the warehouse and full rights on both schemas |
| `CI_USER` | service user for GitHub Actions, default role `TRANSFORMER` |
| `ANALYTICS_WH_MONITOR` | resource monitor: suspends the warehouse past 5 credits a month |

The script is idempotent; running it twice changes nothing.

## 3. Add the GitHub secrets (2 min)

Repository → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Value |
|---|---|
| `SNOWFLAKE_ACCOUNT` | the account identifier, e.g. `ABCDEFG-XY12345` |
| `SNOWFLAKE_USER` | `CI_USER` |
| `SNOWFLAKE_PASSWORD` | the password from step 2 (or use key-pair, below) |
| `SNOWFLAKE_ROLE` | `TRANSFORMER` |
| `SNOWFLAKE_WAREHOUSE` | `ANALYTICS_WH` |
| `SNOWFLAKE_DATABASE` | `OLIST_ANALYTICS` |
| `SNOWFLAKE_SCHEMA` | `ANALYTICS` |

Raw tables go to schema `RAW` by default; set `SNOWFLAKE_RAW_SCHEMA` and
`RAW_SCHEMA` only if you want another name.

Until these exist, the Snowflake job in `warehouse-deploy.yml` **skips** with a
notice listing the missing names, instead of failing.

Then run it: **Actions → Warehouse Deploy → Run workflow → target `snowflake`**.

### Key-pair auth

Snowflake is phasing out password-only sign-in, service users included. If the
password is refused, switch `CI_USER` to a key pair:

```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out snowflake_key.p8 -nocrypt
openssl rsa -in snowflake_key.p8 -pubout -out snowflake_key.pub
```

```sql
-- paste the body of snowflake_key.pub, without the BEGIN/END lines
ALTER USER CI_USER SET TYPE = SERVICE RSA_PUBLIC_KEY = 'MIIBIjANBgkqh...';
ALTER USER CI_USER UNSET PASSWORD;
```

Store the whole content of `snowflake_key.p8` (with its BEGIN/END lines) in the
secret `SNOWFLAKE_PRIVATE_KEY` and delete `SNOWFLAKE_PASSWORD`. The workflow
writes the key to a temp file and points `SNOWFLAKE_PRIVATE_KEY_PATH` at it; the
loader, dbt profile and validator all read that variable. Never commit the key.

## 4. What the workflow does

```
daily_synthetic_append.py   same deterministic rows CI generates for DuckDB
load_snowflake.py           22 CSVs → RAW, each table replaced (rerun-safe)
dbt run / dbt test          --target snowflake: 25 models, 83 tests
validate_metrics.py         --target snowflake --completed-months-only
```

The last step is the parity gate: every completed calendar month in the
committed `dashboards/golden_metrics.json` (generated on DuckDB) must match what
the Snowflake marts produce. It is the same check CI runs on DuckDB, so a
mismatch means the engines disagree, not that the data moved.

## 5. Cost

An X-Small warehouse burns 1 credit per running hour, billed per second with a
60-second minimum each time it resumes. Standard edition costs about $2–3 per
credit depending on region.

| Item | Estimate |
|---|---|
| Load (~2.2M rows, mostly geolocation and attribution) | 1–3 min |
| `dbt run` + `dbt test` | 1–3 min |
| Parity queries | < 1 min |
| **One full deploy** | **~0.1 credit ≈ $0.20–0.30** |
| Storage (< 1 GB compressed) | cents per month |

A deploy on every push to `main` for a month stays well inside the trial
credits, and the resource monitor stops the warehouse at 5 credits.
`AUTO_SUSPEND = 60` keeps idle time near zero.

## 6. Running locally

```bash
pip install -e ".[snowflake]"
cp dbt_project/profiles.yml.example dbt_project/profiles.yml
export SNOWFLAKE_ACCOUNT=... SNOWFLAKE_USER=CI_USER SNOWFLAKE_PASSWORD=... \
       SNOWFLAKE_ROLE=TRANSFORMER SNOWFLAKE_WAREHOUSE=ANALYTICS_WH \
       SNOWFLAKE_DATABASE=OLIST_ANALYTICS SNOWFLAKE_SCHEMA=ANALYTICS

python scripts/daily_synthetic_append.py        # rewrites CSVs locally; don't commit them
python scripts/load_snowflake.py --dry-run      # lists the 22 tables, no connection
python scripts/load_snowflake.py
cd dbt_project && dbt build --target snowflake && cd ..
python scripts/validate_metrics.py --target snowflake --completed-months-only
git checkout data/                               # drop the regenerated CSVs
```

Without an account, `pytest tests/test_load_snowflake.py` runs the loader
against fakesnow.

## What has been verified

| Check | How | Result |
|---|---|---|
| Loader: connect, create schema, overwrite, row counts, loud failure | `tests/test_load_snowflake.py` on fakesnow | passes |
| `dbt build --target snowflake`, all 22 CSVs loaded | fakesnow server mode + dbt-snowflake | 108/108 (25 models, 83 tests) |
| Parity gate | `validate_metrics.py --target snowflake --completed-months-only` on fakesnow | 12/12 checks, 0 drift |
| Full artifact | `generate_golden_metrics.py` on fakesnow vs DuckDB, every numeric leaf | 2,810 leaves equal; only `_meta.dbt_target` differs |
| Live Snowflake account | — | **pending** |

fakesnow parses Snowflake SQL with sqlglot and executes it on DuckDB. It
verifies that the Snowflake branches of the models are valid Snowflake syntax as
sqlglot reads it, and that they produce the same numbers. It does not verify
Snowflake's own planner, type coercion edge cases, `write_pandas`'s PUT/COPY
staging path, grants, or authentication. The first live run is what closes those.

## Portability notes

Dialect differences are handled inside the models with `target.type`, so the
DuckDB SQL is unchanged:

| DuckDB | Snowflake |
|---|---|
| `range()` / `generate_series` date spine | `GENERATOR` + `ROW_NUMBER()` (macro `snowflake_day_spine`) |
| `DATEDIFF('day', a, b)` | `DATEDIFF(day, a, b)` |
| raw tables in schema `main` | raw tables in `RAW` (`sources.yml`) |

The loader writes unquoted upper-case identifiers, so dbt's lower-case unquoted
SQL resolves without quoting anything.
