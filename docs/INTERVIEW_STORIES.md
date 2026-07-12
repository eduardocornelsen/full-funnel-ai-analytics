# Interview Stories & Talk Tracks

> Polished narratives for data-platform / analytics-engineering / AI-engineering
> interviews, all grounded in verifiable commits in this repository. Every
> number below is real and checkable — that is the point. Nothing here requires
> embellishment; the failure stories are more valuable than the feature list.

---

## The elevator pitch (30 seconds)

> "I built an open-source analytics platform around one idea: AI agents
> shouldn't write ad-hoc SQL against your warehouse — they should read
> pre-computed, drift-validated metrics from a governed golden layer. dbt
> defines the metrics, a generator snapshots them to a versioned JSON artifact,
> CI gates on both drift *and* freshness, and six MCP servers expose the data
> to any AI client. I also built an eval harness that scores whether the AI
> actually reproduces the canonical numbers. The most valuable things I got
> out of it were two production-grade postmortems — a 71× ROAS bug from
> scope-mixing, and 93 days of silent staleness that my own validation gate
> couldn't see."

---

## Story 1 — The 71.1× ROAS bug (metric governance)

**Use for:** "Tell me about a data quality issue you caught." / "How do you
make AI analytics trustworthy?" / "Describe a time a dashboard was wrong."

**Situation.** An AI-generated dashboard reported Blended ROAS of 71.1× —
absurd for e-commerce, where 2–8× is realistic. Nobody's SQL was "wrong";
every individual number was correct.

**Task.** Find why a correct pipeline produced a nonsensical KPI, and make the
failure class impossible, not just this instance.

**Action.** The root cause was **scope mixing**: all-time attributed revenue
divided by 90-day ad spend. Two individually-correct numbers, one meaningless
ratio. I fixed it three ways, in layers:
1. **Data layer** — restructured the attribution mart to order-date grain so
   time-windowing is possible at all (the previous all-time grain made
   filtering silently impossible).
2. **Artifact layer** — the golden metrics snapshot is organized by scope
   (`windowed_90d`, `all_time`, calendar months); every section is
   self-contained, so a consumer physically can't take a numerator from one
   window and a denominator from another without leaving the section.
