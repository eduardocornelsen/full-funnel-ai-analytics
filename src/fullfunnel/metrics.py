"""Canonical Python metric formulas — the ONLY place these live in Python.

Mirrors CLAUDE.md §1 and dbt_project/models/metrics/metrics.yml (the semantic
layer is the ultimate source of truth; generate_golden_metrics.py cross-checks
against MetricFlow at every generation). dashboards/js/metrics.js is the
JavaScript twin for browser dashboards — change formulas in metrics.yml first,
then here, then there, in the same PR.

Never redefine GOOGLE_AOV or these formulas in another module. The 2026-07
review found this file's contents copy-pasted across four scripts, two of
which had silently diverged (a stale Meta ROAS formula in each).
"""

# AOV for Google ROAS estimates (CLAUDE.md §8). Calibrated from Meta's
# platform-reported revenue — which is exactly why Meta ROAS must NEVER be
# derived from this constant (circular). Meta uses purchase_value/spend.
GOOGLE_AOV = 100.0


def google_roas(conversions: float, cost: float) -> float:
    """Google Ads estimated ROAS: conversions × $AOV / cost (Google reports no revenue)."""
    return round((conversions * GOOGLE_AOV) / cost, 2) if cost else 0.0


def meta_roas(purchase_value: float, spend: float) -> float:
    """Meta platform ROAS: platform-reported revenue / spend (ratio of sums)."""
    return round(purchase_value / spend, 2) if spend else 0.0


def session_cvr(conversions: float, sessions: float) -> float:
    """Canonical Session CVR %: GA4 conversions / GA4 sessions × 100."""
    return round(conversions / sessions * 100, 2) if sessions else 0.0


def click_cvr(conversions: float, clicks: float) -> float:
    """Click CVR %: platform conversions / clicks × 100. NOT comparable to session CVR."""
    return round(conversions / clicks * 100, 2) if clicks else 0.0


def blended_roas(attributed_revenue: float, spend: float) -> float:
    """Blended ROAS: linear-attributed revenue / total paid spend."""
    return round(attributed_revenue / spend, 2) if spend else 0.0
