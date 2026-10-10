import sys

from llm import DEFAULT_MODEL, ask

model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
print(f"Model: {model}")
text, tin, tout = ask(model, 'Reply with the JSON {"ok": true} and nothing else.', "ping", max_tokens=500)
print(text, tin, tout)