3. **Policy layer** — a written rule ("never mix scopes; every ROAS/CVR
   carries its attribution window in the label") enforced by agent
   instructions and a shared metrics module.

**Result.** Blended ROAS is now labeled `Linear attribution · 90d`, computed
from a single window section, and the drift validator re-derives it from the
warehouse in CI on every PR. The bug became the project's founding story and
its best test case.

**Senior-level kicker:** the deep lesson isn't "check your denominators" — it's
that *correct components compose into wrong answers when scope isn't part of
the type*. That's why the golden layer treats the window as part of the
metric's identity, not a query parameter.

---

## Story 2 — 93 days of silent staleness (the validator that lied by being right)

**Use for:** "Tell me about a failure of your own design." / "How do you
monitor data pipelines?" / "What's the difference between data quality and
data observability?"

**Situation.** The platform had a drift gate I was proud of: CI re-computed
every golden metric from the warehouse and failed on any divergence. It ran
daily. It was green for three months straight. During those three months, the
golden layer was **93 days out of date**.

**Task.** Understand how a validation system passed daily while the thing it
validated was frozen — then fix the class, not the instance.

**Action.** Root cause chain: a dbt mart had a literal-date fallback
(`var("window_end", "2026-03-15")`), the scheduled refresh ran `dbt run`
without `--vars`, so the mart froze at the fallback; the metrics generator
"auto-detected" its anchor as `MAX(date)` **from the frozen mart**; and the
validator compared the golden snapshot against **the same frozen mart** —
perfect agreement, forever. Meanwhile the raw CSVs grew daily, and a second
bug compounded it: the daily append job only advanced 3 of 13 tables, so even
the raw layer had frozen revenue against growing spend.

The fix:
1. Removed the literal-date default — the mart now derives its bounds from the
   source data itself (`MIN`/`MAX` over the staged inputs), so it structurally
   cannot freeze.
2. Rebuilt the append job around a table registry: all seven time-series
   tables advance to one shared target date, each backfilling from its own
   last date — a table that falls behind self-heals on the next run.
3. Added a **staleness gate** to the validator: the golden anchor is compared
   against the *raw data frontier* (not the mart — the mart was the liar),
   failing if it lags by more than a day. I regression-tested the gate against
   the old frozen artifact: it fails with exactly the 93-day lag that had gone
   undetected.

**Result.** Anchor rolled forward from 2026-03-15 to the data frontier on the
next run; 82 dbt tests and 26 pytest checks green; the validator now checks
two orthogonal contracts — *consistency* (drift) and *currency* (staleness) —
and the postmortem lives in the code comments where the next maintainer will
read it.

**Senior-level kicker:** "My validator detected divergence, not staleness. A
system can be 100% consistent and 100% useless. Freshness is a separate
contract with its own gate — and the freshness reference must be upstream of
everything that can freeze." This maps directly to `dbt source freshness`,
SLAs/SLOs on data products, and why observability ≠ testing.

---

## Story 3 — Why a golden layer instead of text-to-SQL (architecture)

**Use for:** "Design an AI analytics system." / "How would you let a PM query
the warehouse in natural language?" / "Semantic layer vs text-to-SQL?"

**The argument, in interview form:**

1. Text-to-SQL accuracy collapses on realistic warehouses — Spider 2.0 showed
   ~17–21% execution accuracy for frontier models on enterprise-grade
   workflows. Worse, the failure mode isn't a crash; it's a *plausible wrong
   number* handed to someone who can't verify it.
2. A semantic layer fixes definitional ambiguity (which of the six revenue
   columns?), but query-time generation still leaves arithmetic and window
   selection to the model on every request.
3. So I inverted the flow: **compute once, serve many.** dbt marts → a
   generator writes a versioned JSON artifact with pre-computed metrics per
   window (7/30/60/90/180-day, calendar months, all-time) → the AI's
   instructions and tools say *copy exact values; never recalculate*. The
   agent's job shrinks from "derive the number" to "retrieve and present the
   number" — which LLMs are actually reliable at.
4. Trade-off, stated honestly: you lose ad-hoc flexibility on the pre-computed
   path. The escape hatch is a parameterized query tool for arbitrary windows,
   clearly labeled "ad-hoc — not from golden layer," so governed and ungoverned
   answers are visually distinct to the stakeholder.
5. Side benefit that matters at scale: pre-computed metrics are the cheapest
   possible agent context — no schema dump, no multi-turn SQL retries, no
   token burn re-deriving context per question.

**One-liner:** "Deterministic answers from a governed artifact, with an
explicit, labeled escape hatch for everything else."

---

## Story 4 — Killing my own fake number (integrity)

**Use for:** "Tell me about a time you pushed back on shipping something." /
integrity probes / code-review culture questions.

**Situation.** My lead-scoring API had a line I wrote early on for demo
effect: `if channel == "Direct": prob *= 1.2` — a hardcoded multiplier on the
model's output probability. The same repo's governance rules explicitly ban
hardcoded multipliers in metrics.

**Action.** During a self-audit I treated my own repo the way a skeptical
staff engineer would on a 10-minute skim. That line fails the audit instantly:
a fabricated probability is worse than no ML at all, because it wears the
credibility of the model. I removed the multipliers, made the API return the
model's honest score with a `model_features_used` field declaring exactly what
the model saw, and kept `channel`/`country` as routing metadata explicitly
documented as *not* model features until they're genuinely trained in.

**Result/kicker.** "The fastest way to lose a technical audience is one
fabricated number. I'd rather ship a weaker honest model than a stronger-
looking dishonest one — and I've deleted my own 'for effect' code to prove
it." (Also a good hook for discussing probability calibration and why
post-hoc output scaling destroys it.)

---

## Story 5 — Six copies of one formula (semantic layer, the honest version)

**Use for:** "What's the hardest part of semantic layers?" / "How do you keep
metrics consistent?" / self-awareness probes ("what's wrong with your project?").

**The honest telling.** My canonical metric formulas ended up defined in six
places: the MetricFlow YAML, the golden-metrics generator's SQL, an ad-hoc
query script (whose own comment admitted "kept in sync manually"), the drift
validator's SQL, a JavaScript metrics module for dashboards, and the agent's
instruction file. The semantic layer existed — but nothing queried through it,
so it was a credential, not an architecture. I had rebuilt, by hand, the exact
sprawl semantic layers exist to kill.

**The plan (in progress, documented in docs/STRATEGY.md):** make MetricFlow the
only definition point — the golden generator calls `mf query` instead of
carrying its own SQL; the ad-hoc script becomes a thin parameterized wrapper;
`mf validate-configs` runs in CI. One definition, N consumers.

**Kicker:** "Industry data says only ~18% of teams use dbt's semantic layer,
and having lived why, I get it: the layer is easy to *write* and hard to make
*load-bearing*. The test I now apply: if you deleted the YAML, would anything
break? If not, you don't have a semantic layer — you have documentation."

