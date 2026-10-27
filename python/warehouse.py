"""Read-only access to the local DuckDB warehouse built by dbt."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "kroma.duckdb"


def query(sql: str):
    with duckdb.connect(str(DB), read_only=True) as con:
        return con.sql(sql).df()
