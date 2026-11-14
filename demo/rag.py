"""The RAG engine for the NED Rules Assistant demo.

Pipeline:  question -> Roman Urdu normalisation -> retrieval (BM25 / fuzzy / dense / hybrid)
           -> answer (Claude grounded on the retrieved clauses, or an extractive fallback)

Every answer carries citations such as [ADM 7.5], so a student can check the original rule.
"""
import difflib
import json
import math
import os
import re
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

HERE = Path(__file__).parent

# ---------------------------------------------------------------------------
# 1. Text cleaning and Roman Urdu support
# ---------------------------------------------------------------------------

ENGLISH_STOPWORDS = set("""
a an the of to in on for and or is are was were be been being by with as at from that this these those
it its his her he she they them their any such shall may will can should would could do does did not no
if then than there here which who whom what when where how why all each every other into under upon
i me my we our you your about after before during up down out over only also so very just
need needed much many get got want know tell please
""".split())

# Roman Urdu function words: they carry no search meaning, so they are dropped.
ROMAN_URDU_STOPWORDS = set("""
kya kia ka ki ke hai hain hy he mein me main se ko agar to tou kitni kitne kitna kab kaise kese kaisay
kyun kyu hota hoti hote hoga hogi mera meri mere mujhe muje hum humein kar karna karne sakta sakti sakte
chahiye chahye liye lie wala wali walay aur ya bhi nahi nahin nai jab koi kuch tak par pe ap aap apna apni
yeh ye woh wo isko usko jo jis kis kon kaun hua hui gaya gayi raha rahi ho na
karte karta karti hue huay sath saath pakde pakra pakray gaye gaye baad bahar ja jaa jana lene lena
hone hona chorne agle agla milne milte milta az pehle pehla aaye aaye band reh rehna badalne banta
parhne sa si karwane karwana andar poori pura zaroori le dene dena kaunsa konsa ek do teen kahan
""".split())

# Roman Urdu / colloquial words mapped to the formal English words used in NED's regulations.
# Several spellings are listed because Roman Urdu has no fixed spelling (hazri, haazri, hazree...).
ROMAN_URDU_LEXICON = {
    "hazri": "attendance", "haazri": "attendance", "hazree": "attendance", "haziri": "attendance",
    "hazirii": "attendance", "attendence": "attendance", "attendnce": "attendance",
    "imtihan": "examination", "imtehan": "examination", "imtihaan": "examination", "imtahan": "examination",
    "paper": "examination", "papers": "examination", "exam": "examination", "exams": "examination",
    "nakal": "unfair means", "naqal": "unfair means", "cheating": "unfair means", "cheat": "unfair means",
    "dakhla": "admission", "dakhila": "admission", "dakhilah": "admission", "admisson": "admission",
    "fees": "fee", "fess": "fee", "paisay": "fee", "paise": "fee", "wapis": "refund refunded adjusted",
    "kam": "less minimum", "kum": "less minimum", "zyada": "maximum more", "ziada": "maximum more",
    "kamaz": "minimum", "kamazkam": "minimum least", "zyadase": "maximum",
    "saal": "years", "sal": "years", "hafte": "weeks", "haftay": "weeks", "hafta": "week",
    "din": "days", "dino": "days", "mahine": "months",
    "dobara": "repeat again improvement", "dubara": "repeat again improvement",
    "chorna": "withdrawal", "chhorna": "withdrawal", "chor": "withdrawal", "chhor": "withdrawal",
    "chutti": "withdrawal", "chhutti": "withdrawal",
    "nateeja": "result", "natija": "result", "result": "result",
    "number": "marks", "numbers": "marks", "nambar": "marks",
    "mazmoon": "course subject", "subject": "course", "subjects": "courses",
    "mobile": "mobile phone smart device", "phone": "mobile phone", "calculator": "programmable calculators",
    "degree": "degree award", "milegi": "award", "milay": "award", "milta": "award",
    "shart": "condition eligibility", "sharait": "conditions eligibility",
    "fail": "fail failed failing", "pass": "pass passed",
    "badalna": "change", "tabdeel": "change", "discipline": "discipline", "department": "discipline",
    "recheck": "scrutiny inquiry correctness", "rechecking": "scrutiny inquiry correctness",
    "medal": "gold medal", "position": "merit position",
    "taleem": "studies", "parhai": "studies", "class": "classes",
    "seat": "seats", "shaher": "domiciled", "domicile": "domiciled",
    "test": "entry test", "entry": "entry test",
    "late": "late", "jurmana": "fee penalty", "saza": "punishment debarred",
    "kitab": "books notes", "kitabein": "books notes", "notes": "notes",
    "sifarish": "approach relative influence", "rishtedar": "relative guardian",
    "cgpa": "cgpa", "gpa": "gpa",
    "percent": "marks percentage", "percentage": "marks percentage", "inter": "hsc", "intermediate": "hsc",
    "der": "time hour", "shuru": "start commencement", "khatam": "complete",
}


