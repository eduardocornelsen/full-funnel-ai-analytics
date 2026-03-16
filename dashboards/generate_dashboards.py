"""
Generate static HTML dashboards from mock marketing data.
Run: python dashboards/generate_dashboards.py
Opens: dashboards/index.html
"""
from pathlib import Path
import pandas as pd
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

DATA = Path(__file__).parent.parent / "data" / "mock_marketing"
OUT  = Path(__file__).parent


def load_data():
    gads  = pd.read_csv(DATA / "google_ads_daily_performance.csv")
    meta  = pd.read_csv(DATA / "meta_ads_daily_performance.csv")
    ga4   = pd.read_csv(DATA / "ga4_daily_sessions.csv")
    hs_d  = pd.read_csv(DATA / "hubspot_deals.csv")
    sf    = pd.read_csv(DATA / "salesforce_opportunities.csv")
    return gads, meta, ga4, hs_d, sf


def build_kpis(gads, meta, ga4, hs_d, sf):
    spend       = gads["cost"].sum() + meta["spend"].sum()
    sessions    = ga4["sessions"].sum()
    conversions = ga4["conversions"].sum()
    pipeline    = hs_d["amount"].sum()
    leads       = len(hs_d)
    roas        = (meta["purchases"].sum() * 100) / meta["spend"].sum()
    return {
        "Total Spend":      f"${spend:,.0f}",
        "Total Sessions":   f"{sessions:,.0f}",
        "Conversions":      f"{conversions:,.0f}",
        "Pipeline Value":   f"${pipeline:,.0f}",
        "Leads":            f"{leads:,.0f}",
        "Blended ROAS":     f"{roas:.2f}x",
    }


def channel_share(ga4):
    ch = ga4.groupby("channel_group")["sessions"].sum().reset_index()
    ch.columns = ["channel", "sessions"]
    ch = ch.sort_values("sessions", ascending=False)
    return ch.to_dict(orient="records")


def pipeline_stages(hs_d, sf):
    hs_s  = hs_d.groupby("deal_stage")["amount"].sum().reset_index()
    hs_s.columns  = ["stage", "value"]
    sf_won = sf[sf["probability"] == 100].groupby("stage")["amount"].sum().reset_index()
    sf_won.columns = ["stage", "value"]
    combined = pd.concat([hs_s, sf_won]).groupby("stage")["value"].sum().reset_index()
    return combined.sort_values("value", ascending=False).to_dict(orient="records")


def weekly_spend(gads, meta):
    gads["date"] = pd.to_datetime(gads["date"])
    meta["date"] = pd.to_datetime(meta["date"])
    gads["week"]  = gads["date"].dt.to_period("W").astype(str)
    meta["week"]  = meta["date"].dt.to_period("W").astype(str)
    gw = gads.groupby("week")["cost"].sum().reset_index()
    mw = meta.groupby("week")["spend"].sum().reset_index()
    merged = gw.merge(mw, on="week", how="outer").fillna(0)
    merged.columns = ["week", "google", "meta"]
    merged = merged.sort_values("week").tail(12)
    return merged.to_dict(orient="records")


