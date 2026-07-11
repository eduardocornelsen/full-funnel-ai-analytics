# Platform Strategy & Roadmap

> Synthesized from a four-track review (data platform architecture, agentic BI layer,
> open-source product readiness, competitive landscape) conducted 2026-07-11.
> This document is the working plan for evolving this repo from an impressive
> portfolio into a real open-source platform at the edge of the modern data
> stack and Agentic BI.

---

## 1. Verdict

**The thesis is right, and the market has proven it.** In 2025–26 the industry
converged on exactly this project's claim — *AI agents need governed semantic
context, not raw text-to-SQL*: dbt/Fivetran merged and launched Agents Schema,
Cube shipped D3, Snowflake ships Cortex Analyst, Wren AI reached ~16k GitHub
stars on this pitch. **Being right is no longer differentiating. Being useful
about it is.**

What remains unowned in the market — and what this repo is uniquely positioned
to own — is **proof**: nobody neutral measures whether AI analytics actually
gets the numbers right. Every published accuracy number (AtScale's 16%→100%,
Cube's "3× accuracy", nao's agent rankings) comes from a vendor selling the
winning architecture.

**Two crown jewels**, independently identified by every review track:

1. **The golden-layer pattern** — pre-computed, drift-validated metrics as the
   agent's only data source (`dashboards/golden_metrics.json` + the
   generate/validate loop). A genuinely novel, articulate answer to LLM
   arithmetic non-determinism.
2. **The SQRA eval harness** (`tests/benchmark/`, `scripts/run_sqra.py`) — the
   seed of "evals for agentic BI," which almost nobody in open source has
   shipped.

Both were buried under portfolio packaging. The strategy below surfaces them.

---

## 2. The critical findings (and their status)

### 2.1 The silent-staleness bug — FIXED (Phase 0)

The project's zero-drift guarantee was broken for ~3 months without any gate
noticing:

- Raw CSVs grew daily (through 2026-06-15) but `golden_metrics.json` was frozen
  at anchor 2026-03-15.
- Root cause: `fct_marketing_daily.sql` capped the mart at
  `var("window_end", "2026-03-15")`, and the scheduled refresh ran `dbt run`
  with no `--vars` — so the mart never moved, and the generator "auto-detected"
  MAX(date) from a frozen table.
- The drift validator stayed green the whole time because it detects
  **divergence**, not **staleness**: golden and warehouse agreed perfectly — on
  months-old data.
- Compounding: `daily_synthetic_append.py` appended only 3 of 13 tables, so
  attribution revenue and CRM data were frozen even in the raw layer.

**Fixes shipped:** the mart now spans the full source data range (bounds derived
from the data, never a literal date); the append script advances all 7
time-series tables to a shared target end and self-heals gaps;
`validate_metrics.py` now has a staleness gate that fails when the golden
anchor lags the raw-data frontier by >1 day. The gate was regression-tested
against the old frozen artifact: it fails with exactly the 93-day lag that
previously went undetected.

**Lesson (now encoded in the code comments):** a validator that only checks
consistency will happily bless a perfectly consistent, completely stale system.
Freshness is a separate contract and needs its own gate.

### 2.2 Credibility leaks — FIXED (Phase 0)

- `.mcp.json` hardcoded the author's personal machine paths in all 7 server
  entries → now repo-relative (works for any clone); the Claude Desktop example
  uses an explicit `/ABSOLUTE/PATH/TO/` placeholder.
- `api/main.py` multiplied model output by hardcoded channel factors
  (`prob *= 1.2` for Direct) — a fabricated probability in the very repo whose
  CLAUDE.md forbids hardcoded multipliers → removed; the API now returns the
  model's honest score and declares `model_features_used`.
- Meta "platform-reported ROAS" was computed from the same $100 AOV assumption
  it supposedly validates (circular) → now uses `SUM(purchase_value)/SUM(spend)`.
