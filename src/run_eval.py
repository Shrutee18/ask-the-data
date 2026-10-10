import argparse
import os
import json
import re
import time
from pathlib import Path

import pandas as pd

from db import connect, run
from llm import DEFAULT_MODEL, ask, parse
from prompts import PROMPTS
from score import results_match

ROOT = Path(__file__).resolve().parent.parent
HELD_OUT = {2, 8, 15, 19, 21, 23, 26, 29, 31, 33, 36, 38}


def load_questions():
    qs = []
    for p in sorted((ROOT / "eval").glob("*.jsonl")):
        for line in p.read_text().splitlines():
            if line.strip():
                qs.append(json.loads(line))
    return sorted(qs, key=lambda q: q["id"])


def evaluate(con, q, obj):
    should_refuse = q["gold_sql"] is None
    if obj["action"] == "refuse":
        return ("pass", None) if should_refuse else ("wrongly_refused", obj.get("reason"))
    if should_refuse:
        try:
            run(con, obj["sql"])
            return ("should_have_refused", None)
        except Exception as e:
            return ("should_have_refused_but_blocked", str(e))
    try:
        pred = run(con, obj["sql"])
    except Exception as e:
        return ("sql_error", str(e))
    for g in [q["gold_sql"]] + q.get("alt_gold_sql", []):
        if results_match(run(con, g), pred):
            return ("pass", None)
    return ("wrong_result", None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=DEFAULT_MODEL, help="Groq model ID (default: GROQ_MODEL in .env)")
    ap.add_argument("--prompt", choices=PROMPTS.keys(), default="v2")
    ap.add_argument("--split", choices=["dev", "heldout", "all"], default="dev")
    ap.add_argument("--limit", type=int, default=None, help="only run the first N questions")
    args = ap.parse_args()

    questions = load_questions()
    if args.split == "dev":
        questions = [q for q in questions if q["id"] not in HELD_OUT]
    elif args.split == "heldout":
        if input("Held-out set: run this once, at the very end. Type YES to continue: ") != "YES":
            return
        questions = [q for q in questions if q["id"] in HELD_OUT]
    if args.limit:
        questions = questions[: args.limit]

    con = connect()
    rows = []
    for q in questions:
        raw, tin, tout, sql, note = "", 0, 0, None, None
        t0 = time.time()
        try:
            raw, tin, tout = ask(args.model, PROMPTS[args.prompt], q["question"])
            obj = parse(raw)
            sql, note = obj.get("sql"), obj.get("note")
            status, detail = evaluate(con, q, obj)
        except (json.JSONDecodeError, ValueError) as e:
            status, detail = "parse_error", str(e)
        except Exception as e:
            status, detail = "api_error", str(e)
        secs = time.time() - t0
        rows.append({"id": q["id"], "category": q["category"], "question": q["question"],
                     "status": status, "detail": detail, "sql": sql, "note": note,
                     "latency_s": round(secs, 1), "input_tokens": tin, "output_tokens": tout,
                     "raw": raw})
        print(f"[{q['id']:>2}] {status:<32} {secs:5.1f}s  {q['question'][:60]}")
        time.sleep(float(os.environ.get("PAUSE", "0")))

    df = pd.DataFrame(rows)
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    safe_model = re.sub(r"[^A-Za-z0-9._-]+", "_", str(args.model))
    out = out_dir / f"{safe_model}__{args.prompt}__{args.split}.jsonl"
    df.to_json(out, orient="records", lines=True)

    df["pass"] = df.status == "pass"
    print(f"\nModel {args.model}, prompt {args.prompt}, split {args.split}")
    print(f"Overall: {df['pass'].sum()} of {len(df)} ({100 * df['pass'].mean():.0f}%)")
    print(f"Average time per question: {df.latency_s.mean():.1f}s")
    print(df.groupby("category")["pass"].agg(["sum", "count"]).rename(columns={"sum": "passed", "count": "total"}))
    print("\nFailure types:")
    print(df[~df["pass"]]["status"].value_counts())
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()