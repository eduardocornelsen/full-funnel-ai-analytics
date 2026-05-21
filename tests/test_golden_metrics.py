"""
Tests for golden_metrics.json structural integrity and metric sanity.
These run in CI without a warehouse connection.
"""

import pytest


# ── Structure ──────────────────────────────────────────────────────────────────

def test_top_level_keys(golden):
    assert "_meta" in golden
    assert "windowed_90d" in golden
    assert "all_time" in golden


def test_meta_required_fields(golden):
    meta = golden["_meta"]
    for field in ["generated_at", "anchor_date", "window_start", "window_end",
                  "schema_version", "google_aov"]:
        assert field in meta, f"_meta missing field: {field}"


def test_section_keys(golden_90d, golden_at):
    for section in (golden_90d, golden_at):
        for key in ["spend", "sessions", "conversions", "blended_roas",
                    "channel_performance", "attribution_by_channel", "ga4_by_channel",
                    "campaigns", "crm"]:
            assert key in section, f"Section missing key: {key}"


# ── Spend ──────────────────────────────────────────────────────────────────────

def test_spend_positive(golden_90d):
    spend = golden_90d["spend"]
    assert spend["google"] > 0
    assert spend["meta"] > 0
    assert spend["total"] > 0


def test_spend_total_equals_sum(golden_90d):
    spend = golden_90d["spend"]
    assert abs(spend["total"] - (spend["google"] + spend["meta"])) < 1.0


# ── Sessions & conversions ─────────────────────────────────────────────────────

def test_sessions_positive(golden_90d):
    assert golden_90d["sessions"]["total"] > 0
    assert golden_90d["sessions"]["engaged"] > 0


def test_funnel_ordering(golden_90d):
    total_sess = golden_90d["sessions"]["total"]
    engaged    = golden_90d["sessions"]["engaged"]
    conv       = golden_90d["conversions"]["ga4_total"]
    assert total_sess >= engaged, "engaged_sessions should be <= total_sessions"
    assert total_sess >= conv,    "conversions should be <= sessions"


def test_session_cvr_plausible(golden_90d):
    cvr = golden_90d["conversions"]["session_cvr_pct"]
    assert 0 < cvr < 30, f"session CVR {cvr}% looks implausible"


# ── ROAS ───────────────────────────────────────────────────────────────────────

def test_blended_roas_plausible(golden_90d):
    roas = golden_90d["blended_roas"]
    assert 0.5 < roas < 100, f"blended ROAS {roas}x looks implausible"


def test_channel_roas_positive(golden_90d):
    for ch in golden_90d["channel_performance"]:
        assert ch["roas"] >= 0, f"channel {ch['channel']} has negative ROAS"


# ── Attribution ────────────────────────────────────────────────────────────────

def test_attribution_has_channels(golden_90d):
    assert len(golden_90d["attribution_by_channel"]) > 0


def test_attribution_linear_revenue_positive(golden_90d):
    for ch in golden_90d["attribution_by_channel"]:
        assert ch["linear_revenue"] >= 0, f"negative linear_revenue for {ch['channel']}"


def test_attribution_percentages_sum_to_100(golden_90d):
    channels = golden_90d["attribution_by_channel"]
    total = sum(ch["linear_revenue"] for ch in channels)
    if total == 0:
        pytest.skip("No attribution revenue to normalise")
    pct_sum = sum((ch["linear_revenue"] / total) * 100 for ch in channels)
    assert abs(pct_sum - 100.0) < 0.5, f"Attribution percentages sum to {pct_sum:.2f}%, expected 100%"


# ── GA4 channels ───────────────────────────────────────────────────────────────

def test_ga4_channels_present(golden_90d):
    assert len(golden_90d["ga4_by_channel"]) > 0


def test_ga4_no_negative_sessions(golden_90d):
    for ch in golden_90d["ga4_by_channel"]:
        assert ch["sessions"] >= 0
        assert ch["engaged_sessions"] >= 0
        assert ch["conversions"] >= 0


def test_ga4_engaged_le_sessions(golden_90d):
    for ch in golden_90d["ga4_by_channel"]:
        assert ch["engaged_sessions"] <= ch["sessions"], (
            f"engaged > sessions for channel {ch['channel']}"
        )


# ── Campaigns ─────────────────────────────────────────────────────────────────

def test_google_campaigns_present(golden_90d):
    assert len(golden_90d["campaigns"]["google"]) > 0


def test_meta_campaigns_present(golden_90d):
    assert len(golden_90d["campaigns"]["meta"]) > 0


def test_campaign_roas_non_negative(golden_90d):
    for c in golden_90d["campaigns"]["google"] + golden_90d["campaigns"]["meta"]:
        assert c["roas"] >= 0, f"negative ROAS on campaign {c.get('campaign_name')}"


# ── CRM ───────────────────────────────────────────────────────────────────────

def test_crm_hubspot_contacts_positive(golden_at):
    assert golden_at["crm"]["hubspot"]["total_contacts"] > 0


def test_crm_salesforce_closed_won_positive(golden_at):
    assert golden_at["crm"]["salesforce"]["closed_won_revenue"] > 0


def test_crm_pipeline_stages_present(golden_at):
    assert len(golden_at["crm"]["hubspot"]["pipeline_by_stage"]) > 0
    assert len(golden_at["crm"]["salesforce"]["pipeline_by_stage"]) > 0
