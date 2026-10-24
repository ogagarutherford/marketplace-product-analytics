"""
Load data/raw/*.parquet into a local DuckDB warehouse (warehouse/kroma.duckdb), schema RAW.
Then print row counts and a quick funnel check.

Usage:  python scripts/load_to_duckdb.py
"""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "kroma.duckdb"
DB.parent.mkdir(exist_ok=True)

con = duckdb.connect(str(DB))
con.execute("create schema if not exists raw")
for f in sorted((ROOT / "data" / "raw").glob("raw_*.parquet")):
    table = f.stem
    con.execute(f"create or replace table raw.{table} as select *, now() as _loaded_at from read_parquet('{f.as_posix()}')")
    n = con.execute(f"select count(*) from raw.{table}").fetchone()[0]
    print(f"raw.{table:28s} {n:>9,d} rows")

print("\nFunnel check (share of sessions reaching each step):")
for row in con.execute("""
    select event_name, round(100.0 * count(distinct session_id) / (select count(*) from raw.raw_sessions), 2) as pct
    from raw.raw_events group by 1 order by pct desc""").fetchall():
    print(f"  {row[0]:15s} {row[1]:6.2f}%")
con.close()
print(f"\nWarehouse ready: {DB.relative_to(ROOT)}")
