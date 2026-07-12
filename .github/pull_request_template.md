## What & why

<!-- One paragraph: the change and the reason. Link the issue if one exists. -->

## Checklist

- [ ] `ruff check .` passes
- [ ] `python -m pytest tests/ -q` passes
- [ ] `fullfunnel validate` exits 0 (drift + staleness gates)
- [ ] `CHANGELOG.md` updated under **Unreleased**
- [ ] No new duplicate metric definitions; no literal-date defaults
- [ ] If metric values changed: regenerated `dashboards/golden_metrics.json`
      is included and the value change is explained below

## Metric impact

<!-- "None" or a before/after of affected metrics -->
