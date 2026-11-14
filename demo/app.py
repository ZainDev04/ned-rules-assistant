"""NED Rules Assistant: Streamlit demo for the NLP CCP.

Run:  streamlit run app.py
"""
import streamlit as st

from rag import RulesAssistant

st.set_page_config(page_title="NED Rules Assistant", layout="wide")


@st.cache_resource(show_spinner="Loading NED regulations and search indexes...")
def load_assistant():
    return RulesAssistant(use_dense=True)


assistant = load_assistant()

EXAMPLES = [
    "What is the minimum attendance required to sit in the final exam?",
    "Final exam dene ke liye kam az kam kitni hazri chahiye?",
    "Pehle saal ke fall semester mein CGPA 2 se kam aaye to kya hota hai?",
    "Kya exam hall mein mobile phone le ja sakte hain?",
    "Until which week can I withdraw from a course?",
    "What is the hostel fee for boys?",
]

# ---------------- sidebar ----------------
with st.sidebar:
    st.header("Settings")
    method = st.selectbox("Retrieval method", assistant.available_methods, index=0,
                          help="BM25 was the best retriever in our pilot evaluation.")
    k = st.slider("Clauses to retrieve (top-k)", 1, 8, 4)
    use_lexicon = st.checkbox("Roman Urdu word normalisation", value=True,
                              help="Maps words like 'hazri' to 'attendance' before searching.")
    llm_ready = RulesAssistant.llm_available()
    use_llm = st.checkbox("Generate answer with Claude", value=llm_ready, disabled=not llm_ready,
                          help="Needs the ANTHROPIC_API_KEY environment variable. Without it the demo "
                               "shows the most relevant sentences of the rules instead.")
    compare = st.checkbox("Also show plain LLM answer (no retrieval)", value=False, disabled=not llm_ready,
                          help="For research question 2: compare a chatbot answering from memory "
                               "with the RAG answer.")
    if assistant.dense_error:
        st.caption("Dense retriever is off (sentence-transformers model not available).")
    st.divider()
    st.caption("Knowledge base: NED Regulations for Admission, Studies and Examinations "
               "(Notification 4155, 13-01-2025) and NED Examinations Regulations 2024 "
               "(Notification 56434, 26-06-2024), from reg.neduet.edu.pk.")

# ---------------- main page ----------------
st.title("NED Rules Assistant")
st.write("Ask about NED undergraduate rules in English or Roman Urdu. Every answer cites the clause "
         "it came from, so you can check the original rule.")

# allow a question in the link, e.g. http://localhost:8501/?q=hazri
if "q" in st.query_params and "question" not in st.session_state:
    st.session_state["question"] = st.query_params["q"]

cols = st.columns(3)
for i, ex in enumerate(EXAMPLES):
    if cols[i % 3].button(ex, key=f"ex{i}", use_container_width=True):
        st.session_state["question"] = ex

question = st.text_input("Your question", key="question",
                         placeholder="e.g. Semester chorne par kaun si fees adjust hoti hai?")

if question:
    with st.spinner("Searching the regulations..."):
        out = assistant.ask(question, method=method, k=k, use_lexicon=use_lexicon, use_llm=use_llm)

    st.subheader("Answer")
    st.info(out["answer"])
    st.caption(f"Answer mode: {out['mode']}  |  Language detected: "
               f"{'Roman Urdu' if out['roman_urdu'] else 'English'}")
    if out["conflict"] and out["answerable"]:
        st.warning(out["conflict"])

    if compare and llm_ready:
        with st.spinner("Asking the plain LLM (no documents)..."):
            try:
                plain = assistant.plain_llm_answer(question)
            except Exception as e:
                plain = f"Plain LLM call failed: {type(e).__name__}"
        st.subheader("Plain LLM answer (no retrieval)")
        st.write(plain)
        st.caption("This answer comes from the model's memory only. Compare it with the cited RAG answer above.")

    with st.expander("How the question was processed", expanded=False):
        st.write(f"**Search query after normalisation:** `{out['normalised_query']}`")
        if out["expansions"]:
            st.write("**Roman Urdu words mapped:** " + ", ".join(out["expansions"]))
        cov, unknown = assistant.coverage(question, use_lexicon)
        st.write(f"**Question words found in the regulations:** {cov:.0%}"
                 + (f" (not found: {', '.join(unknown)})" if unknown else ""))

    st.subheader(f"Retrieved clauses ({method})")
    for rank, r in enumerate(out["results"], start=1):
        with st.expander(f"{rank}. [{r['id']}]  page {r['page']}  |  score {r['score']:.3f}", expanded=rank == 1):
            st.caption(r["doc_title"])
            st.write(r["text"])
