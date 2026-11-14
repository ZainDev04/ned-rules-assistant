"""Builds the standalone website ui/NED_Rules_Assistant.html (no Python needed to use it).

Run:  python build_ui.py
It reads the clause chunks and word lists from ../demo so both versions stay identical.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "demo"))
import rag  # noqa: E402

chunks = json.loads((HERE.parent / "demo" / "chunks.json").read_text(encoding="utf-8"))
data = {
    "chunks": [{k: c[k] for k in ("id", "doc_code", "clause", "page", "text")} for c in chunks],
    "docs": {
        "ADM": {"title": "Regulations for Admission, Studies and Examinations (Semester System)",
                "notification": "Notification 4155", "date": "13-01-2025"},
        "EXM": {"title": "Examinations Regulations (Semester System) 2024",
                "notification": "Notification 56434", "date": "26-06-2024"},
    },
    "englishStopwords": sorted(rag.ENGLISH_STOPWORDS),
    "romanUrduStopwords": sorted(rag.ROMAN_URDU_STOPWORDS),
    "lexicon": rag.ROMAN_URDU_LEXICON,
    "lexiconNotCountedForDetection": sorted(rag.LEXICON_ENGLISH_WORDS),
    "phrases": [[pat, tok] for pat, tok in rag.ROMAN_URDU_PHRASES],
}


template = (HERE / "site.html").read_text(encoding="utf-8")
engine = (HERE / "engine.js").read_text(encoding="utf-8")
fonts = (HERE / "fonts.css").read_text(encoding="utf-8")
results = json.loads((HERE.parent / "demo" / "results.json").read_text(encoding="utf-8"))
results = {"rows": [{k: r[k] for k in ("method", "lang", "lexicon", "Recall@1", "Recall@3", "Recall@5", "MRR@10")}
                    for r in results["rows"]], "refusal": results["refusal"]}


def js(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", r"<\/")


theme = (HERE / "theme.css").read_text(encoding="utf-8")
html = (template.replace("/*__FONTS__*/", fonts).replace("/*__THEME__*/", theme)
        .replace("/*__ENGINE__*/", engine)
        .replace("/*__DATA__*/null", js(data))
        .replace("/*__RESULTS__*/null", js(results)))
out = HERE / "NED_Rules_Assistant.html"
out.write_text(html, encoding="utf-8")
print(f"Saved {out.name} ({len(html) // 1024} KB)")