# Lexicon entries that are ordinary English words: they do not signal that a question is Roman Urdu.
LEXICON_ENGLISH_WORDS = {
    "exam", "exams", "fail", "pass", "result", "subject", "subjects", "degree", "mobile", "phone", "fees",
    "notes", "test", "late", "class", "cgpa", "gpa", "paper", "papers", "position", "seat", "department",
    "discipline", "calculator", "medal", "entry", "number", "numbers", "percent", "percentage", "inter",
    "intermediate", "cheating", "cheat", "recheck", "rechecking", "attendence", "attendnce", "admisson",
}


def tokenize(text):
    return re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower())


def light_stem(word):
    """A very small stemmer so 'courses' matches 'course' and 'examinations' matches 'examination'."""
    for suffix in ("ations", "ation", "ings", "ing", "ies", "es", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)] + ("y" if suffix == "ies" else "")
    return word


def detect_roman_urdu(question):
    words = tokenize(question)
    if not words:
        return False
    hits = sum(1 for w in words if w in ROMAN_URDU_STOPWORDS
               or (w in ROMAN_URDU_LEXICON and w not in LEXICON_ENGLISH_WORDS))
    return hits >= 2 or hits / len(words) >= 0.25


# Multi-word Roman Urdu phrases are joined into one token before word mapping.
ROMAN_URDU_PHRASES = [
    (r"\bkam\s*az\s*kam\b", "kamazkam"),
    (r"\bzyada\s*se\s*zyada\b", "zyadase"),
    (r"\bziada\s*se\s*ziada\b", "zyadase"),
]


def join_phrases(text):
    for pattern, token in ROMAN_URDU_PHRASES:
        text = re.sub(pattern, token, text, flags=re.IGNORECASE)
    return text


def normalise_query(question, use_lexicon=True):
    """Return (normalised query text, list of expansions that were applied)."""
    words = tokenize(join_phrases(question) if use_lexicon else question)
    kept, expansions = [], []
    for w in words:
        if use_lexicon and w in ROMAN_URDU_LEXICON:
            eng = ROMAN_URDU_LEXICON[w]
            kept.append(eng)
            if eng.split()[0] != w:
                expansions.append(f"{w} -> {eng}")
        elif w in ROMAN_URDU_STOPWORDS and use_lexicon:
            continue
        else:
            kept.append(w)
    return " ".join(kept), expansions


def content_tokens(text):
    return [light_stem(t) for t in tokenize(text) if t not in ENGLISH_STOPWORDS and len(t) > 1]


# ---------------------------------------------------------------------------
# 2. Retrievers
# ---------------------------------------------------------------------------

