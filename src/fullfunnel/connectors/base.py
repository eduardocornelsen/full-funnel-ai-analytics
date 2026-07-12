"""The Connector protocol — the seam where real platform data enters.

A connector's one job: produce a DataFrame in the EXACT staging schema of its
target table for a date range. Everything downstream (load_duckdb → dbt →
golden metrics → governed serving) is connector-agnostic; swapping mock for
real data is a registry lookup, not a refactor.

Field-mapping knowledge lives HERE as declared schema, not in prose. (CLAUDE.md
§7's "Google spend is `cost`, Meta spend is `spend`" is the kind of fact a
connector encodes in its `schema` and mapping code.)

Contract rules:
- `extract(start, end)` returns rows for [start, end] inclusive, matching
  `schema` exactly (names AND order — CSV appends are positional).
- Connectors never write files or touch the warehouse; ingestion mechanics
  (merging into the CSV layer, rebuilding) belong to the CLI.
- Raise ConnectorConfigError with actionable guidance when configuration is
  missing — never return an empty frame for a config problem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class ConnectorConfigError(RuntimeError):
    """Missing/invalid connector configuration (credentials, ids)."""


class Connector(ABC):
    #: registry key, e.g. "ga4"
    name: str
    #: staging table / CSV basename this connector feeds, e.g. "ga4_daily_sessions"
    target_table: str
    #: exact output columns, in order
    schema: list[str]
    #: the date column used for range merging
    date_column: str = "date"

    @abstractmethod
    def extract(self, start: date, end: date) -> pd.DataFrame:
        """Return rows for [start, end] inclusive in `schema` order."""

    def validate_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enforce the schema contract on an extracted frame."""
        missing = [c for c in self.schema if c not in df.columns]
        if missing:
            raise ValueError(f"{self.name}: extracted frame missing columns {missing}")
        return df[self.schema]


_REGISTRY: dict[str, type[Connector]] = {}


def register(cls: type[Connector]) -> type[Connector]:
    _REGISTRY[cls.name] = cls
    return cls


def get_connector(name: str) -> Connector:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown connector '{name}'. Available: {sorted(_REGISTRY)}")
    return _REGISTRY[name]()


def available() -> list[str]:
    return sorted(_REGISTRY)
