/**
 * metrics.js — Canonical metric computation module
 * Full-Funnel AI Analytics · single source of truth
 *
 * Rules enforced (mirrors CLAUDE.md + dbt_project/models/metrics/metrics.yml):
 *  - Google ROAS: conversions × $100 AOV / cost  (NEVER spend × multiplier)
 *  - Meta ROAS:   platform roas field, pass-through
 *  - Session CVR: conversions / sessions           (cross-channel, GA4)
 *  - Click CVR:   conversions / clicks             (platform campaigns only)
 *  - Attribution: always normalised to 100% before render
 *  - Funnel:      each step must be ≤ the step above it
 *  - Freshness:   every dashboard must show the query window and generation date
 *
 * Usage in HTML:
 *   <script src="js/metrics.js"></script>
 *   // then use Metrics.googleROAS(), Metrics.normaliseAttribution(), etc.
 *
 * Usage in Node (testing):
 *   const Metrics = require('./dashboards/js/metrics.js');
 */

const Metrics = (() => {
  // $100 avg order value — derived from Meta platform data (avg revenue/conversion).
  // Used for all Google ROAS estimates. Never change without updating CLAUDE.md.
  const AOV = 100;

  /* ── Computation ──────────────────────────────────────────────────────────── */

  /**
   * Google ROAS (estimated): conversions × AOV / cost
   * Use this for ALL Google Ads ROAS calculations.
   * Never use spend × multiplier.
   * @param {number} conversions
   * @param {number} cost  — Google Ads "cost" field (USD)
   * @returns {number}  ROAS rounded to 2 dp
   */
  function googleROAS(conversions, cost) {
    if (!cost || cost === 0) return 0;
    return parseFloat(((conversions * AOV) / cost).toFixed(2));
  }

  /**
   * Meta ROAS: pass-through of the platform-reported roas field.
   * Attribution: 7-day click / 1-day view (Meta native last-click).
   * @param {number} platformRoas  — Meta MCP response "roas" field
   * @returns {number}  ROAS rounded to 2 dp
   */
  function metaROAS(platformRoas) {
    return parseFloat(Number(platformRoas).toFixed(2));
  }

  /**
   * Session CVR — canonical cross-channel conversion rate (GA4).
   * Formula: conversions / sessions.
   * Use this for funnel analysis, not platform campaign tables.
   * @param {number} conversions
   * @param {number} sessions  — GA4 sessions
   * @returns {number}  CVR as a percentage (e.g. 2.52 means 2.52%)
   */
  function sessionCVR(conversions, sessions) {
    if (!sessions || sessions === 0) return 0;
    return parseFloat(((conversions / sessions) * 100).toFixed(2));
  }

  /**
   * Click CVR — platform campaign conversion rate.
   * Formula: conversions / clicks.
   * Use this for Google Ads / Meta Ads campaign tables only.
   * Do NOT use for cross-channel comparisons (use sessionCVR instead).
   * @param {number} conversions
   * @param {number} clicks  — paid ad clicks
   * @returns {number}  CVR as a percentage (e.g. 3.72 means 3.72%)
   */
  function clickCVR(conversions, clicks) {
    if (!clicks || clicks === 0) return 0;
    return parseFloat(((conversions / clicks) * 100).toFixed(2));
  }

  /**
   * Normalise attribution channels so shares always sum to exactly 100%.
   * MUST be called before rendering any pie, donut, or attribution bar chart.
   * @param {Array<{label: string, val: number, color: string}>} channels
   *   val can be any raw share value (absolute spend, percentage points, etc.)
   * @returns {Array<{label: string, val: number, color: string}>}
   *   same shape, val replaced with normalised percentage (sum = 100)
   */
  function normaliseAttribution(channels) {
    const total = channels.reduce((s, d) => s + d.val, 0);
    if (total === 0) return channels;
    return channels.map(d => ({
      ...d,
      val: parseFloat(((d.val / total) * 100).toFixed(1)),
    }));
  }

  /**
   * Validate funnel step ordering.
   * Each step must be ≤ the step above it. CRM Contacts must NOT appear
   * between GA4 Conversions and Deals Won.
   * @param {Array<{label: string, val: number}>} steps  ordered top → bottom
   * @returns {string[]}  array of error messages; empty = valid
   */
  function validateFunnel(steps) {
    const issues = [];
    for (let i = 1; i < steps.length; i++) {
      if (steps[i].val > steps[i - 1].val) {
        issues.push(
          `Funnel integrity error: "${steps[i].label}" (${steps[i].val.toLocaleString()}) ` +
          `> "${steps[i - 1].label}" (${steps[i - 1].val.toLocaleString()})`
        );
      }
    }
    return issues;
  }

  /* ── Formatters ───────────────────────────────────────────────────────────── */

  /** Format a dollar value. $1.2M / $345.6K / $99 */
  function fmt$(value, decimals = 0) {
    if (value >= 1e6) return '$' + (value / 1e6).toFixed(1) + 'M';
    if (value >= 1e3) return '$' + (value / 1e3).toFixed(1) + 'K';
    return '$' + value.toFixed(decimals);
  }

  /** Format a percentage value. Default 1 dp. */
  function fmtPct(value, decimals = 1) {
    return value.toFixed(decimals) + '%';
  }

  /** Format a ROAS value. e.g. "3.46×" */
  function fmtROAS(value) {
    return value.toFixed(2) + '×';
  }

  /* ── Canonical KPI subtitle strings ──────────────────────────────────────── */
  // Use these in ROAS / CVR KPI card subtitles so every dashboard shows
  // the same attribution window and basis labels.

  const labels = {
    blendedROAS:  'Linear attribution · 90-day window',
    channelROAS:  'Linear attribution · 90-day window',
    metaROAS:     'Meta platform · 7d click / 1d view',
    googleROAS:   'Google est. · AOV $100 · 30-day',
    sessionCVR:   'Session CVR: conversions ÷ sessions',
    clickCVR:     'Click CVR: conversions ÷ clicks',
    attributed:   'Attributed Revenue (90d) · linear',
    sfClosedWon:  'Salesforce Closed Won · 90-day',
    crmAllTime:   'CRM all-time (HubSpot + Salesforce)',
  };

  /* ── Data Freshness Badge (CLAUDE.md §6) ─────────────────────────────────── */

  /**
   * Build the canonical data freshness string required by CLAUDE.md §6.
   * Format: "[Start date] – [End date] · Data as of [generatedAt]"
   *
   * Example output: "Dec 16, 2025 – Mar 15, 2026 · Data as of Mar 15, 2026"
   *
   * @param {string} windowStart   ISO date "YYYY-MM-DD" — period start (inclusive)
   * @param {string} windowEnd     ISO date "YYYY-MM-DD" — period end (inclusive)
   * @param {string} [generatedAt] ISO timestamp from golden_metrics._meta.generated_at.
   *                               When omitted, falls back to today's date in the browser.
   *                               Always pass this value when available so the badge
   *                               reflects the snapshot date, not the render date.
   * @returns {string}
   */
  function freshnessLabel(windowStart, windowEnd, generatedAt) {
    // Parse YYYY-MM-DD as local calendar date.
    // Using (y, m-1, d) constructor avoids the UTC midnight off-by-one shift
    // that would occur with new Date("2025-12-16") on machines west of UTC.
    const fmtDate = (iso) => {
      const [y, m, d] = iso.slice(0, 10).split('-').map(Number);
      return new Date(y, m - 1, d).toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric',
      });
    };

    // Use the golden-layer generation timestamp when available.
    // Fall back to today's local date when called outside a golden-layer context.
    const asOf = generatedAt
      ? fmtDate(generatedAt)
      : new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

    return `${fmtDate(windowStart)} – ${fmtDate(windowEnd)} · Data as of ${asOf}`;
  }

  /**
   * Inject the canonical freshness label into a DOM element.
   *
   * Usage — call this once after loading golden_metrics.json:
   *   const meta = goldenMetrics._meta;
   *   Metrics.renderFreshnessBadge(
   *     '#freshness-badge',
   *     meta.window_start,    // "2025-12-16"
   *     meta.window_end,      // "2026-03-15"
   *     meta.generated_at     // "2026-03-15T00:00:00+00:00"
   *   );
   *
   * The element with id="freshness-badge" should already exist in the HTML, e.g.:
   *   <span id="freshness-badge" class="freshness-badge">Loading…</span>
   *
   * @param {string} selector    CSS selector for the target element
   * @param {string} windowStart ISO date string for the period start
   * @param {string} windowEnd   ISO date string for the period end
   * @param {string} [generatedAt] ISO timestamp from golden_metrics._meta.generated_at
   */
  function renderFreshnessBadge(selector, windowStart, windowEnd, generatedAt) {
    const el = document.querySelector(selector);
    // Silently skip if the element is absent — not every dashboard has a badge element.
    if (!el) return;
    el.textContent = freshnessLabel(windowStart, windowEnd, generatedAt);
  }

  /* ── Public API ───────────────────────────────────────────────────────────── */

  return {
    AOV,
    googleROAS,
    metaROAS,
    sessionCVR,
    clickCVR,
    normaliseAttribution,
    validateFunnel,
    fmt$,
    fmtPct,
    fmtROAS,
    labels,
    freshnessLabel,
    renderFreshnessBadge,
  };
})();

// CommonJS export so this file can be required in Node for unit testing
// (no-op in browser — `module` is undefined)
if (typeof module !== 'undefined') module.exports = Metrics;