- README claims fixed: `warehouse_configs/` (didn't exist), `.opencode/opencode.json`
  (didn't exist), "7 MCP servers" (counted a weather demo — deleted), "~10MB"
  CSVs (actually ~60MB and growing), phantom `/model-info` endpoint, phantom
  `ml/notebooks/`. CLAUDE.md §13 no longer claims metrics.js coverage it
  doesn't have.
- Partial anchor months are now labeled "(month to date)" instead of
  "(full month)".

### 2.3 Structural gaps — OPEN (Phases 1–3)

| Gap | Evidence | Phase |
|-----|----------|-------|
| Metric formulas defined in 5–6 unsynchronized places | `metrics.yml`, `generate_golden_metrics.py`, `query_window.py`, `validate_metrics.py`, `metrics.js`, CLAUDE.md | 2 |
| MetricFlow is decorative — nothing runs `mf query`; golden layer is hand-written SQL | no `dbt-metricflow` in requirements; no `mf` call anywhere | 2 |
| Commands contradict governance — `/marketing` says "query ALL MCP servers", CLAUDE.md §14 says golden-first | `.claude/commands/marketing.md:1` | 2 |
| Streamlit "Governed AI analyst" is ungoverned raw NL→SQL, no memory, hardcoded dates | `streamlit_app/app.py:1244-1330` | 2 |
| SQRA never touches an LLM; two scoring paths are circular; not in CI | `scorer.py` adversarial auto-zero; `expected_from_golden` tautology | 3 |
| No real EL story — CSV loaders, one swallowing all errors | `load_supabase.py` `except: pass` ×3 | 2 |
| No packaging — no pyproject, CLI, docker-compose, releases, CONTRIBUTING | repo root | 1 |
| 4× duplicated agent configs, no build pipeline | `.claude/`, `.opencode/`, `cowork_plugin/`, `.agents/` | 1 |
| 62MB+ CSVs committed to git daily, unbounded history | daily bot commits | 1 |
| `warehouse-deploy.yml` regenerates random data and can clobber the golden artifact | workflow line 60, 122–127 | 1 |
| metrics.js loaded by 1 of 5 dashboards; dashboards bake in date constants | `full_funnel_marketing_dashboard.html:150` | 2 |
| No memory / multi-turn analysis anywhere | all skills are one-shot | 3 |

---

## 3. The strategic bet: make SQRA the flagship

The best wedge for a solo open-source project in this landscape is the
**neutral, open benchmark for agentic BI metric fidelity** — not "can the LLM
write SQL" (Spider 2.0 covers that; accuracy collapses to ~17–21% on realistic
warehouses) but:

> Given (a) a raw schema, (b) a semantic-layer MCP server, or (c) a pre-computed
> golden layer, does an agent reproduce the organization's canonical KPIs
> within tolerance — and at what token cost?

Why this wedge wins:

1. **Nobody neutral owns it.** Every existing accuracy claim is vendor content
   marketing, and benchmark annotation quality is a documented scandal (>50%
   error rates found in popular text-to-SQL benchmarks).
2. **Benchmarks are the highest-leverage artifact a solo dev can ship** —
   vendors must engage (run it, dispute it, cite it); citations compound.
3. **It's incremental from this codebase**: golden_metrics.json is the ground
   truth, the mock MCP servers are the harness, CLAUDE.md rules are the rubric,
   and the two postmortems (71.1× ROAS scope-mixing, the 93-day silent
   staleness) are adversarial test cases.
4. **It is simultaneously the strongest hiring-market artifact**: it
   demonstrates the four hottest 2026 data keywords — semantic layer, MCP,
   agent evals, DuckDB — in one deliverable.

The repo repositions as the **reference harness**; the marketing-analytics
stack becomes the benchmark's governed contestant and dataset.

---

## 4. Roadmap

### Phase 0 — Truth & trust (DONE, this branch)

- [x] Fix golden-layer staleness (unbounded mart, data-driven bounds, postmortem in comments)
- [x] Extend daily append to all 7 time-series tables with self-healing backfill
- [x] Staleness gate in `validate_metrics.py` (anchor vs raw frontier, regression-tested)
- [x] De-personalize MCP configs (relative paths in `.mcp.json`)
- [x] Remove fake ML scoring multipliers; honest model output
- [x] Fix Meta platform-ROAS circularity (`purchase_value / spend`)
- [x] Delete weather server; correct every false README/docs claim
- [x] Honest month-to-date labels

### Phase 1 — Installable (1–2 weeks) — largely DONE, remainder below

Shipped on this branch: pyproject + `fullfunnel` CLI, docker-compose,
zero-credential default quick start, CONTRIBUTING/CHANGELOG/templates,
ruff + CLI + config-drift CI gates, single-sourced agent configs,
warehouse-deploy hardening, catch-up-to-today data feed with per-table
freshness gates.

#### Phase 1 — remaining (tracked here as the near-term roadmap)

**1. Hosted demo.**
- **Streamlit Community Cloud** — previous attempts failed because the app
  expects `data/olist_analytics.duckdb`, which is gitignored and never
  committed (only the CSVs are). The fix is a startup bootstrap in the app:
  if the DuckDB file is missing, build it on first boot (load CSVs → dbt run →
  golden metrics — i.e., what `fullfunnel demo` does), cache it, then serve.
  Owner action: deploy the repo at share.streamlit.io after the bootstrap
  lands.
- **GitHub Pages** for the five HTML dashboards (today they render as raw
  source when linked from the repo). Owner action: enable Pages in repo
  settings; then a publish workflow can ship `dashboards/` on every refresh.

**2. Data out of git** — stop committing ~60MB of CSVs daily. Decision matrix:

| Option | How | Pros | Cons |
|--------|-----|------|------|
| **A. Regenerate, don't store (recommended)** | The standalone baseline is seeded (`np.random.seed(42)`) and daily appends are date-seeded — the whole dataset is deterministic. Clone → `fullfunnel demo` regenerates everything locally in seconds; nothing is hosted. Keep only `golden_metrics.json` committed as the artifact of record. | Zero storage, zero hosting, clone shrinks permanently, "data as code" is a great story | The committed dataset today is **Olist-anchored** (real Kaggle-derived order ids); regenerated standalone data is a *different* universe, so golden metrics change once at migration. CI must guard determinism across numpy/pandas versions (pin + a reproducibility test) |
| B. Rolling GitHub Release | Daily workflow uploads Parquet snapshots to a `data-latest` release; `load_duckdb.py` downloads with a local cache | Keeps the exact Olist-anchored dataset; Parquet is ~5–10× smaller; free | Consumers need network on first run; workflows/CI/freshness gates must read from the release manifest |
| C. Object storage (S3/GCS/R2) + DuckDB-over-HTTPS | Publish Parquet; DuckDB queries `https://` directly | The most "modern data platform" pattern; no download step | Costs money, needs credentials/secrets, overkill for synthetic data |
| D. Data-only git branch/repo | Move commits to an orphan branch | Main history clean | Total storage still grows unboundedly; solves the wrong problem |

  Decisions to make before executing: (1) keep the Olist-anchored dataset
  (→ B) or accept a one-time metric reset to the fully regenerable standalone
  dataset (→ A)? (2) rewrite existing git history to reclaim the ~60MB×days
  already committed (git-filter-repo — breaks existing clones/forks) or leave
  history and only stop the growth? Recommendation: **A + leave history**,
  pin numpy in `pyproject.toml`, add a determinism test to CI.

**3. Release v0.9.0** — after this branch merges to `main`: tag `v0.9.0`,
publish a GitHub Release with the CHANGELOG's Unreleased section, and move
that section under `[0.9.0]`. Tagging the feature branch would version
pre-merge history, so this deliberately waits for the merge.

#### Phase 1 — original checklist

- [x] `pyproject.toml` + `src/` package; extras: `[duckdb]` (default), `[bigquery]`, `[snowflake]`, `[ml]`
- [x] CLI: `init` (writes configs), `demo` (synthetic data → DuckDB → golden → Streamlit, zero credentials, <5 min), `validate`, `bench`
- [x] `docker-compose.yml` (streamlit + api + mlflow, seeded data)
- [x] Make `--standalone` synthetic the default path; Kaggle/Olist becomes opt-in
- [ ] Stop committing daily CSVs to git — see the decision matrix in the remainder above
- [x] Fix `warehouse-deploy.yml`: deploy from committed data, never regenerate; add `concurrency:` groups; never let it overwrite the DuckDB-derived golden artifact
- [x] CHANGELOG; CONTRIBUTING with dev setup + good-first-issues; issue templates; ruff in CI
- [ ] Tag `v0.9.0` (after merge to main — see remainder above); mypy in CI
- [x] Single-source agent configs: one `agent_config/` tree + build script rendering `.claude/`, `.opencode/`, `cowork_plugin/`, Gemini, with a CI `--check`
- [ ] Hosted demo: Streamlit Community Cloud + dashboards on GitHub Pages — see the remainder above (needs app bootstrap + owner account actions)
- [ ] README ≤150 lines: one sentence, one GIF, three install commands; portfolio content moves to `docs/about.md`

### Phase 2 — Make the architecture real (3–4 weeks)

- [ ] MetricFlow on the query path: `generate_golden_metrics.py` calls `mf query`; delete duplicated SQL in `query_window.py` / `validate_metrics.py`; `mf validate-configs` in CI. One metric definition, everywhere.
- [ ] A single governed **analytics MCP server** as the product: `list_metrics`, `get_metric(metric, window, grain)`, `explain_metric`, `get_funnel` (server-side ordering validation), `compare_windows` — every response carrying `{value, metric_id, formula, scope, window, attribution_model, source}`. Guardrails as tool contract, not prompt. Platform mocks demoted to test fixtures.
- [ ] Rebuild the Streamlit chat on those tools: full conversation history, metric definitions injected from `metrics.yml` at runtime, "how was this computed" expander, streaming.
- [ ] Memory: persist analyses to DuckDB; `recall_analyses(topic, since)` tool.
- [ ] Real EL: dlt pipelines (verified sources exist for Google Ads, GA4, Facebook Ads, HubSpot, Salesforce); ship one real connector (GA4 Data API — free) behind a small Connector protocol; delete `load_supabase.py`'s silent `except: pass`.
- [ ] dbt hardening: `packages.yml` (dbt_utils, dbt-expectations, elementary), grain tests on composite-key marts, model contracts on golden-feeding marts, `sources.yml` freshness blocks + `dbt source freshness` in CI, `exposures:` for dashboards and MCP servers, dbt docs to GitHub Pages.
- [ ] JSON Schema + pydantic contract for `golden_metrics.json`; dashboards `fetch()` it at load instead of baking constants; retire or golden-route `generate_dashboards.py`.

### Phase 3 — The wedge (ongoing)

- [ ] SQRA v2: put a model in the loop (Agent SDK / tool-use loop over the MCP stack), fix the two circular scorings (adversarial auto-zero; `expected_from_golden` tautology), independent expected values.
- [ ] The three-architecture benchmark: raw text-to-SQL vs semantic-layer MCP vs golden layer, across ≥2 models, scoring numeric fidelity + governance compliance (labels, scope-mixing, funnel integrity) + token cost.
- [ ] Publish methodology + leaderboard; nightly CI with `--min-score` gate; score badge in README.
- [ ] Launch sequence: dbt Slack (#tools-and-integrations) → r/dataengineering war story ("An AI dashboard reported 71.1× ROAS" / "My drift gate was green for 93 days while the data was stale") → Show HN ("an eval harness that catches your AI analyst lying about metrics").

### What to CUT (less is more)

- ~~Weather server~~ (done)
- The 5-warehouse headline — keep DuckDB (default) + BigQuery (production path); Snowflake/Databricks/Supabase move to a portability doc
- n8n / Looker Studio / Antigravity as headline features → `docs/integrations.md`
- The 20-badge wall → CI, license, PyPI, Python version
- Half-real ML: either make lead scoring genuinely production-grade (proper preprocessing pipeline, categorical features, calibration) or move it to `examples/`

---

## 5. Competitive positioning summary

| Player | OSS | Approach | Relevance |
|--------|-----|----------|-----------|
| dbt/Fivetran (Agents Schema) | partial | metrics as customer-owned context tables | Don't compete on the spec — become its best small-stack reference + test suite |
| Cube D3 | core | semantic-layer agents | Loudest voice; validates the thesis |
| Wren AI (~16k★) | yes | governed text-to-SQL, "open context layer" | Closest OSS analog; doesn't do pre-computed metrics or evals |
| Snowflake Cortex Analyst / Databricks Genie | no | semantic-model NL→SQL | Enterprise; cite their accuracy claims as benchmark motivation |
| Vanna AI (~24k★, fading) | yes | RAG text-to-SQL | The anti-pattern contestant for the benchmark |
| Rill / MotherDuck | partial | "BI for humans and agents", local-first DuckDB | Architecture allies; potential benchmark participants |
| nao | early | warehouse-native agent with eval harness | Validates the eval wedge — but they're a vendor; we're neutral |

**The market consensus ("agents need semantic context") is won. The open
questions are proof (who measures accuracy neutrally) and practice (who makes
governed context easy at small scale). This project answers both.**

---

## 6. Success metrics

- Time-to-first-value for a stranger: **<5 minutes, zero credentials** (currently 1–2 hours + Kaggle key)
- SQRA benchmark published with ≥3 architectures × ≥2 models, re-runnable by anyone
- CI gates: drift ✅ (exists) + staleness ✅ (shipped) + lint/type + `mf validate-configs` + SQRA `--min-score`
- Evidence of a second human: 1 external contributor, 10 closed issues, a real launch thread
- One metric definition source (currently 5–6)
