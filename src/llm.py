import json
import os
import re
import time

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq()  # reads GROQ_API_KEY from the environment

DEFAULT_MODEL = os.getenv("GROQ_MODEL")


def ask(model, system, question, max_tokens=3000):
    """Send one question to Groq. Returns (text, input_tokens, output_tokens)."""
    model = (model or DEFAULT_MODEL or "").replace("groq:", "")
    if not model:
        raise ValueError("No model set. Add GROQ_MODEL to .env or pass --model.")

    for attempt in range(5):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": question},
                ],
                temperature=0,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            return (
                resp.choices[0].message.content,
                resp.usage.prompt_tokens,
                resp.usage.completion_tokens,
            )
        except Exception as e:
            if type(e).__name__ == "RateLimitError" and attempt < 4:
                wait = 15 * (attempt + 1)
                print(f"   rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            raise


def parse(text):
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"\{.*\}", cleaned, re.S)
    if not match:
        raise ValueError("no JSON object found")
    obj = json.loads(match.group(0))
    if obj.get("action") not in ("query", "refuse"):
        raise ValueError("action must be 'query' or 'refuse'")
    if obj["action"] == "query" and not obj.get("sql"):
        raise ValueError("query action without sql")
    return obj