---

## Story 6 — Evals for AI analytics (the frontier story)

**Use for:** "How do you test AI systems?" / "What would you build next?" /
differentiation in AI-adjacent data roles.

**The telling.** Dashboards get tested; AI analysts mostly don't. I built SQRA
— a benchmark harness that scores retrieval accuracy across surfaces (golden
layer, SQL, semantic definitions, adversarial cases) with tolerance-typed
scoring: exact match for counts, absolute tolerance for dollars, percentage
tolerance for ratios, because "correct" means different things per metric type.

Then, auditing it honestly: my first version had two circular scorings — the
adversarial cases "detected" flaws because they were *labeled* adversarial,
and one surface set expected = retrieved, making precision tautologically 1.0.
And no LLM was in the loop at all; it tested my plumbing, not the agent. That
self-audit is now the v2 roadmap: model-in-the-loop end-to-end runs over the
MCP stack, independently-computed expected values, and a nightly CI gate with
a published score.

**Kicker:** "Every accuracy number in this market comes from a vendor selling
the winning architecture. The neutral benchmark for 'does the agent reproduce
the org's canonical KPIs, at what token cost' doesn't exist yet. That's the
most valuable thing a solo open-source project can ship — and evals are the
least-supplied skill in data hiring right now."

---

## Story 7 — Validation as a system, not a step (and knowing what's redundant)

**Use for:** "How do you test data pipelines?" / "Design a data quality
strategy." / "What's the difference between testing and validation?"

**The telling.** My validator does three jobs, and being able to name them —
including where one is deliberately redundant — is the point:

1. **Double-entry bookkeeping.** The metrics generator and the validator carry
   *independently written* SQL for the same metric definitions. Same warehouse,
   same moment — but two implementations must agree within tolerance. This
   caught a real bug class twice: two other code paths had quietly kept an old
   Meta ROAS formula after the canonical one changed.
2. **Freshness contracts.** Anchor vs raw-data frontier, cross-table skew
   (spend advancing while revenue tables freeze — which silently deflates
   ROAS), and wall-clock lag. The generator can't check these; it has no
   concept of "should be newer."
3. **Cross-context parity.** The same validator runs against BigQuery and
   Snowflake after every deploy, comparing them to the DuckDB-derived
   committed artifact — same data, same dbt models, different engine must
   yield the same numbers. That's where dialect bugs (date arithmetic macros,
   type casts) surface.

Plus a subtle one: CI validates the *committed* artifact using only
**completed calendar months**, because those are anchor-independent — a June
total is identical whether it was computed on July 1st or July 30th. That
property is what makes yesterday's committed artifact comparable against a
warehouse rebuilt today.

**The senior kicker:** "I can also tell you which of these becomes redundant
and when: once the semantic layer is the single definition source (my Phase 2),
the double-entry check proves nothing — both sides would run the same
definition — so its job collapses into freshness + parity, by design.
Validation layers should be built knowing which ones you intend to retire."

---

## Story 8 — Data as code (regenerate, don't commit)

**Use for:** "Tell me about a storage/architecture trade-off." / "How would you
version data?" / reproducibility questions.

**Situation.** Two bots committed ~60MB of synthetic CSVs to git daily. Git
history grew unboundedly — every clone downloads every day's snapshot forever.

**Action.** I noticed the daily data was already a *pure function of the
calendar date* (generators seeded per date, baseline seeded with a constant).
So the rows didn't need storing anywhere — they needed a **reproducibility
contract**. I froze the one non-regenerable thing (the real-data-anchored
baseline) in git, made every environment regenerate the daily days locally
(CI, clones, the daily refresh — all compute byte-identical rows in seconds),
and reduced the bots' daily commit to the 50KB metrics artifact. Then I
guarded the contract: numpy pinned, plus a CI test that regenerates a
reference date and compares against pinned hashes — if a dependency upgrade
ever changes the random stream, CI fails *before* clones start regenerating
data that disagrees with the committed metrics.

**Result.** History growth: ~22GB/year → ~18MB/year. Fresh-clone experience
unchanged (one command materializes everything). And the model proved itself
the day it shipped: UTC midnight rolled over during verification and the
pipeline caught the new day up automatically.

**Kicker:** "It's the lockfile principle applied to data: commit the recipe
and the checksum, not the artifact — but only after you've separated what's
truly source (the real-data baseline) from what's derivable (everything
else). And a reproducibility contract without an enforcement test is just a
hope."