class BM25:
    """Okapi BM25 (Robertson and Zaragoza, 2009): the classic keyword-matching retriever."""

    def __init__(self, docs, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.doc_tokens = [content_tokens(d) for d in docs]
        self.doc_len = np.array([len(t) for t in self.doc_tokens], dtype=float)
        self.avgdl = self.doc_len.mean()
        self.tf = [Counter(t) for t in self.doc_tokens]
        df = Counter()
        for t in self.doc_tokens:
            df.update(set(t))
        n = len(docs)
        self.idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}

    def scores(self, query):
        q = content_tokens(query)
        out = np.zeros(len(self.doc_tokens))
        for i, tf in enumerate(self.tf):
            norm = self.k1 * (1 - self.b + self.b * self.doc_len[i] / self.avgdl)
            s = 0.0
            for w in q:
                if w in tf:
                    s += self.idf[w] * tf[w] * (self.k1 + 1) / (tf[w] + norm)
            out[i] = s
        return out


class FuzzyCharRetriever:
    """TF-IDF over character 3-5 grams. Tolerates spelling variation such as
    'attendence' vs 'attendance', which is common in Roman Urdu and student typing."""

    def __init__(self, docs):
        self.vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=1)
        self.matrix = self.vec.fit_transform(docs)

    def scores(self, query):
        q = self.vec.transform([query])
        return (self.matrix @ q.T).toarray().ravel()


class DenseRetriever:
    """Sentence embeddings from a multilingual transformer (Reimers and Gurevych, 2019).
    Optional: used only if the sentence-transformers package and the model are available."""

    MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self, docs):
        from sentence_transformers import SentenceTransformer  # imported lazily (large dependency)
        local = HERE / "models" / self.MODEL_NAME.split("/")[-1]
        self.model = SentenceTransformer(str(local) if local.exists() else self.MODEL_NAME)
        cache = HERE / "dense_cache.npy"
        if cache.exists() and np.load(cache).shape[0] == len(docs):
            self.emb = np.load(cache)
        else:
            self.emb = self.model.encode(docs, normalize_embeddings=True, show_progress_bar=False)
            np.save(cache, self.emb)

    def scores(self, query):
        q = self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
        return self.emb @ q


def reciprocal_rank_fusion(score_lists, k=60):
    """Hybrid retrieval: combine several rankings (Cormack et al., 2009). A clause that ranks
    high in more than one retriever ends up on top."""
    fused = np.zeros(len(score_lists[0]))
    for scores in score_lists:
        ranks = np.argsort(-scores)
        for rank, idx in enumerate(ranks):
            fused[idx] += 1.0 / (k + rank + 1)
    return fused


# ---------------------------------------------------------------------------
# 3. The assistant
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the NED Rules Assistant. You help students of NED University of Engineering and Technology, Karachi, understand the official undergraduate regulations.

Answer ONLY from the regulation clauses given inside <clauses>. Each clause has an id such as ADM 7.5 or EXM 3.5.
Rules for your answer:
- Cite the clause id in square brackets after each fact, for example [EXM 3.5].
- If the clauses do not contain the answer, say exactly: "I could not find this in the NED regulations I have. Please ask your department or the Registrar office." Do not guess and do not use outside knowledge.
- If two clauses disagree (for example an older and a newer notification), mention both and say which notification is newer.
- Reply in the same language style as the student. If the student writes in Roman Urdu, answer in simple Roman Urdu, keeping official terms (CGPA, probation, condonation) in English.
- Keep the answer short: 2 to 5 sentences."""

PLAIN_SYSTEM_PROMPT = """You are a helpful assistant. Answer the student's question about NED University of Engineering and Technology, Karachi, in 2 to 5 sentences. Reply in the same language style as the student."""

NOT_FOUND_EN = "I could not find this in the NED regulations I have. Please ask your department or the Registrar office."
NOT_FOUND_RU = "Yeh baat mujhe NED ki regulations mein nahi mili. Apne department ya Registrar office se poochein."

DOC_DATES = {"ADM": "13-01-2025", "EXM": "26-06-2024"}


