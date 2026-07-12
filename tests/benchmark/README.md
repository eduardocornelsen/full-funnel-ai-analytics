# SQRA — Search Quality & Retrieval Accuracy benchmark

**The question this benchmark answers neutrally:** given the same questions and
the same data, does an analytics retrieval path reproduce the organization's
**canonical KPIs** — and for AI agents, at what token cost?

Existing text-to-SQL benchmarks (Spider 2.0 et al.) score "can the model write
SQL that executes." SQRA scores something stricter and more business-relevant:
**metric fidelity against a governed source of truth**, including whether
plausible-but-wrong formulations (scope mixing, wrong denominator, wrong spend
field) get caught.

## Design (v2)

- **No literals.** Case dates are anchor-relative tokens (`$anchor-29d`)
  resolved from the golden artifact at load time; expected values resolve from
  the artifact via `expected_ref`. The dataset grows daily — v1's hardcoded
  expectations silently rotted; v2's cannot.
- **Every surface is a cross-implementation check.** MCP servers (pandas over
  CSVs), raw SQL (DuckDB over CSVs), `query_window` (independent SQL), and the
  golden artifact (dbt marts + generator) are *different code paths* that must
  agree within tolerance (±$1, ±0.5% relative, ±1 count).
- **The golden surface is double-entry**, not self-referential: artifact values
  are compared against an independent recomputation (v1 compared the artifact
  to itself — tautological precision 1.0).
- **Adversarial detection is on merit**, not by label: flawed queries carry the
  CANONICAL expected value; they count as "caught" only if their result
  actually diverges (or errors). v1 zeroed them because they were *labeled*
  adversarial — 100% detection by construction. A flawed query that happens to
  produce the right number is now honestly scored as NOT caught.

## Running

```bash
python scripts/run_sqra.py                 # 50 deterministic cases, 5 surfaces
python scripts/run_sqra.py --min-score 95  # the CI gate
python scripts/run_sqra.py --surface nl2sql --verbose
```

Runs in CI on every PR and in the daily scheduled refresh.

## Agent benchmark (model in the loop)

Three agent architectures answer the same natural-language questions, scored
with the same tolerance-typed precision against golden-derived ground truth:

| Architecture | Grounding |
|---|---|
| `golden-tools` | the governed analytics server (pre-computed metrics + governance envelopes) |
| `raw-sql` | schema dump + free SQL against the DuckDB warehouse |
| `semantic-layer` | MetricFlow (`mf query`) over the dbt semantic layer |

```bash
export ANTHROPIC_API_KEY=...
python scripts/run_sqra.py --agents                    # all three architectures
python scripts/run_sqra.py --agents --arch raw-sql --limit 5
python scripts/run_sqra.py --agents --model claude-sonnet-5
```

Metrics per architecture: **accuracy** (exact within tolerance), **mean
precision** (partial credit for near-misses), **tokens/question** (the cost of
the grounding strategy). Results are written to
`tests/benchmark/agent_results_<model>.json`; the weekly
`agent-benchmark.yml` workflow runs it when the `ANTHROPIC_API_KEY` repo
secret is configured and uploads the report as an artifact.

## Leaderboard

*Pending the first credentialed run (`ANTHROPIC_API_KEY`). Populate from
`agent_results_*.json`:*

| Model | Architecture | Accuracy | Mean precision | Tokens/question |
|---|---|---|---|---|
| — | golden-tools | — | — | — |
| — | raw-sql | — | — | — |
| — | semantic-layer | — | — | — |

## Adding cases

Add to `cases.json` with an `expected_ref` (never a literal value) and
anchor-relative date tokens (never literal dates). Adversarial cases set
`is_adversarial: true` and point `expected_ref` at the value the *correct*
query would return.
