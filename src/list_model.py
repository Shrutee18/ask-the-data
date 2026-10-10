from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

for m in sorted(Groq().models.list().data, key=lambda m: m.id):
    print(m.id)