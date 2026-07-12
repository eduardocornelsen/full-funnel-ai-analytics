# Contributing

Thanks for your interest! This project aims to be the reference implementation
for **governed, drift-free, eval-measured AI analytics** on a small stack
(DuckDB + dbt + MCP). Contributions that strengthen that thesis are the most
valuable — see [`docs/STRATEGY.md`](docs/STRATEGY.md) for the roadmap.

## Dev setup (5 minutes, zero credentials)

```bash
git clone https://github.com/eduardocornelsen/full-funnel-ai-analytics
cd full-funnel-ai-analytics
pip install -e ".[dev]"
fullfunnel demo          # synthetic data → DuckDB → dbt → golden metrics → validation
```

`fullfunnel demo` must finish green before and after your change. No Kaggle
account, cloud warehouse, or API key is needed for the default path.

## Quality gates (all must pass — CI enforces them)

```bash
ruff check .                              # lint
python -m pytest tests/ -q               # unit + artifact tests
cd dbt_project && dbt test --target duckdb && cd ..
fullfunnel validate                       # metric drift + staleness gates
```

## The two rules that make this project what it is

1. **Never introduce a second definition of a metric.** Formulas live in
   `dbt_project/models/metrics/metrics.yml` and are consumed via the golden
   layer. If you must duplicate one temporarily, add a comment linking the
   canonical source, and expect review pushback.
2. **Never default a date to a literal.** Anchors and windows derive from the
   data or the wall clock (see the staleness postmortem in
   `dbt_project/models/marts/fct_marketing_daily.sql`). A hardcoded date
   default froze this pipeline for 93 days once. Once.

## Adding a time-series table?

Register it in the `tables` list in `scripts/daily_synthetic_append.py` —
a table missing from that registry silently freezes while the rest of the
dataset grows (that's the other half of the postmortem).

## Good first contributions

- Migrate one of the four legacy HTML dashboards to `dashboards/js/metrics.js`
- Add a unit test for `scripts/query_window.py` window parsing
- Make an SQRA benchmark case's expected value derive from the golden layer
  instead of a hardcoded number (they break as the dataset grows)
- Port a command from `agent_config/commands/` to a new AI client
- Replace a `except Exception: pass` in `scripts/load_supabase.py` with real
  error handling

## Pull requests

- Branch from `main`; keep PRs focused on one concern.
- Update `CHANGELOG.md` under **Unreleased**.
- If your change affects metric values, say so explicitly in the PR body and
  include the regenerated `golden_metrics.json` in the same PR — CI validates
  drift on every push.
