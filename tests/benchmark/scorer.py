"""
scorer.py
─────────────────────────────────────────────────────────────────────────────
Precision + relevance scoring functions for the SQRA benchmark.

Tolerances mirror validate_metrics.py:
  dollar  ±$1.00 absolute
  pct     ±0.50% relative
  count   ±1 absolute
  exact   string equality

SQRA(case) = F1(precision, relevance) — harmonic mean, expressed 0–100.
"""

from __future__ import annotations


# ── Precision ──────────────────────────────────────────────────────────────────

def precision_score(retrieved, expected, tolerance: dict) -> float:
    """Return 0.0–1.0.  1.0 = within tolerance, decays linearly beyond it."""
    tol_type = tolerance["type"]

    if tol_type == "exact":
        return 1.0 if str(retrieved).strip() == str(expected).strip() else 0.0

    try:
        retrieved = float(retrieved)
        expected = float(expected)
    except (TypeError, ValueError):
        return 0.0

    if tol_type == "pct":
        # relative tolerance in percent
        denom = max(abs(expected), 1e-9)
        diff_pct = abs(retrieved - expected) / denom * 100
        threshold = float(tolerance["value"])
        if diff_pct <= threshold:
            return 1.0
        # linear decay: score → 0 at 2× threshold
        return max(0.0, 1.0 - (diff_pct - threshold) / threshold)

    else:  # "dollar" or "count"
        diff_abs = abs(retrieved - expected)
        threshold = float(tolerance["value"])
        if diff_abs <= threshold:
            return 1.0
        return max(0.0, 1.0 - (diff_abs - threshold) / max(threshold, 1e-9))


# ── Relevance ─────────────────────────────────────────────────────────────────

def relevance_score(case: dict, retrieval_meta: dict) -> float:
    """
    Return 0.0 or 1.0 (binary).

    retrieval_meta keys (supplied by the surface runner):
      used_date_params   bool   — MCP/SQL: were canonical dates passed?
      accessed_section   str    — golden: "windowed_90d" or "all_time"
      sql_text           str    — SQL: the query string that was executed
      is_adversarial     bool   — NL→SQL flawed fixture (always 0)
    """
    check = case.get("relevance_check", {})
    check_type = check.get("type", "always_pass")

    if check_type == "adversarial":
        return 0.0

    if check_type == "always_pass":
        return 1.0

    if check_type == "date_params_present":
        return 1.0 if retrieval_meta.get("used_date_params") else 0.0

    if check_type == "section":
        expected_section = check.get("expected")
        accessed = retrieval_meta.get("accessed_section", "")
        return 1.0 if accessed == expected_section else 0.0

    if check_type == "sql_has_date_filter":
        sql = retrieval_meta.get("sql_text", "").lower()
        # Accept any ISO date in a BETWEEN/WHERE clause — dates roll with anchor
        import re
        has_dates = bool(re.search(r"\d{4}-\d{2}-\d{2}", sql)) and (
            "between" in sql or "where" in sql
        )
        return 1.0 if has_dates else 0.0

    return 1.0  # unknown type → pass


# ── SQRA ──────────────────────────────────────────────────────────────────────

def sqra_score(precision: float, relevance: float) -> float:
    """F1 harmonic mean of precision and relevance, expressed 0–100."""
    if precision + relevance == 0:
        return 0.0
    return 100.0 * 2 * precision * relevance / (precision + relevance)


# ── Aggregation ───────────────────────────────────────────────────────────────

def aggregate(results: list[dict]) -> dict:
    """
    Aggregate per-case results into surface-level and overall SQRA.

    Adversarial cases (is_adversarial=True) are excluded from the main SQRA
    index — they test error detection, not retrieval quality. They are counted
    separately as adversarial_detected_rate.

    Each result dict must have: id, surface, precision, relevance, sqra.
    Returns:
      {
        "overall": float,               # non-adversarial cases only
        "by_surface": {...},            # non-adversarial per surface
        "case_count": int,              # total including adversarial
        "non_adversarial_count": int,
        "pass_rate": float,             # pct of non-adversarial cases with SQRA >= 90
        "adversarial_total": int,
        "adversarial_detected": int,    # correctly scored SQRA < 10
        "adversarial_detected_rate": float,
      }
    """
    canonical = [r for r in results if not r.get("adversarial")]
    adversarial = [r for r in results if r.get("adversarial")]

    surfaces: dict[str, list[float]] = {}
    for r in canonical:
        surfaces.setdefault(r["surface"], []).append(r["sqra"])

    by_surface = {s: _mean(scores) for s, scores in surfaces.items()}
    overall = _mean(list(by_surface.values())) if by_surface else 0.0
    pass_rate = sum(1 for r in canonical if r["sqra"] >= 90) / max(len(canonical), 1) * 100

    adv_detected = sum(1 for r in adversarial if r["sqra"] < 10)
    adv_rate = adv_detected / max(len(adversarial), 1) * 100

    return {
        "overall": round(overall, 1),
        "by_surface": {s: round(v, 1) for s, v in by_surface.items()},
        "case_count": len(results),
        "non_adversarial_count": len(canonical),
        "pass_rate": round(pass_rate, 1),
        "adversarial_total": len(adversarial),
        "adversarial_detected": adv_detected,
        "adversarial_detected_rate": round(adv_rate, 1),
    }


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
