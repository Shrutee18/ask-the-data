#!/bin/bash
# usage: ./run_and_save.sh v3 2
p=$1; n=$2
dest=results/${p}_run${n}.jsonl
if [ -e "$dest" ]; then echo "$dest already exists, refusing to overwrite"; exit 1; fi
PAUSE=${PAUSE:-5} python -u src/run_eval.py --prompt $p 2>&1 | tee logs_${p}_run${n}.txt
if grep -q "api_error" logs_${p}_run${n}.txt; then
  echo "Run had api_error rows: NOT saved. Wait for the rate limit to reset and rerun."
  exit 1
fi
cp results/openai_gpt-oss-20b__${p}__dev.jsonl "$dest"
echo "Saved $dest"
