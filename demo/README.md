# NED Rules Assistant (demo)

A small retrieval-augmented generation (RAG) prototype for our NLP CCP. It answers student questions about NED University's undergraduate rules in English or Roman Urdu and cites the clause each answer comes from.

Group: Shaikh Muhammad Zain, Syed Mohammad Huzaifa, Muhammad Maaz ur Rehman. BS Artificial Intelligence, Department of CSIT, NED University of Engineering and Technology.

## How it works

1. `build_index.py` reads the two official NED regulation PDFs in `../ned_docs/` and splits them into 174 clause-sized chunks (for example `ADM 7.5`, page 5).
2. The question is normalised. Roman Urdu words are mapped to the formal English words used in the rules (`hazri` becomes `attendance`, `nakal` becomes `unfair means`) and filler words (`kya`, `ke liye`, `hai`) are removed.
3. Retrieval finds the most relevant clauses with one of four methods:
   - BM25: keyword matching
   - Fuzzy: TF-IDF over character 3 to 5 grams, which tolerates spelling variation
   - Dense: multilingual sentence embeddings (`paraphrase-multilingual-MiniLM-L12-v2`), used if `sentence-transformers` is installed
   - Hybrid: reciprocal rank fusion of the above
4. If too few of the question's words exist anywhere in the rules, the assistant refuses instead of guessing.
5. The answer is written by Claude using only the retrieved clauses, with clause ids in brackets. Without an API key, the demo shows the most relevant sentences of the top clauses (extractive mode), so it still works offline.

## Run it

```
pip install -r requirements.txt
python build_index.py
streamlit run app.py
```

To turn on generated answers, set an Anthropic API key first.

PowerShell:

```
$env:ANTHROPIC_API_KEY = "your key"
streamlit run app.py
```

## Pilot evaluation

```
python evaluate.py
```

This runs 25 English questions, the same 25 written in Roman Urdu, and 5 unanswerable question pairs. It writes `results.md` with Recall@1, Recall@3, Recall@5 and MRR@10 for each retriever, with and without the Roman Urdu normalisation, and the refusal results. The test set is small and written by us, so the numbers are a pilot, not a final result.

## Files

- `build_index.py`: PDF to clause chunks (`chunks.json`)
- `rag.py`: normalisation, retrievers, refusal check, answer generation
- `app.py`: Streamlit web interface
- `eval_questions.json`: pilot test questions with gold phrases
- `evaluate.py`: retrieval and refusal evaluation

## Offline web version

`../ui/NED_Rules_Assistant.html` is the same assistant as a single web page (JavaScript, no Python, works offline). Double-click it to open it in Chrome or Edge. It has BM25, fuzzy and hybrid retrieval, Roman Urdu normalisation, the refusal check, clause citations and the two-notification warning. It does not include the dense embedding model or Claude answers. To rebuild it after changing `rag.py` or `chunks.json`, run `python ../ui/build_ui.py`.
