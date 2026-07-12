# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/) · Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added
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
- **Semantic layer YAML had never run and was silently wrong** — first
  MetricFlow execution caught: `payment_type` dimension mapped to a renamed
  column; `blended_roas` defined on `fct_orders` revenue (NULL for all recent
  windows, different scope than the golden layer); `session_conversion_rate`
  defined orders-based (returned 0) instead of the canonical GA4 ratio. All
  redefined to match CLAUDE.md §1 and verified equal to the golden layer to 4
  decimal places
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
