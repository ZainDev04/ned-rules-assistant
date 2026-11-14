"""Pilot evaluation of the retrieval step (RQ1 and RQ3) and of refusing unanswerable questions (RQ2).

Run:  python evaluate.py            (add --no-dense to skip the embedding model)
Output: results.md (tables used in the report and slides) and results.json
"""
import json
import sys
from pathlib import Path

import numpy as np

from rag import RulesAssistant

HERE = Path(__file__).parent
K_VALUES = (1, 3, 5)


def is_hit(chunk_text, gold_phrases):
    t = " ".join(chunk_text.lower().split())
    return any(" ".join(g.lower().split()) in t for g in gold_phrases)


def first_hit_rank(assistant, question, gold, method, use_lexicon):
    scores, _, _ = assistant.score(question, method, use_lexicon)
    order = np.argsort(-scores)[:10]
    for rank, idx in enumerate(order, start=1):
        if is_hit(assistant.chunks[idx]["text"], gold):
            return rank
    return None


def metrics(ranks):
    n = len(ranks)
    out = {f"Recall@{k}": sum(1 for r in ranks if r and r <= k) / n for k in K_VALUES}
    out["MRR@10"] = sum(1.0 / r for r in ranks if r) / n
    return out


def main():
    use_dense = "--no-dense" not in sys.argv
    assistant = RulesAssistant(use_dense=use_dense)
    data = json.loads((HERE / "eval_questions.json").read_text(encoding="utf-8"))
    pairs, unans = data["pairs"], data["unanswerable"]

    # sanity check: every gold phrase must exist in the corpus
    for p in pairs:
        if not any(is_hit(c["text"], p["gold"]) for c in assistant.chunks):
            raise SystemExit(f"Gold phrase for question {p['id']} not found in chunks: {p['gold']}")

    rows = []
    for method in assistant.available_methods:
        for lang in ("en", "ru"):
            for use_lexicon in ((True, False) if lang == "ru" else (True,)):
                ranks = [first_hit_rank(assistant, p[lang], p["gold"], method, use_lexicon) for p in pairs]
                rows.append({"method": method, "lang": lang, "lexicon": use_lexicon, **metrics(ranks),
                             "misses": [p["id"] for p, r in zip(pairs, ranks) if not r or r > 5]})

    # refusal behaviour (same for every method: it uses the confidence score)
    refusal = {}
    for lang in ("en", "ru"):
        answered_ok = sum(assistant.is_answerable(p[lang]) for p in pairs)
        refused_ok = sum(not assistant.is_answerable(u[lang]) for u in unans)
        refusal[lang] = {"answerable_answered": f"{answered_ok}/{len(pairs)}",
                         "unanswerable_refused": f"{refused_ok}/{len(unans)}"}

    lang_name = {"en": "English", "ru": "Roman Urdu"}
    lines = ["# Pilot retrieval results", "",
             f"Corpus: {len(assistant.chunks)} clause chunks from 2 NED regulation documents. "
             f"Test set: {len(pairs)} question pairs (English and Roman Urdu) + {len(unans)} unanswerable pairs.", "",
             "| Retriever | Question language | Roman Urdu lexicon | Recall@1 | Recall@3 | Recall@5 | MRR@10 |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lex = "on" if r["lexicon"] else "off"
        lines.append(f"| {r['method']} | {lang_name[r['lang']]} | {lex} | {r['Recall@1']:.2f} | "
                     f"{r['Recall@3']:.2f} | {r['Recall@5']:.2f} | {r['MRR@10']:.2f} |")
    lines += ["", "## Refusal check (confidence threshold)", ""]
    for lang, v in refusal.items():
        lines.append(f"- {lang_name[lang]}: answerable questions answered {v['answerable_answered']}, "
                     f"unanswerable questions refused {v['unanswerable_refused']}")
    if assistant.dense_error:
        lines += ["", f"Dense retriever not available: {assistant.dense_error}"]
    lines += ["", "## Questions missed in the top 5", ""]
    for r in rows:
        if r["misses"]:
            lex = "lexicon on" if r["lexicon"] else "lexicon off"
            lines.append(f"- {r['method']}, {lang_name[r['lang']]}, {lex}: {r['misses']}")

    (HERE / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (HERE / "results.json").write_text(json.dumps({"rows": rows, "refusal": refusal}, indent=2), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
