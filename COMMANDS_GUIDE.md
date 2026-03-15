# ⌨️ Analytical Commands Guide

This project includes specialized "Slash Commands" that turn your AI clients (Claude Desktop, OpenCode, Antigravity) into expert marketing analysts. These commands orchestrate multiple MCP tools to give you instant, governed answers.

---

## 🚀 How to Use Commands

### 1. Claude Desktop
Type the command directly into the chat box. Claude will see the definition in the `cowork_plugin` folder and execute the steps.
- **Example:** *"Run `/marketing` for last quarter."*

### 2. OpenCode CLI
Type the command in the terminal chat. OpenCode uses these as "Expert Skills."
- **Example:** `> /attribution what is the ROAS difference between models?`

### 3. Antigravity IDE
Ask your assistant to follow a specific command blueprint.
- **Example:** *"Use the `/pipeline` command to analyze our funnel bottlenecks."*

---

## 📜 Command Reference

### 📈 `/marketing`
**Goal:** Blended performance analysis across Google Ads, Meta Ads, and GA4.
- **Tools used:** `google-ads`, `meta-ads`, `ga4`, `salesforce`.
- **Primary Metric:** Blended CAC (Cost / Conversions) and ROAS.
- **Best for:** Weekly executive summaries and budget allocation reviews.

### 🔍 `/attribution`
**Goal:** Compare First-Touch, Last-Touch, and Linear models to find hidden gems.
- **Tools used:** `dbt-semantic-layer`.
- **Primary Metric:** Revenue credit by model.
- **Best for:** Decisions on top-of-funnel (awareness) vs. bottom-of-funnel (direct) spend.

### 🧬 `/pipeline`
**Goal:** Full funnel visibility from CRM leads to deal revenue.
- **Tools used:** `hubspot`, `salesforce`, `dbt-semantic-layer`.
- **Primary Metric:** Win rate, Lead-to-Opp conversion, Pipeline Velocity.
- **Best for:** Sales and Marketing alignment meetings and revenue forecasting.

---

## 🛠️ Adding New Commands
You can create your own commands by adding a new Markdown file to:
- `cowork_plugin/commands/` (for Claude Desktop)
- `.opencode/commands/` (for OpenCode CLI)

**Template:**
```markdown
---
description: Brief description of the command.
---
# /yourcommand [query]
## Steps
1. Call [mcp-server].[tool-name]
2. ...
3. Provide summary.
```
