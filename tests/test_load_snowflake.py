"""load_snowflake.py against fakesnow (an in-process Snowflake emulator on DuckDB).

No real account is needed: fakesnow patches snowflake.connector.connect, so the
loader's real code path (connect -> CREATE SCHEMA -> write_pandas) runs end to end.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

fakesnow = pytest.importorskip("fakesnow")
pytest.importorskip("snowflake.connector")

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import load_snowflake  # noqa: E402

SF_ENV = {
    "SNOWFLAKE_ACCOUNT": "fake",
    "SNOWFLAKE_USER": "fake",
    "SNOWFLAKE_PASSWORD": "fake",
    "SNOWFLAKE_WAREHOUSE": "ANALYTICS_WH",
    "SNOWFLAKE_DATABASE": "OLIST_ANALYTICS",
    "SNOWFLAKE_RAW_SCHEMA": "RAW",
}


@pytest.fixture
def sample_data(tmp_path: Path) -> Path:
    """A tiny copy of the data/ layout: two olist files and one marketing file."""
    olist = tmp_path / "olist"
    mkt = tmp_path / "mock_marketing"
    olist.mkdir()
    mkt.mkdir()
    (olist / "olist_orders_dataset.csv").write_text(
        "order_id,customer_id,order_status,order_purchase_timestamp\n"
        "o1,c1,delivered,2025-01-02 10:00:00\n"
        "o2,c2,shipped,2025-01-03 11:00:00\n"
        "o3,c1,delivered,2025-01-04 12:00:00\n"
    )
    (olist / "product_category_name_translation.csv").write_text(
        "product_category_name,product_category_name_english\nbeleza_saude,health_beauty\n"
    )
    (mkt / "google_ads_daily_performance.csv").write_text(
        "date,campaign_id,impressions,clicks,cost,conversions\n"
        "2025-01-02,g1,1000,50,25.5,3\n"
        "2025-01-03,g1,1200,60,30.0,4\n"
    )
    return tmp_path


@pytest.fixture
def sf_env(monkeypatch):
    for k, v in SF_ENV.items():
        monkeypatch.setenv(k, v)


def test_table_names_match_duckdb_loader():
    assert load_snowflake.table_name_for(Path("data/olist/olist_orders_dataset.csv")) == "orders"
    assert (
        load_snowflake.table_name_for(Path("data/olist/product_category_name_translation.csv"))
        == "product_category_name_translation"
    )
    # Marketing stems stay as they are, even if they contain "_dataset"-like text.
    assert (
        load_snowflake.table_name_for(Path("data/mock_marketing/ga4_daily_sessions.csv"))
        == "ga4_daily_sessions"
    )


def test_discover_covers_every_committed_csv():
    found = {t for _, t in load_snowflake.discover_csvs()}
    data = load_snowflake.DATA_DIR
    expected = len(list((data / "olist").glob("*.csv"))) + len(
        list((data / "mock_marketing").glob("*.csv"))
    )
    assert len(found) == expected
    assert {"orders", "order_items", "google_ads_daily_performance", "hubspot_deals"} <= found


def test_dry_run_needs_no_credentials(monkeypatch, capsys):
    for k in SF_ENV:
        monkeypatch.delenv(k, raising=False)
    assert load_snowflake.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "RAW.ORDERS" in out


def test_missing_credentials_fail_loudly(monkeypatch):
    for k in SF_ENV:
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(SystemExit, match="SNOWFLAKE_ACCOUNT"):
        load_snowflake.connect()


def test_load_writes_tables_and_is_idempotent(sample_data, sf_env, monkeypatch, capsys):
    monkeypatch.setattr(load_snowflake, "DATA_DIR", sample_data)
    with fakesnow.patch():
        # Run twice: overwrite must leave exactly the CSV rows, not double them.
        assert load_snowflake.main([]) == 0
        assert load_snowflake.main([]) == 0

        con = load_snowflake.connect()
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM RAW.ORDERS")
        assert cur.fetchone()[0] == 3
        cur.execute("SELECT COUNT(*) FROM RAW.GOOGLE_ADS_DAILY_PERFORMANCE")
        assert cur.fetchone()[0] == 2
        # Unquoted lower-case SQL, as dbt writes it, resolves the upper-case columns.
        cur.execute("select sum(clicks) from raw.google_ads_daily_performance")
        assert cur.fetchone()[0] == 110
        cur.execute("select product_category_name_english from raw.product_category_name_translation")
        assert cur.fetchone()[0] == "health_beauty"
        con.close()

    out = capsys.readouterr().out
    assert "orders: 3 rows" in out


def test_failure_names_the_table(sample_data, sf_env, monkeypatch, capsys):
    monkeypatch.setattr(load_snowflake, "DATA_DIR", sample_data)

    def boom(con, csv_file, table, schema):
        raise RuntimeError("simulated")

    monkeypatch.setattr(load_snowflake, "load_table", boom)
    with fakesnow.patch():
        assert load_snowflake.main([]) == 1
    assert "orders: simulated" in capsys.readouterr().out
