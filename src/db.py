import re
from pathlib import Path

import duckdb
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
MAX_ROWS = 1000

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|copy|attach|detach|pragma|"
    r"install|load|export|import|call|set|read_csv|read_parquet|read_json|glob)\b",
    re.I,
)


def connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    con.execute(f"CREATE TABLE gm_sales AS SELECT * FROM read_parquet('{DATA / 'gm_sales.parquet'}')")
    con.execute(f"CREATE TABLE cpi_annual AS SELECT * FROM read_parquet('{DATA / 'cpi_annual.parquet'}')")
    con.execute("SET enable_external_access=false")
    return con


def validate(sql: str) -> str:
    s = sql.strip().rstrip(";").strip()
    if ";" in s:
        raise ValueError("Only one statement is allowed")
    if not re.match(r"^(select|with)\b", s, re.I):
        raise ValueError("Only SELECT queries are allowed")
    hit = FORBIDDEN.search(s)
    if hit:
        raise ValueError(f"Keyword not allowed: {hit.group(0)}")
    return s


def run(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    cur = con.execute(validate(sql))
    cols = [d[0] for d in cur.description]
    return pd.DataFrame(cur.fetchmany(MAX_ROWS), columns=cols)