---

## The 5-minute repo walkthrough (screen-share script)

1. **The one-liner** (30s): governed marketing analytics that AI agents can't
   hallucinate around — dbt golden layer + MCP + drift/staleness gates + evals.
2. **Show `golden_metrics.json` `_meta`** (60s): anchor date, windows,
   schema_version, the "copy, never recalculate" note. "This artifact is the
   API between my data platform and every AI client."
3. **Show the CI gates** (60s): drift validation + the staleness gate; tell the
   93-day story in three sentences. This is where senior interviewers lean in.
4. **Live demo** (90s): `/marketing` command or Streamlit — question in,
   governed numbers out, labels on every KPI.
5. **Show the postmortem comments in the code** (30s):
   `fct_marketing_daily.sql` header. "I document failures where the next
   maintainer will trip over them."
6. **The roadmap** (30s): benchmark-first strategy from `docs/STRATEGY.md` —
   shows product thinking, not just code output.

---

## Q&A prep — likely follow-ups and strong answers

**"Isn't a pre-computed JSON just… a cache? What about cache invalidation?"**
Yes — deliberately. It's a materialized read-model with explicit versioning,
and the two hard problems (staleness, drift) each have a CI gate. The lesson
from my postmortem is that the invalidation signal must come from upstream raw
data, not from anything that can freeze along with the cache.

**"How does this scale beyond 500k rows?"**
The pattern scales because the artifact is aggregates, not rows — its size is
O(metrics × windows), independent of fact-table size. The compute moves to the
warehouse/dbt; incremental models and partitioning handle volume; the artifact
moves from git to object storage (Parquet over HTTPS, which DuckDB queries
directly). Git-as-data-lake is a demo convenience I'm explicitly retiring.

**"Why MCP rather than a chat UI with function calling?"**
MCP decouples the data contract from the client: the same six servers serve
Claude Desktop, Claude Code, OpenCode, and Gemini CLI with zero code changes.
Client churn is high; the protocol layer is what persists. (And the stakeholder
chat UI consumes the same tools — one governed path.)

**"What would you do differently?"**
Three things: (1) make the semantic layer load-bearing from day one instead of
decorative; (2) freshness gates before drift gates — staleness bit me, drift
never did; (3) fewer integrations, deeper — five warehouses was resume-driven
development; DuckDB + one cloud path with contracts and evals is worth more
than five shallow targets.

**"What's the hardest bug you've dealt with?"** → Story 2 (staleness).
**"Tell me about disagreeing with a stakeholder."** → Story 4 works: the
stakeholder was my own demo instinct; the disagreement was resolved by policy
("no fabricated numbers"), not taste.

---

## Keyword map (2026 hiring signals → where this project demonstrates them)

| Hot keyword | Your evidence |
|---|---|
| Semantic layer / MetricFlow | `dbt_project/models/metrics/metrics.yml` + the honest Story 5 |
| MCP / agent tooling | 6 servers, 4 clients, `.mcp.json`, tool-description design |
| Agent evals | SQRA harness + v2 benchmark plan (Story 6) |
| DuckDB / local-first analytics | entire default stack |
| Data contracts / quality gates | drift + staleness validators, dbt tests, JSON schema roadmap |
| Data observability | Story 2 — consistency vs currency framing |
| Attribution modeling | 4-model attribution marts, scope-labeled ROAS |
| MLOps | XGBoost + MLflow + FastAPI + the integrity fix (Story 4) |
| Cost-aware AI | pre-computed context as the cheapest agent grounding |

## Numbers worth memorizing

- **71.1×** — the impossible ROAS; **2–8×** — realistic e-commerce blended ROAS
- **93 days** — silent staleness the drift gate missed; **1 day** — new staleness tolerance
- **7 tables** advanced by the append feed (was 3 of 13 — the frozen-revenue compounding bug)
- **82** dbt tests + **26** pytest checks green after the fix
- **~17–21%** — frontier-model execution accuracy on Spider 2.0 (why text-to-SQL alone fails)
- **~18%** — teams using dbt semantic layer (why "governed but easy" is the gap)
- **5–6** places one formula was defined (the sprawl the roadmap collapses to 1)
- **3 validation jobs** — double-entry recomputation, freshness contracts, cross-warehouse parity (and which one is designed to be retired)
- **~22GB/year → ~18MB/year** — git history growth after the regenerate-don't-commit data model
- **7 pinned generator hashes** — the CI determinism contract that makes "data as code" safe
