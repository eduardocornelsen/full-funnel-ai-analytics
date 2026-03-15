## Rewriting Plan:
- Focus on the biggest achieviment here. As our research stated: "Semantic layers dramatically improve AI query reliability — average confidence in AI-generated queries is just 5.5/10 without them, but tools like dbt MCP (60+ tools, v1.10.0) and Cube.dev now provide production-grade MCP servers that give LLMs deterministic metric definitions, reducing hallucination and enforcing governance across Snowflake and Databricks"

---

# LinkedIn Post — Eduardo

## Option A: The Technical Builder (strongest for analytics/engineering roles)

---

Marketing analytics just changed and most attribution tools should be worried

I connected 7 data sources to a single AI interface. Not just a dashboard — a system where anyone can ask "which channels actually drive revenue?" and get the answer in 15 seconds

Here's what I built:

I started with real e-commerce data (Olist, 100K orders) and built a governed dbt semantic layer on top. MetricFlow defines what every metric actually means — CAC, ROAS, LTV, win rate. One definition, consumed everywhere

Then I plugged MCP servers directly into the warehouse AND 5 marketing platforms
Now I can query Google Ads, Meta Ads, GA4, HubSpot, and Salesforce from natural language. Through Claude, Gemini, OpenCode — any MCP client

I built it to work across 5 data warehouses. BigQuery, DuckDB, Supabase, Snowflake, Databricks. Same semantic layer, same MCP servers, same results. Zero query changes between engines

I added multi-touch attribution: first-touch, last-touch, linear, time-decay. The AI doesn't just show you numbers — it tells you which channels are under-credited and where to reallocate budget

And here's where it gets interesting: I trained a lead scoring model (XGBoost + MLflow), deployed it via FastAPI, and connected it to n8n for automated routing. Hot leads go to Sales. Warm leads get nurtured. Cold leads get monitored. All triggered by a single API call

Then I built a Cowork plugin so non-data people can type /marketing and get a full cross-platform performance report. Brand voice baked in. Output format is whatever you want

Real example I ran:

"Show me the complete marketing funnel for Q1 2018: ad spend across Google and Meta, website sessions by channel, lead conversion rates from HubSpot, and final revenue. Calculate blended CAC and ROAS."

It queried 4 MCP servers, joined the data through the semantic layer, calculated attribution-adjusted metrics, and generated a full dashboard with KPIs, trend charts, and recommendations

In about 20 seconds

Total cost: $0/month on free tiers. No Fivetran. No Tableau license. No enterprise contracts

The stack:
→ dbt Core + MetricFlow (semantic layer)
→ 7 MCP servers (BigQuery, dbt, Google Ads, Meta, GA4, HubSpot, Salesforce)
→ 4 AI clients (Claude Desktop, OpenCode, Gemini CLI, Antigravity)
→ 5 warehouses (BigQuery, DuckDB, Supabase, Snowflake, Databricks)
→ XGBoost + MLflow + FastAPI (lead scoring)
→ n8n (automated routing)
→ Looker Studio + Streamlit + React artifacts (visualization)

Every MCP server is open source. The mock servers have the exact same interface as real platform APIs — swap to production with zero code changes

What am I missing?

GitHub: [link]
Demo video: [link]

#DataAnalytics #MCP #MarketingAttribution #dbt #BigQuery #MLflow #AI #RevOps

---

## Option B: The Business Storyteller (strongest for marketing analytics/RevOps roles)

---

Every company running paid ads asks the same question:

"Which channels actually drive revenue, not just clicks?"

I got tired of seeing teams answer this with spreadsheets and guesswork. So I built the system that answers it in 15 seconds

Here's the problem: your Google Ads data lives in Google. Your Meta data lives in Meta. Your CRM lives in HubSpot or Salesforce. Your website data lives in GA4. To connect them, you either pay $50K+ for a BI stack or you export CSVs and pray

I took a different approach

I built 7 MCP servers that connect all these platforms to a single AI interface. Ask a question in plain English. The AI queries every platform, joins the data through a governed semantic layer, and returns a formatted analysis with attribution-adjusted metrics

