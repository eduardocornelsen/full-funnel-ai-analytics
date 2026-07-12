---
name: Bug report
about: Something broken — wrong metric, failed pipeline step, install problem
labels: bug
---

**What happened?**

**What did you expect?**

**Steps to reproduce**

```bash
# commands you ran
```

**Environment**
- OS / Python version:
- Install method: `pip install -e .` / manual requirements.txt
- Data path: standalone synthetic / Olist-anchored / own data

**If a metric value is wrong:** paste the relevant section of
`dashboards/golden_metrics.json` (`_meta` + the metric) and the output of
`fullfunnel validate`.
