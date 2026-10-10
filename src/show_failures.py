import json
import sys
from pathlib import Path

import pandas as pd

from db import connect, run

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_json(sys.argv[1], lines=True)

gold = {}
for p in sorted((ROOT / "eval").glob("*.jsonl")):
    for line in p.read_text().splitlines():
        if line.strip():
            q = json.loads(line)
            gold[q["id"]] = q

con = connect()
for _, r in df[df.status != "pass"].iterrows():
    q = gold[int(r["id"])]
    sql = r["sql"] if pd.notna(r["sql"]) else None
    note = r["note"] if pd.notna(r["note"]) else None
    detail = r["detail"] if pd.notna(r["detail"]) else None
    print("=" * 72)
    print(f"[{r['id']}] {r['status']}: {r['question']}")
    if sql:
        print("\nMODEL SQL:\n" + sql)
        if note:
            print("NOTE:", note)
        try:
            print(run(con, sql).head(10).to_string(index=False))
        except Exception as e:
            print("ERROR:", e)
    elif detail:
        print("\nDETAIL:", detail)
    if q["gold_sql"]:
        print("\nGOLD SQL:\n" + q["gold_sql"])
        print(run(con, q["gold_sql"]).head(10).to_string(index=False))
    else:
        print("\nExpected: refuse")