"Compare first-touch vs last-touch attribution for our top 5 channels. Which are under-credited? Where should we move budget?"

The AI calls Google Ads, Meta Ads, GA4, HubSpot, and Salesforce. It runs four attribution models. It identifies that organic search drives 22% of first touches but gets 8% of last-touch credit. It recommends reallocating $3K/month from branded search to organic content

That's not a dashboard you stare at. That's an analyst sitting next to you

But I didn't stop at analytics

I trained a lead scoring model that predicts which leads will become high-value customers. It looks at marketing source, website behavior, order history, and review patterns. Deployed via API, connected to n8n for automated routing

Score above 70? Routed to Sales immediately
Score 40-69? Added to nurture sequence
Below 40? Long-term monitoring

A marketing manager types /marketing in the AI interface and gets:
→ Blended CAC across all channels
→ ROAS by platform (Google vs Meta vs Organic)
→ Lead quality distribution by source
→ Budget reallocation recommendations

No SQL. No dashboard training. No waiting for the data team

And the kicker? The whole thing runs on free tiers. $0/month base cost

The traditional marketing analytics stack costs $5K-50K/month (warehouse + ETL + BI + attribution tool). This does the same thing with open source tools and AI

I open-sourced everything: [GitHub link]

What would you ask your marketing data if you could just... ask it?

#MarketingAnalytics #Attribution #RevOps #LeadScoring #AI #GrowthAnalytics

---

## Option C: The Provocative Hot Take (strongest for engagement/virality)

---

I replaced a $50K/year marketing analytics stack with 7 MCP servers and $0/month in infrastructure

No Fivetran. No Tableau. No Looker license. No attribution tool subscription

Here's what happened:

Week 1: Loaded 100K real e-commerce orders + synthetic data for Google Ads, Meta Ads, GA4, HubSpot, and Salesforce into BigQuery (free tier)

Week 2: Built a dbt semantic layer with 30+ models and 15 governed metrics. "ROAS" means one thing now. Everywhere. Forever

Week 3: Connected 7 MCP servers to Claude, OpenCode, Gemini CLI, and Antigravity. Any of them can query any data source in natural language

Week 4: Trained a lead scoring model with MLflow. Deployed via FastAPI. Connected to n8n for automated routing. Hot leads go to Sales in seconds, not days

Week 5: Built dashboards in Looker Studio and Streamlit. Plus Claude generates Voi-style React dashboards on the fly from any query

Week 6: Proved it works on BigQuery, DuckDB, Supabase, Snowflake, AND Databricks. Same query. Same results. Five different engines

The query that convinced me this actually works:

"Show me the complete marketing funnel: ad spend across Google and Meta → website sessions by channel → lead conversion rates → final revenue. Calculate blended CAC and ROAS. Compare first-touch vs last-touch attribution"

It pulled data from 4 different MCP servers, joined it through the semantic layer, ran attribution calculations, and returned a formatted executive summary with charts

In 20 seconds

What a junior analyst does in 2 days, this does before your coffee gets cold

The entire stack is open source
Every MCP server is swappable (mock → production, zero code changes)
Every warehouse is interchangeable (same dbt models across all 5)
Every AI client works (Claude, Gemini, GPT — your choice)

GitHub: [link]

Am I crazy or did the analytics tool market just get very uncomfortable?

---

## Posting Strategy

**Which version to use:**
- Apply to RevOps/Marketing roles → Post Option B (business story)
- Apply to Analytics Engineering/DS roles → Post Option A (technical)
- Want maximum LinkedIn engagement → Post Option C (provocative)

**Timing:** Post Tuesday-Thursday, 8-10am your timezone

**Attach:** Screenshot of the dashboard (use the Voi-style React artifact)

**First comment:** Pin a comment with the GitHub link + "Here's the full architecture if you want to build this yourself"

**Tag strategy:** Tag 2-3 people whose work inspired you (e.g., the Voi CEO, dbt Labs team, MCP creators). Don't tag more than 3
