import json
import os
import re
import time

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DEFAULT_MODEL = os.getenv("GROQ_MODEL")


def ask(model, system, question, max_tokens=3000, api_key=None):
    """Send one question to Groq. Returns (text, input_tokens, output_tokens)."""
    model = (model or DEFAULT_MODEL or "").replace("groq:", "")
    if not model:
        raise ValueError("No model set. Add GROQ_MODEL to .env or pass --model.")
    client = Groq(api_key=api_key) if api_key else Groq()
    extra = {}
    if os.environ.get("REASONING_EFFORT"):
        extra["reasoning_effort"] = os.environ["REASONING_EFFORT"]

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
                **extra,
            )
            return (
                resp.choices[0].message.content,
                resp.usage.prompt_tokens,
                resp.usage.completion_tokens,
            )
        except Exception as e:
            if type(e).__name__ == "RateLimitError" and attempt < 4:
                time.sleep(15 * (attempt + 1))
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