class RulesAssistant:
    METHODS = ["BM25 (keywords)", "Fuzzy (character n-grams)", "Dense (multilingual embeddings)", "Hybrid (RRF)"]

    def __init__(self, use_dense=True):
        self.chunks = json.loads((HERE / "chunks.json").read_text(encoding="utf-8"))
        texts = [c["text"] for c in self.chunks]
        self.bm25 = BM25(texts)
        self.vocab = {t for toks in self.bm25.doc_tokens for t in toks}
        self.vocab_list = sorted(self.vocab)
        self.fuzzy = FuzzyCharRetriever(texts)
        self.dense = None
        self.dense_error = None
        if use_dense:
            try:
                self.dense = DenseRetriever(texts)
            except Exception as e:  # missing package, no internet for first download, etc.
                self.dense_error = str(e)

    @property
    def available_methods(self):
        return [m for m in self.METHODS if self.dense is not None or not m.startswith("Dense")]

    # ---- retrieval -------------------------------------------------------
    def score(self, question, method="Hybrid (RRF)", use_lexicon=True):
        query, expansions = normalise_query(question, use_lexicon)
        if method.startswith("BM25"):
            s = self.bm25.scores(query)
        elif method.startswith("Fuzzy"):
            s = self.fuzzy.scores(query)
        elif method.startswith("Dense"):
            if self.dense is None:
                raise RuntimeError("Dense retriever is not available")
            # the dense model sees the original question too, since it is multilingual
            s = self.dense.scores(question + " " + query)
        else:
            lists = [self.bm25.scores(query), self.fuzzy.scores(query)]
            if self.dense is not None:
                lists.append(self.dense.scores(question + " " + query))
            s = reciprocal_rank_fusion(lists)
        return s, query, expansions

    def retrieve(self, question, method="Hybrid (RRF)", k=4, use_lexicon=True):
        s, query, expansions = self.score(question, method, use_lexicon)
        top = np.argsort(-s)[:k]
        results = [{**self.chunks[i], "score": float(s[i])} for i in top]
        return results, query, expansions

    def coverage(self, question, use_lexicon=True):
        """Share of the question's content words that exist anywhere in the regulations
        (allowing small spelling differences). Words like 'hostel' or 'bus' never appear in
        the rules, so a question about them gets low coverage and is refused."""
        query, _ = normalise_query(question, use_lexicon)
        terms = [t for t in set(content_tokens(query)) if not t.isdigit()]
        if not terms:
            return 0.0, []
        unknown = [t for t in terms if t not in self.vocab
                   and not difflib.get_close_matches(t, self.vocab_list, n=1, cutoff=0.85)]
        return 1 - len(unknown) / len(terms), unknown

    def is_answerable(self, question, use_lexicon=True):
        cov, _ = self.coverage(question, use_lexicon)
        return cov >= 0.8

    # ---- answering -------------------------------------------------------
    def _overlap(self, q_terms, text):
        """idf-weighted share of the question's words that appear in a piece of text."""
        terms = set(content_tokens(text))
        total = sum(self.bm25.idf.get(t, 0) for t in q_terms) or 1.0
        return sum(self.bm25.idf.get(t, 0) for t in q_terms & terms) / total

    def extractive_answer(self, question, results, roman_urdu):
        """No-LLM fallback: return the most relevant sentences of the top clauses, with citations."""
        query, _ = normalise_query(question)
        q_terms = set(content_tokens(query))
        candidates = []
        for rank, r in enumerate(results[:3]):
            # split on sentence ends and on list markers such as "ii.", "b)", "(iii)"
            parts = re.split(r"(?<=[.;:])\s+(?=[A-Z0-9(])|\s(?=(?:[ivx]{1,4}\.|[a-h]\)|\([ivx]{1,4}\)|\([a-h]\))\s)",
                             r["text"])
            for sent in parts:
                sent = sent.strip()
                if len(sent) < 25:
                    continue
                score = self._overlap(q_terms, sent) * (1.0 - 0.15 * rank)
                if score > 0:
                    candidates.append((score, sent, r["id"]))
        if not candidates:
            return NOT_FOUND_RU if roman_urdu else NOT_FOUND_EN
        candidates.sort(key=lambda x: -x[0])
        chosen = [candidates[0]]
        for c in candidates[1:]:
            if c[0] >= 0.7 * candidates[0][0] and c[1] != chosen[0][1]:
                chosen.append(c)
                break
        lines = [f"{sent} [{cid}]" for _, sent, cid in chosen]
        prefix = "Regulations ke mutabiq (English text): " if roman_urdu else "According to the regulations: "
        return prefix + " ".join(lines)

    @staticmethod
    def llm_available():
        return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))

    @staticmethod
    def _call_claude(system, user_text):
        import anthropic

        client = anthropic.Anthropic()
        model = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
        response = client.beta.messages.create(
            model=model,
            max_tokens=2000,
            system=system,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": user_text}],
        )
        if response.stop_reason == "refusal":
            return "The model declined to answer this question."
        return "".join(b.text for b in response.content if b.type == "text").strip()

    def generate_answer(self, question, results):
        clauses = "\n\n".join(
            f'<clause id="{r["id"]}" document="{r["doc_title"]}" page="{r["page"]}">\n{r["text"]}\n</clause>'
            for r in results
        )
        user_text = f"<clauses>\n{clauses}\n</clauses>\n\nStudent question: {question}"
        return self._call_claude(SYSTEM_PROMPT, user_text)

    def plain_llm_answer(self, question):
        """Baseline for RQ2: the same model with no retrieved clauses (answers from memory)."""
        return self._call_claude(PLAIN_SYSTEM_PROMPT, question)

    def ask(self, question, method="Hybrid (RRF)", k=4, use_lexicon=True, use_llm=True):
        roman_urdu = detect_roman_urdu(question)
        results, query, expansions = self.retrieve(question, method, k, use_lexicon)
        answerable = self.is_answerable(question, use_lexicon)
        conflict = self.find_conflict(question, results)
        if not answerable:
            answer, mode = (NOT_FOUND_RU if roman_urdu else NOT_FOUND_EN), "refused (question words not found in the regulations)"
        elif use_llm and self.llm_available():
            try:
                answer, mode = self.generate_answer(question, results), "Claude, grounded on retrieved clauses"
            except Exception as e:
                answer = self.extractive_answer(question, results, roman_urdu)
                mode = f"extractive (LLM call failed: {type(e).__name__})"
        else:
            answer, mode = self.extractive_answer(question, results, roman_urdu), "extractive (no LLM)"
        return {
            "question": question,
            "roman_urdu": roman_urdu,
            "normalised_query": query,
            "expansions": expansions,
            "results": results,
            "answer": answer,
            "mode": mode,
            "answerable": answerable,
            "conflict": conflict,
        }

    def find_conflict(self, question, results):
        """Flag when strongly matching clauses come from both notifications, since the two documents
        can disagree (e.g. attendance condonation: 65-75% in ADM 7.5, 70-75% in EXM 3.5)."""
        query, _ = normalise_query(question)
        q_terms = set(content_tokens(query))
        overlaps = [(self._overlap(q_terms, r["text"]), r) for r in results[:3]]
        best = max(o for o, _ in overlaps) if overlaps else 0
        strong = {r["doc_code"] for o, r in overlaps if best and o >= 0.75 * best}
        if strong == {"ADM", "EXM"}:
            return ("Matching clauses were found in two different notifications: "
                    f"ADM (dated {DOC_DATES['ADM']}) and EXM (dated {DOC_DATES['EXM']}). "
                    "If they disagree, the newer notification is usually the one in force. Check with your department.")
        return None
