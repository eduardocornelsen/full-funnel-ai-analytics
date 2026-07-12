"""Connector registry — real and mock data sources behind one protocol."""

from . import csv_mock, ga4  # noqa: F401  (imports register the connectors)
from .base import Connector, ConnectorConfigError, available, get_connector

__all__ = ["Connector", "ConnectorConfigError", "available", "get_connector"]
