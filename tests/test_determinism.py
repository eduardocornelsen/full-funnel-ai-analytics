"""Determinism guard for the regenerate-don't-commit data model.

The repo commits only a frozen baseline of CSVs; every machine (CI, fresh
clones, the owner's laptop, the daily refresh) regenerates the appended days
locally via date-seeded generators. That model is safe only while generation
is byte-stable — across runs AND across numpy/pandas upgrades.

- test_generators_are_repeatable catches seeding bugs (same date must always
  produce identical rows in one environment).
- test_generators_match_pinned_hashes catches environment drift: if a numpy
  upgrade changes the random stream, this fails loudly BEFORE clones start
  regenerating different data than golden_metrics.json was computed from.
  If it fails after a deliberate generator change, regenerate the hashes:
      python -c "import tests.test_determinism as t; t.print_current_hashes()"
  and update PINNED_HASHES in the same PR that changes the generator.
"""

import hashlib
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import daily_synthetic_append as gen  # noqa: E402

REFERENCE_DATE = date(2026, 7, 1)

GENERATORS = {
    "google":      gen._google_day,
    "meta":        gen._meta_day,
    "ga4":         gen._ga4_day,
    "attribution": gen._attribution_day,
    "hs_deals":    gen._hubspot_deals_day,
    "hs_contacts": gen._hubspot_contacts_day,
    "salesforce":  gen._salesforce_day,
}

# sha256[:16] of each generator's output for REFERENCE_DATE.
PINNED_HASHES = {
    "google":      "0331cddc08cd80c0",
    "meta":        "b061399758a77ef2",
    "ga4":         "3bc40181d1e7ad77",
    "attribution": "bf364213279e0a30",
    "hs_deals":    "8d958c7ca6b3d897",
    "hs_contacts": "ad23b82065448e26",
    "salesforce":  "dc1aef190710ba75",
}


def _digest(rows: list[dict]) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()[:16]


def test_generators_are_repeatable():
    for name, fn in GENERATORS.items():
        assert fn(REFERENCE_DATE) == fn(REFERENCE_DATE), f"{name} is not repeatable for a fixed date"


def test_generators_match_pinned_hashes():
    for name, fn in GENERATORS.items():
        got = _digest(fn(REFERENCE_DATE))
        assert got == PINNED_HASHES[name], (
            f"{name} generated different data for {REFERENCE_DATE}: {got} != {PINNED_HASHES[name]}. "
            "Either a generator changed (update PINNED_HASHES in the same PR) or a "
            "numpy/pandas upgrade broke stream stability (pin the dependency — clones "
            "would regenerate data that diverges from golden_metrics.json)."
        )


def test_different_dates_differ():
    # Guards against a seeding bug that ignores the date entirely.
    assert gen._google_day(date(2026, 7, 1)) != gen._google_day(date(2026, 7, 2))


def print_current_hashes() -> None:
    for name, fn in GENERATORS.items():
        print(f'    "{name}": "{_digest(fn(REFERENCE_DATE))}",')
