"""Step 1 of the demo: turn NED regulation PDFs into clause-sized chunks.

Run:  python build_index.py
Output: chunks.json (one entry per clause, with document name, page and clause number)
"""
import json
import re
from pathlib import Path

import pymupdf

HERE = Path(__file__).parent
DOCS_DIR = HERE.parent / "ned_docs"

# Short codes are used in citations, e.g. "ADM 7.5" or "EXM 11.3"
DOCUMENTS = [
    {
        "file": "admission_studies_regulations.pdf",
        "code": "ADM",
        "title": "NED Regulations for Admission, Studies and Examinations (Semester System), Notification 4155, 13-01-2025",
    },
    {
        "file": "exam_regulations.pdf",
        "code": "EXM",
        "title": "NED Examinations Regulations (Semester System) 2024, Notification 56434, 26-06-2024",
    },
]

# A new clause starts on a line like "7.5 ...", "8.4 a) ...", "3.6 (ii) ...", "11. GRADE ..."
CLAUSE_START = re.compile(r"^\s*(\d{1,2}(?:\.\d{1,2}){0,2})(?:\.|\s|\(|[a-z]\)|$)")
SUB_LABEL = re.compile(r"^\s*\d{1,2}(?:\.\d{1,2}){0,2}\s*(\([ivx]+\)|\([a-z]\)|[a-z]\))")
PAGE_FOOTER = re.compile(r"^\s*Page \d+ of \d+\s*$")

MIN_CHARS = 150   # very short pieces are merged into the next clause
MAX_CHARS = 1800  # very long clauses are split so each chunk stays focused


def read_lines(pdf_path):
    """Yield (page_number, line) for every non-empty line in the PDF."""
    doc = pymupdf.open(pdf_path)
    for page_no, page in enumerate(doc, start=1):
        for line in page.get_text().splitlines():
            if PAGE_FOOTER.match(line) or not line.strip():
                continue
            yield page_no, line.rstrip()


def valid_clause_number(num, last_major):
    """Reject numbers that are really table values (e.g. grade points 4.0, 3.7)."""
    major = int(num.split(".")[0])
    return last_major <= major <= last_major + 1 and major <= 25


def split_into_clauses(doc_info):
    pdf_path = DOCS_DIR / doc_info["file"]
    clauses = []
    current = {"clause": "0", "page": 1, "lines": []}
    last_major = 0

    for page_no, line in read_lines(pdf_path):
        m = CLAUSE_START.match(line)
        if m and valid_clause_number(m.group(1), last_major):
            if current["lines"]:
                clauses.append(current)
            num = m.group(1)
            last_major = int(num.split(".")[0])
            sub = SUB_LABEL.match(line)
            if sub and "." in num:
                num = f"{num} {sub.group(1)}"
            current = {"clause": num, "page": page_no, "lines": []}
        current["lines"].append(line.strip())
    if current["lines"]:
        clauses.append(current)
    return clauses


def to_chunks(doc_info, clauses):
    chunks = []
    buffer = None
    for c in clauses:
        text = re.sub(r"\s+", " ", " ".join(c["lines"])).strip()
        if buffer:  # merge a short previous piece into this one
            text = buffer["text"] + " " + text
            c = {**c, "clause": buffer["clause"], "page": buffer["page"]}
            buffer = None
        if len(text) < MIN_CHARS:
            buffer = {"text": text, "clause": c["clause"], "page": c["page"]}
            continue
        pieces = [text]
        if len(text) > MAX_CHARS:
            # split long clauses on sentence ends, keeping pieces under MAX_CHARS
            sentences = re.split(r"(?<=[.;:])\s+", text)
            pieces, cur = [], ""
            for s in sentences:
                if len(cur) + len(s) > MAX_CHARS and cur:
                    pieces.append(cur.strip())
                    cur = ""
                cur += " " + s
            if cur.strip():
                pieces.append(cur.strip())
        for i, piece in enumerate(pieces):
            suffix = f" (part {i + 1})" if len(pieces) > 1 else ""
            chunks.append({
                "id": f"{doc_info['code']} {c['clause']}{suffix}",
                "doc_code": doc_info["code"],
                "doc_title": doc_info["title"],
                "clause": c["clause"],
                "page": c["page"],
                "text": piece,
            })
    if buffer:
        chunks.append({
            "id": f"{doc_info['code']} {buffer['clause']}",
            "doc_code": doc_info["code"],
            "doc_title": doc_info["title"],
            "clause": buffer["clause"],
            "page": buffer["page"],
            "text": buffer["text"],
        })
    return chunks


def main():
    all_chunks = []
    for doc_info in DOCUMENTS:
        clauses = split_into_clauses(doc_info)
        chunks = to_chunks(doc_info, clauses)
        all_chunks.extend(chunks)
        print(f"{doc_info['file']}: {len(clauses)} clauses -> {len(chunks)} chunks")
    # make ids unique (the same clause number can repeat, e.g. "3.6 (i)" and "3.6 (ii)")
    seen = {}
    for ch in all_chunks:
        base = ch["id"]
        seen[base] = seen.get(base, 0) + 1
        if seen[base] > 1:
            ch["id"] = f"{base} #{seen[base]}"
    out = HERE / "chunks.json"
    out.write_text(json.dumps(all_chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(all_chunks)} chunks to {out.name}")


if __name__ == "__main__":
    main()
