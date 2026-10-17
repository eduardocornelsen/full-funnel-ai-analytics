# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/) · Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Fixed
- `warehouse-deploy.yml` was not valid YAML (an unquoted `: ` in a step name),
  so GitHub could never start it. It now skips a warehouse cleanly when its
  secrets are missing, honours the `target` input, regenerates the same
  synthetic appends CI uses before loading (otherwise every recent month
  drifts), and gates on `--completed-months-only` parity
- `validate_metrics.py --target snowflake` used `?` placeholders against the
  connector's default `pyformat` paramstyle; it now switches to `qmark`
- **Time-decay attribution is now normalised per order.** The raw weights
  `POWER(2, -days/7)` were summed without dividing by the order's total, so
  time-decay revenue came out at ~$24.7M against ~$18.2M of order revenue
  (+35%). Weights now sum to 1 within each order. The canonical linear model
  and `golden_metrics.json` are unaffected (they never used time-decay)
- New dbt test `assert_attribution_conserves_revenue`: every attribution model
  (first/last/linear/time-decay) must attribute total order revenue within
  0.01% (linear credits are stored rounded to 4 decimals, ~0.003% under)
- Docs no longer oversell the ML layer: the lead-scoring features are random,
  the logged AUC is ≈ 0.49, and the README now says it is a plumbing demo
- README accuracy: 3 workflows (not 4), 6 MCP servers (not 7), which warehouses
  are actually tested, Olist CSVs are committed, no Weather API, no
  `run_mlflow_server.sh`, and a "what's real vs synthetic" box up top
- `src/*.egg-info` is no longer tracked

### Added
- **Snowflake path.** `scripts/load_snowflake.py` (env-only credentials,
  password or key pair, `--dry-run`, every table replaced so reruns are safe,
  row counts, stops naming the table that failed), `scripts/snowflake_setup.sql`
  (X-Small warehouse with 60 s auto-suspend, database, `RAW`/`ANALYTICS`
  schemas, `TRANSFORMER` role, CI user, 5-credit resource monitor) and
  `docs/guides/snowflake.md`. Models branch on `target.type` for the date spine
  (`GENERATOR`), `DATEDIFF(day, …)` and the raw schema; DuckDB SQL unchanged.
  Verified on fakesnow: loader tests, `dbt build --target snowflake` 108/108,
  parity 0 drift. **Live Snowflake run pending.**
- Committed-artifact spot check: `validate_metrics.py --completed-months-only`
  validates the checked-in `golden_metrics.json` against the warehouse using
  completed calendar months (anchor-independent), wired into PR CI before the
  regeneration step — catches metric-logic PRs that forget to regenerate the
  artifact, and any break in generation determinism
- **Regenerate-don't-commit data model**: the committed CSVs are a frozen
  Olist-anchored baseline; daily appends are regenerated deterministically
  (seeded per calendar date) on every machine and never committed. The
  scheduled refresh commits only `golden_metrics.json`; the separate daily
  append workflow was removed. numpy is pinned and `tests/test_determinism.py`
  gates generator reproducibility in CI
- `fullfunnel` CLI (`pip install -e .`): `init`, `demo` (zero-credential path),
  `append`, `refresh`, `validate`, `bench`
- `pyproject.toml` packaging with extras: `[bigquery]`, `[snowflake]`,
  `[postgres]`, `[ml]`, `[app]`, `[olist]`, `[dev]`
- Staleness gate in `validate_metrics.py`: golden anchor vs raw-data frontier
  (hard fail >1 day), plus wall-clock check (warn by default,
  `--strict-freshness` to fail — used by the scheduled refresh)
- Synthetic feed catch-up mode: `daily_synthetic_append.py` now targets
  **today (UTC)** by default, backfilling every table from its own last date —
  missed scheduled runs self-heal, same-day re-runs are no-ops
- Daily append now covers all 7 time-series tables (was 3 of 13): marketing
  attribution, HubSpot deals/contacts, Salesforce opportunities included
- `docs/STRATEGY.md` (platform roadmap) and `docs/INTERVIEW_STORIES.md`
- `CONTRIBUTING.md`, issue/PR templates, ruff lint gate in CI
- Workflow concurrency groups so data-writing jobs can't race

### Fixed
- **Golden layer silently stale for 93 days**: `fct_marketing_daily` was capped
  by a literal-date var fallback and the scheduled refresh passed no `--vars`;
  the mart now derives bounds from source data and cannot freeze
- `.mcp.json` hardcoded the author's machine paths in all server entries —
  now repo-relative (works for any clone)
- Lead-scoring API multiplied model output by hardcoded channel factors
  (`prob *= 1.2`) — removed; the API returns the model's honest probability
  and declares `model_features_used`
- Meta "platform" ROAS was derived from the $100 AOV assumption it supposedly
  validates — now computed from `purchase_value / spend`
- Partial anchor months labeled "(month to date)" instead of "(full month)"
- README/docs corrected: server count, data size, nonexistent files/dirs
  (`warehouse_configs/`, `.opencode/opencode.json`), phantom API endpoint

### Removed
- `mcp_servers/weather_server.py` (unrelated demo)

### Known issues
- SQRA benchmark cases with hardcoded all-time expected values drift as the
  dataset grows daily; expected values must derive from the golden layer
  (planned for SQRA v2 — see `docs/STRATEGY.md` Phase 3)
