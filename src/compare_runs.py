import glob
import re
from collections import defaultdict

import pandas as pd

fails = defaultdict(lambda: defaultdict(int))
valid = defaultdict(list)
invalid = defaultdict(int)

for f in sorted(glob.glob("results/v[0-9]_run[0-9].jsonl")):
    prompt = re.search(r"results/(v\d)_run", f).group(1)
    df = pd.read_json(f, lines=True)
    n_api = int((df.status == "api_error").sum())
    if n_api > 0:
        invalid[prompt] += 1
        print(f"{f}: INVALID ({n_api} api_error rows), skipped")
        continue
    valid[prompt].append((int((df.status == "pass").sum()), len(df)))
    for _, r in df[df.status != "pass"].iterrows():
        fails[prompt][(int(r["id"]), r["status"])] += 1

for prompt in sorted(valid):
    s = valid[prompt]
    mean = sum(p for p, _ in s) / len(s)
    print(f"\n{prompt}: valid runs = {[f'{p}/{n}' for p, n in s]}  mean = {mean:.1f} of {s[0][1]}  ({invalid[prompt]} invalid skipped)")
    for (qid, status), count in sorted(fails[prompt].items()):
        print(f"   Q{qid:<3} {status:<24} failed in {count} of {len(s)} valid runs")