def render_html(kpis, channels, pipeline, weekly):
    kpi_cards = "".join(
        f'<div class="card"><div class="label">{k}</div><div class="value">{v}</div></div>'
        for k, v in kpis.items()
    )

    channel_rows = "".join(
        f'<tr><td>{r["channel"]}</td><td>{r["sessions"]:,}</td></tr>'
        for r in channels
    )

    pipeline_rows = "".join(
        f'<tr><td>{r["stage"]}</td><td>${r["value"]:,.0f}</td></tr>'
        for r in pipeline
    )

    weekly_labels = json.dumps([r["week"] for r in weekly])
    weekly_google = json.dumps([round(r["google"], 2) for r in weekly])
    weekly_meta   = json.dumps([round(r["meta"], 2) for r in weekly])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Marketing Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0d0d1a; color: #e2e8f0; font-family: system-ui, sans-serif; padding: 24px; }}
  h1 {{ font-size: 1.5rem; margin-bottom: 20px; color: #60a5fa; }}
  h2 {{ font-size: 1rem; color: #94a3b8; margin-bottom: 12px; text-transform: uppercase; letter-spacing: .05em; }}
  .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 28px; }}
  .card {{ background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 10px; padding: 16px; }}
  .label {{ font-size: .75rem; color: #64748b; margin-bottom: 6px; }}
  .value {{ font-size: 1.5rem; font-weight: 700; color: #f87171; }}
  .grid2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 28px; }}
  .panel {{ background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 10px; padding: 20px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .85rem; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #2a2a4a; }}
  th {{ color: #64748b; font-weight: 500; }}
  canvas {{ max-height: 280px; }}
  @media (max-width: 640px) {{ .grid2 {{ grid-template-columns: 1fr; }} }}
  .ts {{ font-size: .7rem; color: #475569; margin-top: 20px; text-align: right; }}
</style>
</head>
<body>
<h1>Full-Funnel Marketing Dashboard</h1>
<div class="kpis">{kpi_cards}</div>

<div class="grid2">
  <div class="panel">
    <h2>Weekly Spend by Platform</h2>
    <canvas id="spendChart"></canvas>
  </div>
  <div class="panel">
    <h2>Traffic by Channel</h2>
    <table>
      <tr><th>Channel</th><th>Sessions</th></tr>
      {channel_rows}
    </table>
  </div>
</div>

<div class="grid2">
  <div class="panel">
    <h2>Pipeline by Stage</h2>
    <table>
      <tr><th>Stage</th><th>Value</th></tr>
      {pipeline_rows}
    </table>
  </div>
  <div class="panel">
    <h2>Channel Mix</h2>
    <canvas id="channelChart"></canvas>
  </div>
</div>

<p class="ts">Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</p>

<script>
const weeks  = {weekly_labels};
const google = {weekly_google};
const meta   = {weekly_meta};

new Chart(document.getElementById('spendChart'), {{
  type: 'line',
  data: {{
    labels: weeks,
    datasets: [
      {{ label: 'Google Ads', data: google, borderColor: '#60a5fa', backgroundColor: '#60a5fa22', fill: true, tension: .3 }},
      {{ label: 'Meta Ads',   data: meta,   borderColor: '#f87171', backgroundColor: '#f8717122', fill: true, tension: .3 }}
    ]
  }},
  options: {{ plugins: {{ legend: {{ labels: {{ color: '#94a3b8' }} }} }}, scales: {{ x: {{ ticks: {{ color: '#64748b', maxTicksLimit: 6 }} }}, y: {{ ticks: {{ color: '#64748b' }} }} }}, responsive: true }}
}});

const chLabels = {json.dumps([r['channel'] for r in channels])};
const chData   = {json.dumps([r['sessions'] for r in channels])};
const chColors = ['#60a5fa','#f87171','#fbbf24','#34d399','#a78bfa','#fb923c','#e879f9'];

new Chart(document.getElementById('channelChart'), {{
  type: 'doughnut',
  data: {{ labels: chLabels, datasets: [{{ data: chData, backgroundColor: chColors, borderWidth: 0 }}] }},
  options: {{ plugins: {{ legend: {{ position: 'right', labels: {{ color: '#94a3b8', boxWidth: 12 }} }} }}, responsive: true }}
}});
</script>
</body>
</html>"""


def main():
    print("Loading data...")
    gads, meta, ga4, hs_d, sf = load_data()

    print("Computing metrics...")
    kpis     = build_kpis(gads, meta, ga4, hs_d, sf)
    channels = channel_share(ga4)
    pipeline = pipeline_stages(hs_d, sf)
    weekly   = weekly_spend(gads, meta)

    html = render_html(kpis, channels, pipeline, weekly)

    out_path = OUT / "marketing_dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard saved: {out_path}")
    print(f"Open: file://{out_path}")


if __name__ == "__main__":
    main()
