# Changes made to the evaluation after the first run
- Questions 3, 7, 18, 19, 20, 26, 35: gold queries now return only the name asked for, because the scorer rejected correct answers that omitted a supporting number (found on Q3).
- Question 6: reworded to ask for 2018 and 2025 explicitly, because "change between" was ambiguous.
- First scores (before these changes): V1 12 of 30, V2 26 of 30.
- Question 6: added a second accepted answer shape (one row, two columns), because a correct answer was marked wrong for layout.

## Held-out run (openai/gpt-oss-20b, prompt V3, run once, no changes made afterwards)
- Scored 10 of 12 as run.
- Q26: returned both medians instead of naming the winner (valid, different shape).
- Q29: returned a proportion (0.051) where the key expected a percentage (5.09). "Share" is ambiguous.
- These judgements were made after seeing the results, so the headline stays 10 of 12. Accepting both would give 12 of 12.
