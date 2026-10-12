import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from db import connect, run          # noqa: E402
from llm import ask, parse           # noqa: E402
from prompts import PROMPTS          # noqa: E402

st.set_page_config(page_title="Ask the data", layout="wide")

MAX_FREE_QUESTIONS = 10
EXAMPLES = [
    "What was the median price of flats in Manchester in 2023?",
    "Which borough had the highest median price in 2025?",
    "What percentage of sales in 2025 were leasehold?",
    "What was the median price in 2018, expressed in 2025 pounds?",
    "What was the average monthly rent in Salford?",
]


def secret(name, default=None):
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, default)


@st.cache_resource
def get_con():
    return connect()


st.title("Ask the data")
st.caption(
    "Ask a question in plain English about 300,000 Greater Manchester house sales (2018 to 2025). "
    "A language model writes a read-only SQL query, the query runs, and you see both the SQL and the result."
)

model = secret("GROQ_MODEL", "openai/gpt-oss-20b")
server_key = secret("GROQ_API_KEY")

st.sidebar.header("Settings")
user_key = st.sidebar.text_input("Your own Groq API key (optional)", type="password",
                                 help="Used only for your questions in this session and never stored.")
st.sidebar.caption(
    f"Without your own key, each session is limited to {MAX_FREE_QUESTIONS} questions "
    "to protect a shared free-tier quota."
)
st.sidebar.markdown(f"**Model:** `{model}`  \n**Prompt version:** V3")

st.session_state.setdefault("used", 0)
st.session_state.setdefault("q", "")

st.write("Try an example:")
cols = st.columns(len(EXAMPLES))
for col, text in zip(cols, EXAMPLES):
    if col.button(text, use_container_width=True):
        st.session_state["q"] = text

question = st.text_input("Your question", key="q")
go = st.button("Ask", type="primary")

if go and question.strip():
    key = user_key or server_key
    if not key:
        st.error("No API key is configured. Add your own key in the sidebar.")
    elif not user_key and st.session_state["used"] >= MAX_FREE_QUESTIONS:
        st.warning("You have used the free questions for this session. "
                   "Paste your own free Groq API key in the sidebar to continue.")
    else:
        with st.spinner("Thinking..."):
            try:
                raw, tin, tout = ask(model, PROMPTS["v3"], question, api_key=key)
                obj = parse(raw)
            except Exception as e:
                st.error(f"The model call failed ({type(e).__name__}). The free tier may be "
                         "rate limited, so try again in a minute.")
                st.stop()
        if not user_key:
            st.session_state["used"] += 1

        if obj["action"] == "refuse":
            reason = obj.get("reason", "").strip().rstrip(".")
            st.info(
                "This data can't answer that" + (f": {reason}." if reason else ".")
                + " I can answer questions about sale prices, volumes, property types, "
                "tenure, boroughs and years (2018 to 2025) in Greater Manchester."
            )
        else:
            st.subheader("SQL the model wrote")
            st.code(obj["sql"], language="sql")
            if obj.get("note"):
                st.caption(f"Model's note: {obj['note']}")
            try:
                df = run(get_con(), obj["sql"])
                st.subheader("Result")
                st.dataframe(df, hide_index=True, use_container_width=True)
            except Exception as e:
                st.error("The query could not be run. Models sometimes write SQL that fails, "
                         "most often on inflation-adjusted questions.")
                with st.expander("Technical detail"):
                    st.code(str(e))

with st.expander("About this tool and its limits"):
    st.markdown(
        "- Answers are written by a language model and can be wrong. Check the SQL shown.\n"
        "- On a 30-question development set the chosen prompt scored about 29 of 30, and on 12 held-out questions "
        "it scored 10 of 12. Both samples are small, so treat those as rough.\n"
        "- It only answers questions about this table, and declines rents, bedrooms, forecasts, "
        "other areas, years outside 2018 to 2025, and anything that changes data.\n"
        "- Queries run on an in-memory copy with a read-only filter. That filter is a second line of defence, "
        "not a security guarantee; the real protection is that the data is public and non-sensitive.\n"
        "- Medians are not adjusted for property mix, and inflation uses annual average CPI."
    )

st.divider()
st.caption(
    "Contains HM Land Registry data © Crown copyright and database right 2021. "
    "Licensed under the Open Government Licence v3.0. "
    "Inflation data: Office for National Statistics, CPI INDEX 00: ALL ITEMS 2015=100 (D7BT)."
)
