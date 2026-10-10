import json
from pathlib import Path

from db import connect, run

ROOT = Path(__file__).resolve().parent.parent

con = connect()
for path in sorted((ROOT / "eval").glob("*.jsonl")):
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        q = json.loads(line)
        print(f"\n[{q['id']}] ({q['category']}) {q['question']}")
        if q["gold_sql"] is None:
            print(f"   expected behaviour: {q.get('expected')}")
            continue
        print(run(con, q["gold_sql"]).to_string(index=False))