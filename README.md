# Ask the Data: plain-English questions over UK house sale data

A text-to-SQL tool and its evaluation. You ask a question in plain English about 300,000 Greater Manchester
house sales (2018 to 2025). A language model writes a read-only SQL query, the query runs in DuckDB, and the
app shows both the SQL and the result. Questions the data cannot answer are refused.

**Live demo:** https://ask-the-data.streamlit.app

The more interesting part is the evaluation: a 42-question test set with known answers, four prompt versions,
repeated runs, a held-out set and a written failure analysis.

## Results

Model: `openai/gpt-oss-20b` on the Groq free tier, temperature 0, October 2026.
Development set: 30 questions. Held-out set: 12 questions, run once.

| Prompt | What it adds | Development score |
|---|---|---|
| V1 | Table schema only | 13 of 30 (43%), one run |
| V2 | Exact column values and interpretation rules | 28, 27 and 29 of 30 (mean 28.0) |
| V3 | V2 plus "a place name means the district column" | 30, 29 and 29 of 30 (mean 29.3) |

**Held-out result for V3: 10 of 12 (83%).** With only 12 questions the plausible range is wide (roughly 55%
to 95%). Both misses were answers a person would accept (see the failure analysis).

What the results show:
- The prompt mattered most. Giving the model the exact column values and rules took it from 43% to about 93%.
- V3's rule fixed a real ambiguity (Q4: "Manchester" as the postal town versus the council district). V3's
  average is 1.3 questions above V2's from three runs each, so that improvement is small and the evidence is modest.
- Refusals work with the full prompt: rent, bedrooms, forecasts, other areas, other years and "delete all sales"
  were all declined. With the bare V1 prompt, the model wrote a destructive query for the delete request. The
  read-only filter blocked it, so nothing ran.

## Failure analysis

| Question | What happened | Cause |
|---|---|---|
| Q4, flats in Manchester | Filtered on postal town instead of district | Ambiguous wording; fixed by V3's rule |
| Q10, Q28, Q30 (inflation) | SQL joined the CPI table in a way DuckDB rejects, or applied inflation when it was not asked for | Model error, intermittent, not fixed by any prompt version I ran |
| Q25 under a discarded V3 variant | Adjusted every sale for inflation when asked for a plain median | Adding a rule to the prompt caused a new mistake |
| Held-out Q26 | Returned both medians instead of naming the higher one | Valid answer in a different shape from the key |
| Held-out Q29 | Returned 0.051 where the key expected 5.09 | "Share" is ambiguous (proportion or percent) |

## How the evaluation works

- `eval/` holds 42 questions with gold SQL: simple lookups, filters, rankings, trends, comparisons,
  calculations, inflation joins, two ambiguous questions and six that should be refused.
- A prediction passes if its result matches the gold result: row order ignored, extra columns allowed, numbers
  within 0.5%. On questions that should be refused, only a refusal passes.
- 12 questions were set aside before any model run and used once at the end.

## Corrections to the evaluation

The answer key and scorer were corrected after the first runs, and every change is logged in
`CHANGES_TO_EVAL.md`. Gold queries for "which one" questions now return only the name, one question was
reworded, and one question accepts a second answer shape. Scores before those fixes were V1 12 of 30 and V2
26 of 30.

The held-out score was not changed after the run. I judged the two misses acceptable only after seeing them, so
the headline stays 10 of 12 (it would be 12 of 12 if both were accepted).

## Safety design

- The model never touches the database directly. Its SQL passes a validator (one SELECT or WITH statement, with
  no write, file or system keywords) and runs on an in-memory copy with external file access switched off.
- This is a second line of defence, not a guarantee. The real protection is that the data is public and
  non-sensitive, and the app can only reach a copy of it.
- `tests/test_db.py` covers the validator.

## Limitations

- Small test sets: one question is worth 3.3 points on the development set and 8 points on the held-out set.
- The V2 rules and V3's extra rule were written after seeing development failures, so development scores are optimistic.
- One model family on a free tier. Results can vary between runs and change as hosted models change.
- Medians are not adjusted for property mix, and inflation uses annual average CPI.
- The data covers Greater Manchester only, standard market sales only, with no addresses.

## Possible next steps

- Retry once with the database error message when generated SQL fails, aimed at the inflation failures.
- A larger test set, to make comparisons between prompts firmer.
- Compare against other models once there is budget to run each one several times.

## Run it yourself

1. The two data files in `data/` are already included. To rebuild them, use the companion project
   (https://github.com/Shrutee18/uk-house-price-pipeline) and run `python src/export_data.py`.
2. `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt pytest`
3. Create a `.env` file containing `GROQ_API_KEY=...` and `GROQ_MODEL=openai/gpt-oss-20b`.
4. Evaluate: `python src/run_eval.py --prompt v3` (use `--split heldout` only once).
5. Run the app: `streamlit run app.py`

## Data

Contains HM Land Registry data © Crown copyright and database right 2021. Licensed under the Open Government
Licence v3.0. Inflation data: Office for National Statistics, CPI INDEX 00: ALL ITEMS 2015=100 (D7BT).