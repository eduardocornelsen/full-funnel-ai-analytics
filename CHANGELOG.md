# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/) · Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added
- **SQRA v2 — honest, self-updating benchmark + model-in-the-loop agent
  comparison**: cases are anchor-relative (date tokens resolved from golden
  `_meta`) with expected values resolved from the golden artifact — every
  surface is now a cross-implementation check that survives the daily-growing
  dataset. The golden surface validates the artifact against an independent
  recomputation (was: compared to itself). Adversarial detection is on merit
  (flawed queries must actually diverge from canonical values) instead of by
  label. New agent benchmark (`--agents`): three architectures — golden-tools
  / raw-sql / semantic-layer — answer the same NL questions, scored for
  numeric fidelity + tokens/question (needs ANTHROPIC_API_KEY; harness
  unit-tested with a scripted fake client). SQRA gate (`--min-score 95`)
  added to PR CI and the daily refresh; weekly `agent-benchmark.yml` runs the
  model-in-the-loop comparison when the API-key secret is configured
- **Connector protocol + real GA4 connector** (`src/fullfunnel/connectors/`):
  a small `Connector` ABC (extract(start, end) → staging-schema DataFrame,
  schema declared in code — CLAUDE.md §7 field mappings now live as code, not
  prose) with a registry; three CSV mock reference implementations; and the
  first REAL platform connector against the GA4 Data API v1 (free tier),
  with the API→staging mapping as a pure unit-tested function. New CLI:
  `fullfunnel ingest --connector ga4 --last-days 90 [--dry-run]` merges the
  extracted window into the staging CSV (with backup) — "swap in your real
  data" is now a seam, not an aspiration. `pip install -e ".[ga4]"`
- **dbt hardening**: `packages.yml` with dbt_utils (git-pinned — package hub
  blocked in some network policies); model contract ENFORCED on
  `fct_marketing_daily` (the golden-feeding mart) with full column typing;
  grain tests (`unique_combination_of_columns`) on `fct_channel_performance`
  and `fct_marketing_attribution`; dbt-native source freshness on all 7
  time-series sources (warn 2d / error 4d) run in CI and the daily refresh;
  `exposures.yml` declaring the golden artifact, analytics MCP server,
  Streamlit app, and HTML dashboards in the lineage graph. 91 dbt tests
  (was 82)
- **Governed AI analyst chat** (Streamlit): rebuilt on the governed analytics
  tools — the model can no longer run raw SQL from the chat. Full conversation
  history (previously only the last message was sent), runtime-rendered system
  prompt from golden `_meta` (the old prompt hardcoded a date range that had
  been stale for months), and a "How was this computed" expander showing each
  tool call's provenance envelope (value, formula, scope, window, verification)
- **First-boot warehouse bootstrap** (`streamlit_app/lib/bootstrap.py`):
  Streamlit Cloud deploys now work — if the (never-committed) DuckDB file or
  golden artifact is missing, the app builds them once at startup from the
  committed baseline + deterministic appends. Verified: a from-nothing
  bootstrap reproduces the committed golden artifact identically (ex-`_meta`)
- **Governed analytics MCP server** (`mcp_servers/analytics_server.py`,
  renamed from mock_analytics_server): metric-first tools — `list_metrics`,
  `get_metric`, `explain_metric`, `get_funnel` (server-side funnel-ordering
  validation, CRM lifetime counts excluded by contract), `compare_windows`
  (flags month-to-date comparability) — every numeric response carries a
  governance envelope {value, formula, scope_label, window, source,
  semantic_layer_crosscheck}. Formulas read live from metrics.yml, never
  duplicated. Guardrails as tool contract, not prompt. 8 contract tests
- **Semantic layer is now load-bearing** (schema v2.3): CI and the scheduled
  refresh run `mf validate-configs`; `generate_golden_metrics.py` cross-checks
  its governed metrics against `mf query` and fails on divergence, recording
  the result in `_meta.semantic_layer_crosscheck`. New `attribution_touchpoints`
  semantic model. Python metric formulas collapsed into `src/fullfunnel/metrics.py`

### Fixed
- `scripts/load_supabase.py` swallowed every load error (`except: pass` ×3,
  print-and-continue ×1) — partial warehouse loads now fail loudly with the
  failing table and batch offset
- Streamlit app crashed at startup with current marts: a module-level query
  selected columns from a `fct_pipeline` shape that no longer exists
  (`total_conversions`, `total_touches`, …). Rebuilt as a deal-grain rollup;
  the full app now executes cleanly (verified via `streamlit.testing.AppTest`,
  9 tabs, zero exceptions)
- **Semantic layer YAML had never run and was silently wrong** — first
  MetricFlow execution caught: `payment_type` dimension mapped to a renamed
  column; `blended_roas` defined on `fct_orders` revenue (NULL for all recent
  windows, different scope than the golden layer); `session_conversion_rate`
  defined orders-based (returned 0) instead of the canonical GA4 ratio. All
  redefined to match CLAUDE.md §1 and verified equal to the golden layer to 4
  decimal places

### Known issues
- (resolved) ~~SQRA cases with hardcoded expected values drifting as the
  dataset grows~~ — fixed by SQRA v2's golden-derived expectations

## [0.10.0] - 2026-07-12

### Added
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

## [0.9.x and earlier]

Pre-changelog history: initial platform build (dbt project, MCP servers,
dashboards, ML scoring, multi-warehouse deploys) — see git log and GitHub
releases v0.9.0 / v0.9.1.
