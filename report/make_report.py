"""Builds the CCP research report (Word) from the text below and the pilot results in ../demo/results.json.

Run:  python make_report.py
"""
import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).parent
RESULTS = json.loads((HERE.parent / "demo" / "results.json").read_text(encoding="utf-8"))
OUT = HERE / "NLP_CCP_RAG_Report.docx"

FONT = "Times New Roman"
NAVY = RGBColor(0x1F, 0x2D, 0x3D)

doc = Document()

# ---------------------------------------------------------------- styles
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
for side in ("left_margin", "right_margin"):
    setattr(sec, side, Cm(2.5))
sec.top_margin, sec.bottom_margin = Cm(2.3), Cm(2.3)

normal = doc.styles["Normal"]
normal.font.name = FONT
normal.font.size = Pt(12)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.15

for name, size in (("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 12)):
    st = doc.styles[name]
    st.font.name = FONT
    rfonts = st.element.rPr.rFonts
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        rfonts.attrib.pop(qn(attr), None)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), FONT)
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = NAVY
    st.paragraph_format.space_before = Pt(14 if name == "Heading 1" else 10)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.keep_with_next = True


def para(text="", bold_prefix=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=None, italic=False, after=None):
    p = doc.add_paragraph()
    p.alignment = align
    if bold_prefix:
        r = p.add_run(bold_prefix)
        r.bold = True
        if size:
            r.font.size = Pt(size)
    add_rich(p, text, size=size, italic=italic)
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


def add_rich(p, text, size=None, italic=False):
    """Supports *italic* spans inside text (used for paper titles and Roman Urdu examples)."""
    parts = text.split("*")
    for i, part in enumerate(parts):
        if not part:
            continue
        r = p.add_run(part)
        r.italic = italic or (i % 2 == 1)
        if size:
            r.font.size = Pt(size)


def bullets(items, style="List Bullet"):
    for it in items:
        p = doc.add_paragraph(style=style)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(3)
        add_rich(p, it)


def heading(text, level=1):
    return doc.add_heading(text, level=level)


def shade(cell, hex_color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def table(headers, rows, widths_cm, font_size=9, header_fill="1F2D3D"):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(font_size)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade(c, header_fill)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            add_rich(p, str(val), size=font_size)
            if ri % 2 == 1:
                shade(cells[i], "EEF2F7")
    for row in t.rows:
        for i, w in enumerate(widths_cm):
            row.cells[i].width = Cm(w)
    # repeat header row on each page
    tr_pr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    tr_pr.append(th)
    return t


def caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.italic = True
    r.font.size = Pt(10)
    p.paragraph_format.space_after = Pt(10)


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def add_page_number_footer(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)
    run.font.size = Pt(10)


# ---------------------------------------------------------------- cover page
def centered(text, size, bold=False, after=6, color=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.bold = bold
    if color:
        r.font.color.rgb = color
    p.paragraph_format.space_after = Pt(after)
    return p


centered("NED University of Engineering and Technology, Karachi", 16, True, 2, NAVY)
centered("Department of Computer Science and Information Technology (CSIT)", 13, False, 30)
centered("Natural Language Processing", 13, True, 2)
centered("Complex Computing Problem (CCP): Literature-Based Research Study", 12, False, 40)
centered("Grounded question answering over university academic regulations:", 20, True, 2, NAVY)
centered("a retrieval-augmented generation study for English and Roman Urdu student questions", 16, False, 40, NAVY)
centered("Research area: Retrieval-Augmented Generation (RAG)  |  Domain: Education", 11, False, 40)
centered("Submitted by", 12, True, 4)
for name in ("Shaikh Muhammad Zain", "Syed Mohammad Huzaifa",
             "Muhammad Maaz ur Rehman"):
    centered(name, 12, False, 2)
centered("", 12, False, 20)
centered("Submitted to", 12, True, 4)
centered("Dr. Muhammad Imran", 12, False, 30)
centered("BS Artificial Intelligence  |  Fall 2026  |  15 November 2026", 11, False, 0)
page_break()

# ---------------------------------------------------------------- abstract
heading("Abstract", 1)
para("Students at NED University regularly need answers about attendance limits, probation, course "
     "withdrawal, grade improvement and examination conduct. These answers exist in long official "
     "regulation documents, but students rarely read them and often ask general chatbots instead, which "
     "can produce confident but unsupported answers. Retrieval-augmented generation (RAG) addresses this "
     "by retrieving the relevant clauses first and asking a language model to answer only from them. "
     "We reviewed eight peer-reviewed studies on RAG foundations, hallucination, RAG chatbots for "
     "university regulations and Roman Urdu information retrieval. The reviewed regulation chatbots were "
     "built for Polish, Spanish and Indonesian universities and tested only with questions in each "
     "university's official language. We did not find any study that tests such a system with Roman Urdu or "
     "code-mixed questions, even though this is how many Pakistani students type. The studies also disagree "
     "on whether keyword, dense or hybrid retrieval works best for regulations, and they report weak "
     "refusal of questions the documents do not cover. We propose three research questions on retrieval "
     "choice, hallucination and refusal, and the effect of Roman Urdu input, and a methodology based on "
     "NED's two current undergraduate regulation documents and a parallel English and Roman Urdu test "
     "set. A working prototype and a 60-question pilot show that a small Roman Urdu normalisation step "
     "raises keyword retrieval Recall@5 from 0.84 to 1.00, that BM25 keyword retrieval outperforms a "
     "small multilingual embedding model on these documents, and that refusal of out-of-scope questions "
     "remains an open problem (3 of 5 refused).")
para("Keywords: retrieval-augmented generation, question answering, hallucination, Roman Urdu, "
     "low-resource languages, university regulations, BM25, dense retrieval.", italic=True)

# ---------------------------------------------------------------- 1. introduction
heading("1. Introduction and problem statement", 1)
heading("1.1 Background", 2)
para("Universities publish their academic rules as formal notifications. At NED University of Engineering "
     "and Technology, the two documents that govern undergraduate students are the Regulations for "
     "Admission, Studies and Examinations (Notification 4155, revised 13 January 2025) and the Examinations "
     "Regulations 2024 (Notification 56434, 26 June 2024). Together they run to 34 pages and more than "
     "150 numbered clauses. They decide questions that matter a great deal to a student: whether they can "
     "sit an exam with 72% attendance, what happens after a CGPA below 2.00, until which week a course can "
     "be dropped, and how long they have to apply for scrutiny of a result.")
para("Large language models (LLMs) such as ChatGPT can answer questions in fluent English or Roman Urdu, "
     "but they answer from patterns learned during training. They have not read NED's current notifications "
     "and they tend to fill gaps with plausible text. This behaviour is known as hallucination [9]. For "
     "university rules, a wrong answer has real costs: a student who believes the attendance limit is 60% "
     "may be barred from the exam.")
para("Retrieval-augmented generation (RAG) combines a retriever, which searches a document collection, "
     "with a generator, which writes the answer using the retrieved text [1]. Because the answer is tied to "
     "specific passages, the system can cite the clause it used, and the student can check it. This makes "
     "RAG a natural fit for regulation questions.")

heading("1.2 Problem statement", 2)
para("NED students cannot get quick, reliable and verifiable answers about their own university's rules. "
     "The official documents are long and formal, staff time is limited, and general chatbots give answers "
     "that are not grounded in NED's current notifications. A RAG assistant could help, but three things "
     "are unknown for this setting: which retrieval method finds the right clause in this kind of "
     "document, how much grounding reduces wrong answers and whether the system can refuse questions the "
     "rules do not cover, and how well the system works when students ask in Roman Urdu, which has no "
     "fixed spelling and mixes Urdu and English words.")

heading("1.3 Scope", 2)
para("This study covers the undergraduate rules in the two NED notifications named above, and questions "
     "written in English or in Roman Urdu (Urdu written in the Latin alphabet, often mixed with English). "
     "Urdu in its own script, postgraduate rules and fee schedules are outside the scope. As the assignment "
     "allows, the focus is the research design. We also built a small prototype to test that the design is "
     "workable and to collect pilot numbers.")

# ---------------------------------------------------------------- 2. objectives
heading("2. Research objectives and questions", 1)
heading("2.1 Objectives", 2)
bullets([
    "Review published work on RAG, hallucination, regulation question answering and Roman Urdu retrieval, "
    "and identify what has not yet been studied.",
    "Design a method to compare retrieval approaches on NED's regulations for English and Roman Urdu questions.",
    "Design an evaluation that measures answer correctness, grounding, citation accuracy and refusal of "
    "unanswerable questions.",
    "Build a prototype and a pilot test set to show that the method can be carried out.",
])
heading("2.2 Research questions", 2)
para("The questions follow directly from the gaps in Section 4.")
para(" Which retrieval method, keyword-based (BM25), dense multilingual embeddings or a hybrid of the two, "
     "retrieves the correct clause most often for questions about NED's regulations?", bold_prefix="RQ1.")
para(" How much does grounding answers in retrieved clauses reduce incorrect and unsupported answers compared "
     "with the same LLM answering without retrieval, and how reliably can the system refuse questions that "
     "the regulations do not cover?", bold_prefix="RQ2.")
para(" How much does retrieval and answer quality drop when the same questions are asked in Roman Urdu "
     "instead of English, and how much of that drop can a lightweight Roman Urdu normalisation step recover?",
     bold_prefix="RQ3.")

# ---------------------------------------------------------------- 3. literature
heading("3. Literature review and comparison of existing studies", 1)
para("We selected studies in four groups: the foundations of RAG and dense retrieval, work on hallucination "
     "and noisy retrieval, RAG systems built for university regulations, and retrieval for Roman Urdu. All "
     "eight reviewed papers appear in peer-reviewed venues (NeurIPS, EMNLP, Findings of EMNLP, AAAI, an ICCS "
     "workshop volume in Springer LNCS, two journals and an ACL-affiliated workshop) and each has a DOI or "
     "official proceedings entry listed in the references.")

heading("3.1 Foundations of retrieval-augmented generation", 2)
para("Lewis et al. [1] introduced RAG as a model that combines a pre-trained sequence-to-sequence generator "
     "with a dense retriever over Wikipedia. On open-domain question answering it outperformed models that "
     "relied only on their internal parameters, and its answers were more specific and more factual. The "
     "study showed that the knowledge used by the model can be replaced by swapping the document index, "
     "which is the property that makes RAG suitable for rules that change every year. Its evaluation, "
     "however, was on English Wikipedia questions only.")
para("The retriever in [1] was Dense Passage Retrieval (DPR) by Karpukhin et al. [2]. DPR encodes questions "
     "and passages with two BERT encoders and retrieves by vector similarity. On several open-domain QA "
     "benchmarks it beat the BM25 keyword baseline by 9 to 19 percentage points in top-20 passage accuracy. "
     "This result is often taken to mean that dense retrieval is always better. The paper itself shows that "
     "BM25 remained competitive on questions with rare, exact terms, and that DPR needs training data from "
     "the same domain. Both conditions matter for regulations, which are full of exact terms such as "
     "\"condonation\" or \"FYDP\" and have no training data.")

heading("3.2 Hallucination and the quality of retrieved context", 2)
para("Shuster et al. [3] tested retrieval augmentation in knowledge-grounded dialogue. Human evaluators "
     "found that retrieval substantially reduced hallucinated knowledge compared with the same models "
     "without retrieval, and the best retrieval-augmented models approached the factual accuracy of models "
     "given the gold knowledge passage. This is the main evidence that grounding helps, but it was "
     "measured on open-domain English conversation, not on institutional rules.")
para("Chen et al. [4] built the Retrieval-Augmented Generation Benchmark (RGB) in English and Chinese to test "
     "four abilities that a RAG system needs: noise robustness, negative rejection, information integration "
     "and counterfactual robustness. They found that LLMs often fail to reject a question when none of the "
     "retrieved passages contain the answer, and that irrelevant passages reduce accuracy. Negative rejection "
     "is directly relevant to a rules assistant: many student questions (hostel fees, bus routes) are not "
     "in the regulations at all, and the safe answer is to say so.")

heading("3.3 RAG systems for university regulations", 2)
para("Wojtasik et al. [5] built PoliChat, a RAG chatbot for the regulations of Wroclaw University of Science "
     "and Technology in Poland, and annotated a dataset of regulation questions. They studied model size, "
     "document length, summarisation, context size and prompting. In their retrieval experiments BM25 "
     "outperformed the dense retrievers on long Polish regulation documents, and adding more retrieved "
     "passages lowered citation accuracy. A prompting method they called Analyze&Answer improved citation "
     "accuracy. The system was built and tested only for Polish.")
para("Guadalupe Andrade et al. [6] built an academic chatbot for an Ecuadorian university that answers in "
     "Spanish from five regulatory documents. It uses hybrid retrieval, fusing dense and lexical search with "
     "reciprocal rank fusion, and a locally hosted LLM. With the RAGAS framework [10] it scored 0.90 overall "
     "and 0.97 on faithfulness, yet only 57.9% of 19 users agreed that it did not produce fabricated "
     "information, and quality dropped on long, heavily cross-referenced regulations. The gap between "
     "automatic and human judgement is an important warning for our evaluation design.")
para("Suherwin et al. [7] compared an FAQ chatbot with a RAG chatbot for academic services at an Indonesian "
     "university, using the same official documents and 60 questions judged by three validators. RAG reached "
     "88.33% accuracy against 68.33% for FAQ, with RAGAS context precision 0.86 and faithfulness 0.89, but "
     "it was slower (2.41 s against 0.62 s). The authors call for broader testing with live student queries "
     "and stronger retrieval baselines.")

heading("3.4 Roman Urdu as a low-resource language", 2)
para("Butt et al. [8] note that Roman Urdu is used by millions of people in digital communication but has "
     "almost no information retrieval resources. It has no standard spelling and frequently switches to "
     "English. They built the first Roman Urdu retrieval dataset by translating MS MARCO into Urdu and then "
     "transliterating it, and showed that a multilingual transformer retriever fine-tuned on it outperformed "
     "a lexical baseline (MRR@10 of 0.19 against 0.08). Their data is machine-translated web search "
     "queries, not institutional documents, and they do not study answer generation. Earlier work on Roman "
     "Urdu sentiment analysis by Mehmood et al. [11] reported the same core difficulty: the same word can be "
     "spelled in many ways (for example *hazri*, *haazri*, *hazree*), which breaks exact keyword matching.")

heading("3.5 Literature comparison table", 2)
para("Table 1 compares the eight reviewed studies on the points that matter for our problem.")
lit_rows = [
    ["[1] Lewis et al., NeurIPS 2020", "Open-domain QA; English (Wikipedia)", "Dense (DPR) + seq2seq generator",
     "RAG beats parametric-only models and gives more factual answers", "English Wikipedia only; no refusal or citation study"],
    ["[2] Karpukhin et al., EMNLP 2020", "Open-domain QA; English", "Dense dual encoder vs BM25",
     "Dense retrieval beats BM25 by 9 to 19 points top-20 accuracy", "Needs in-domain training data; BM25 still strong on rare exact terms"],
    ["[3] Shuster et al., Findings of EMNLP 2021", "Knowledge-grounded dialogue; English", "Several retrievers + generators",
     "Retrieval sharply reduces hallucinated knowledge (human evaluation)", "Open-domain chat, not institutional documents"],
    ["[4] Chen et al., AAAI 2024", "RAG benchmark (RGB); English, Chinese", "Retrieved news passages with added noise",
     "LLMs are weak at negative rejection and hurt by irrelevant passages", "No regulation domain; no code-mixed or romanised input"],
    ["[5] Wojtasik et al., ICCS 2025 (LNCS)", "University regulations; Polish", "BM25 and dense retrievers, citations",
     "BM25 beat dense on long documents; more passages lowered citation accuracy", "Polish only; no informal or code-mixed questions"],
    ["[6] Guadalupe Andrade et al., Rev. Tecnol. ESPOL 2026", "University regulations; Spanish", "Hybrid dense + lexical (RRF), local LLM",
     "RAGAS 0.90, faithfulness 0.97, but only 57.9% of users trusted it", "Spanish only; 5 documents; quality drops on cross-referenced rules"],
    ["[7] Suherwin et al., G-Tech 2026", "Academic services; Indonesian", "RAG vs FAQ chatbot",
     "RAG 88.33% vs FAQ 68.33% accuracy; RAG slower", "60 questions; authors ask for stronger retrieval baselines"],
    ["[8] Butt et al., LowResNLP 2025", "General web search; Roman Urdu", "Multilingual transformer vs lexical",
     "First Roman Urdu IR dataset; MRR@10 0.19 vs 0.08", "Translated web data; no domain documents; no answer generation"],
]
table(["Study", "Domain and language", "Retrieval / method", "Main finding", "Limitation for our problem"],
      lit_rows, [3.2, 3.0, 3.1, 3.4, 3.3], font_size=8.5)
caption("Table 1. Comparison of the reviewed studies")

# ---------------------------------------------------------------- 4. gap
heading("4. Identified research gap", 1)
para("Reading the studies side by side shows four specific gaps. Each one is supported by the reviewed "
     "literature, and each leads to a research question.")
para(" The three regulation chatbots [5], [6], [7] were tested only in the official language of their "
     "university (Polish, Spanish, Indonesian), with formally written questions. The only Roman Urdu "
     "retrieval study [8] uses translated web queries and does not involve institutional documents or answer "
     "generation. In the papers we reviewed, and in our searches, we did not find any study that evaluates "
     "a RAG system for university rules with Roman Urdu or code-mixed questions, which is how many "
     "Pakistani students write. This leads to RQ3.", bold_prefix="Gap 1: language of the questions.")
para(" Dense retrieval clearly beat BM25 on Wikipedia questions [2], but BM25 beat dense retrievers on long "
     "Polish regulations [5], and a hybrid worked well on Spanish regulations [6]. These results conflict, "
     "and none of them come from English-language Pakistani regulations, where clause numbers and exact "
     "legal terms are common. This leads to RQ1.", bold_prefix="Gap 2: no agreement on the retriever.")
para(" Retrieval reduces hallucination in open-domain settings [3], but LLMs are poor at rejecting questions "
     "whose answers are not in the retrieved text [4]. The regulation chatbots [5], [6], [7] report "
     "correctness and faithfulness on answerable questions but do not test out-of-scope questions, and in "
     "[6] users trusted the system much less than the automatic faithfulness score suggested. A rules "
     "assistant must refuse safely. This leads to RQ2.", bold_prefix="Gap 3: refusal and trust.")
para(" Studies [5] and [6] report that long, cross-referenced regulations reduce quality. None of the "
     "reviewed studies discusses what happens when two current notifications disagree. NED's documents "
     "show this problem: the 2025 Admission and Studies Regulations allow attendance condonation for an "
     "aggregate between 65% and 75% (clause 7.5), while the 2024 Examinations Regulations set the range at "
     "70% to 75% (clause 3.5). We include such cases in the test set as part of RQ2.",
     bold_prefix="Gap 4: conflicting documents.")

# ---------------------------------------------------------------- 5. methodology
heading("5. Proposed research methodology", 1)
heading("5.1 Overview", 2)
para("Figure 1 shows the proposed system and study design. The regulations are split into clauses and "
     "indexed once. For each question, a normalisation step handles Roman Urdu, a retriever returns the "
     "top-k clauses, and an LLM writes an answer that cites clause ids or refuses. Each stage is evaluated "
     "separately so that errors can be traced to retrieval or to generation.")
doc.add_picture(str(HERE / "pipeline.png"), width=Cm(16))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
caption("Figure 1. Proposed RAG pipeline and evaluation design")

heading("5.2 Knowledge base", 2)
para("The knowledge base is the two official NED notifications, downloaded from the Registrar's website "
     "(reg.neduet.edu.pk). Text is extracted from the PDFs and split at clause numbers (for example 7.5 or "
     "3.6 (ii)) instead of fixed-size windows, so that each chunk is one complete rule. Very short pieces "
     "are merged with the next clause and clauses longer than about 1,800 characters are split at sentence "
     "boundaries. Each chunk keeps its document code (ADM or EXM), clause number, page and notification "
     "date. In the prototype this produced 174 chunks. Clause-level chunking addresses the length problem "
     "reported in [5] and gives exact citations for free.")

heading("5.3 Test dataset", 2)
para("We will build a test set called NED-RulesQA. The plan is:")
bullets([
    "150 questions written by students about topics students actually ask: attendance, probation, "
    "registration limits, withdrawal, grading, change of discipline, examination conduct, unfair means, "
    "scrutiny and award of degree.",
    "Each question written in English and in Roman Urdu with the same meaning (300 questions). Roman Urdu "
    "versions will be written by different group members so that spelling varies naturally.",
    "About 20% of the questions will be unanswerable from the documents (for example hostel fees) to "
    "measure refusal, and a small set will target clauses where the two notifications disagree.",
    "Each answerable question is labelled with its gold clause id(s) and a reference answer. Two members "
    "label independently and agreement is reported with Cohen's kappa. Disagreements are resolved by "
    "discussion with the third member.",
])
para("For the pilot we wrote 25 English questions, their 25 Roman Urdu versions, and 5 unanswerable "
     "questions in both languages (60 questions in total).")

heading("5.4 Roman Urdu normalisation", 2)
para("Two approaches will be compared for RQ3. The first is a lightweight lexicon that maps common Roman "
     "Urdu words and their spelling variants to the formal English terms used in the regulations (for "
     "example *hazri*, *haazri* and *haziri* to attendance; *nakal* to unfair means; *dakhla* to "
     "admission) and removes Roman Urdu function words such as *kya*, *ke liye* and *hai*. The second is "
     "to rely on multilingual embedding models without any normalisation. The lexicon is cheap and "
     "explainable, which matters in a university setting; the embedding approach needs no manual work. "
     "Character n-gram matching is also tested because it tolerates spelling variation.")

heading("5.5 Retrieval methods (RQ1)", 2)
bullets([
    "BM25 [12]: the standard probabilistic keyword ranking function, with no training needed.",
    "Character n-gram TF-IDF: vectors over 3 to 5 character pieces, which match *attendence* with "
    "*attendance*.",
    "Dense retrieval: multilingual sentence embeddings [13] (paraphrase-multilingual-MiniLM-L12-v2), and a "
    "stronger multilingual model in the full study.",
    "Hybrid: reciprocal rank fusion (RRF) [14] of BM25 and dense rankings, the approach used in [6].",
])

heading("5.6 Answer generation and baselines (RQ2)", 2)
para("The generator receives the top-k clauses with their ids and a short instruction: answer only from "
     "the clauses, cite the clause id after each fact, mention both clauses if they disagree, reply in the "
     "student's language style, and use a fixed refusal sentence if the answer is not present. We will test "
     "at least one commercial LLM and one open model that can run locally. For RQ2 the baseline is the "
     "same LLM answering without any retrieved clauses. A refusal check before generation also measures "
     "how many of the question's content words exist anywhere in the regulations, so that clearly "
     "out-of-scope questions are refused without calling the LLM.")

heading("5.7 Evaluation measures", 2)
para("Retrieval is measured with Recall@k (k = 1, 3, 5), the share of questions whose gold clause is in "
     "the top k, and Mean Reciprocal Rank (MRR@10), which rewards ranking the gold clause higher. Answers "
     "are judged by two members on a three-level scale (correct, partly correct, incorrect) against the "
     "reference answer. Faithfulness (whether every claim is supported by the retrieved clauses) and "
     "context precision are measured with RAGAS [10], and because [6] found that automatic scores can "
     "overstate quality, a sample is also checked by hand. Citation accuracy is the share of cited clause "
     "ids that actually support the statement. Refusal is measured as the share of unanswerable questions "
     "correctly refused and the share of answerable questions wrongly refused. Paired comparisons (for "
     "example the same question with and without retrieval) use McNemar's test for correct/incorrect "
     "outcomes. Table 2 maps each research question to its method and measures.")
table(["Research question", "What is compared", "Measures"], [
    ["RQ1: best retriever", "BM25, character n-gram, dense, hybrid (RRF)", "Recall@1/3/5, MRR@10 per language"],
    ["RQ2: grounding and refusal", "RAG vs same LLM without retrieval; with and without refusal check",
     "Answer correctness, faithfulness, citation accuracy, refusal rates, McNemar's test"],
    ["RQ3: Roman Urdu", "English vs Roman Urdu versions of the same questions; with and without normalisation",
     "Drop in Recall@k, MRR and correctness between languages"],
], [3.6, 6.2, 6.2], font_size=9)
caption("Table 2. Mapping of research questions to methods and measures")

heading("5.8 Prototype and pilot results", 2)
para("To check that the methodology can be carried out, we built a prototype called NED Rules Assistant "
     "in Python. It implements the pipeline in Figure 1 with a Streamlit web interface. It answers with "
     "Claude when an API key is set and otherwise shows the most relevant sentences of the top clauses. "
     "Each answer shows the clause ids, page numbers and the retrieved text. It also shows a warning when "
     "strongly matching clauses come from both notifications. Table 3 gives the pilot retrieval results "
     "on the 60-question pilot set.")

lang_name = {"en": "English", "ru": "Roman Urdu"}
res_rows = []
for r in RESULTS["rows"]:
    res_rows.append([r["method"], lang_name[r["lang"]], "on" if r["lexicon"] else "off",
                     f"{r['Recall@1']:.2f}", f"{r['Recall@3']:.2f}", f"{r['Recall@5']:.2f}", f"{r['MRR@10']:.2f}"])
table(["Retriever", "Language", "Normalisation", "R@1", "R@3", "R@5", "MRR@10"], res_rows,
      [4.8, 2.4, 2.4, 1.4, 1.4, 1.4, 1.8], font_size=9)
caption("Table 3. Pilot retrieval results (25 question pairs, 174 clause chunks)")


def find(method_prefix, lang, lex):
    for r in RESULTS["rows"]:
        if r["method"].startswith(method_prefix) and r["lang"] == lang and r["lexicon"] == lex:
            return r
    return None


bm_en, bm_ru, bm_raw = find("BM25", "en", True), find("BM25", "ru", True), find("BM25", "ru", False)
dense_ru_raw = find("Dense", "ru", False)
ref = RESULTS["refusal"]
obs = [
    f"Without normalisation, Roman Urdu questions were much harder: BM25 MRR@10 fell from "
    f"{bm_en['MRR@10']:.2f} (English) to {bm_raw['MRR@10']:.2f}. With the lexicon, Roman Urdu reached "
    f"MRR@10 {bm_ru['MRR@10']:.2f} and Recall@5 {bm_ru['Recall@5']:.2f}, close to or above English. "
    f"This early result supports RQ3 and suggests that a small, explainable normalisation step recovers "
    f"most of the gap.",
    "BM25 was the best retriever on this pilot, in line with PoliChat [5] and unlike the Wikipedia results "
    "of DPR [2]. The pilot is too small to settle RQ1, which is why the full study uses 300 questions and a "
    "significance test.",
]
if dense_ru_raw:
    dense_en = find("Dense", "en", True)
    hyb_en = find("Hybrid", "en", True)
    obs.append(f"The small multilingual dense model (paraphrase-multilingual-MiniLM-L12-v2, used without "
               f"fine-tuning) was clearly weaker: MRR@10 {dense_en['MRR@10']:.2f} on English and only "
               f"{dense_ru_raw['MRR@10']:.2f} on raw Roman Urdu. One reason is length: the model reads at most "
               f"128 tokens, and 46 of the 174 clauses are longer, so their endings are ignored. Because the "
               f"dense ranking was weak, adding it to the hybrid lowered English MRR@10 from "
               f"{bm_en['MRR@10']:.2f} (BM25) to {hyb_en['MRR@10']:.2f}. RQ1 therefore needs stronger "
               f"multilingual models with longer input limits before dense retrieval can be judged fairly.")
obs.append(f"The refusal check answered {ref['en']['answerable_answered']} answerable English questions and "
           f"refused {ref['en']['unanswerable_refused']} unanswerable ones ({ref['ru']['unanswerable_refused']} "
           f"in Roman Urdu). It failed on questions such as \"When will the Fall 2026 semester start?\", whose "
           f"words all appear in the regulations even though the answer does not. Word-level checks are not "
           f"enough, which agrees with the negative rejection findings of [4] and motivates RQ2.")
para("The main observations are:")
bullets(obs)
para("These numbers come from a small test set that we wrote ourselves, so they show feasibility, not "
     "final results.")

heading("5.9 Ethical considerations", 2)
para("The regulations are public documents and the test questions contain no personal data. The assistant "
     "is presented as a guide, not an authority: every answer shows its source clause and the refusal "
     "message directs students to their department or the Registrar office. If two notifications "
     "disagree, the assistant must say so rather than choose silently.")

# ---------------------------------------------------------------- 6. contributions
heading("6. Expected contributions and limitations", 1)
heading("6.1 Expected contributions", 2)
bullets([
    "For NED students: a way to get correct, cited answers about attendance, probation, withdrawal and "
    "examination rules in the language they actually type, at any time.",
    "For NED administration: fewer repeated queries to department offices and the Registrar, and a list of "
    "frequently asked topics that can guide clearer notifications. The conflicting attendance clauses we "
    "found are an example of an issue the system brings to light.",
    "For research: to our knowledge the first evaluation of RAG for university regulations with Roman Urdu "
    "questions, a parallel English and Roman Urdu test set for the education domain, and evidence on "
    "which retriever and which normalisation approach work for this kind of document.",
    "For other Pakistani universities: a method that can be reused with their own regulations by "
    "replacing the documents in the index.",
])
heading("6.2 Limitations", 2)
bullets([
    "Only two NED documents are covered. Department-level notices, fee schedules and postgraduate rules "
    "are not included.",
    "The test questions are written by students in our group, not collected from real student use, so "
    "they may not cover every way students ask.",
    "The Roman Urdu lexicon is built by hand and will miss some spellings and slang.",
    "LLM-based answers depend on the model and its version. Results from one model may not hold for "
    "another, and commercial APIs have a cost.",
    "When rules are updated the index must be rebuilt, and the assistant cannot decide which of two "
    "conflicting notifications applies; only the university can.",
])

# ---------------------------------------------------------------- 7. conclusion
heading("7. Conclusion", 1)
para("NED students need reliable answers about rules that directly affect their studies, and general "
     "chatbots cannot provide them. RAG grounds answers in the official documents and lets students check "
     "the source. Our review of eight studies shows that RAG chatbots for university regulations have been "
     "tested in Polish, Spanish and Indonesian but not with Roman Urdu or code-mixed questions, that the "
     "best retriever for regulations is still disputed, and that refusing out-of-scope questions is a weak "
     "point. We proposed three research questions and a methodology to answer them using NED's own "
     "regulations and a parallel English and Roman Urdu test set. The prototype shows that the design "
     "works and the pilot already gives clear signals: simple Roman Urdu normalisation closes most of the "
     "retrieval gap, keyword retrieval beats a small embedding model on formal rules, and safe refusal needs "
     "more than word matching. The full study would turn these "
     "pilot findings into tested results.")

# ---------------------------------------------------------------- references
heading("References", 1)
refs = [
    'P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W. Yih, '
    'T. Rocktäschel, S. Riedel, and D. Kiela, "Retrieval-augmented generation for knowledge-intensive NLP '
    'tasks," in *Advances in Neural Information Processing Systems 33 (NeurIPS 2020)*, 2020, pp. 9459-9474.',
    'V. Karpukhin, B. Oguz, S. Min, P. Lewis, L. Wu, S. Edunov, D. Chen, and W. Yih, "Dense passage '
    'retrieval for open-domain question answering," in *Proc. 2020 Conf. Empirical Methods in Natural '
    'Language Processing (EMNLP)*, 2020, pp. 6769-6781, doi: 10.18653/v1/2020.emnlp-main.550.',
    'K. Shuster, S. Poff, M. Chen, D. Kiela, and J. Weston, "Retrieval augmentation reduces hallucination '
    'in conversation," in *Findings of the Association for Computational Linguistics: EMNLP 2021*, 2021, '
    'pp. 3784-3803, doi: 10.18653/v1/2021.findings-emnlp.320.',
    'J. Chen, H. Lin, X. Han, and L. Sun, "Benchmarking large language models in retrieval-augmented '
    'generation," in *Proc. AAAI Conf. Artificial Intelligence*, vol. 38, no. 16, 2024, pp. 17754-17762, '
    'doi: 10.1609/aaai.v38i16.29728.',
    'K. Wojtasik, A. Berdowski, I. Okulska, and M. Piasecki, "PoliChat: Retrieval augmented generation on '
    'university documents and regulations," in *Computational Science - ICCS 2025 Workshops*, Lecture '
    'Notes in Computer Science. Cham, Switzerland: Springer, 2025, pp. 273-288, '
    'doi: 10.1007/978-3-031-97570-7_21.',
    'J. P. Guadalupe Andrade, B. Topon Visarrea, and C. Iza, "An academic chatbot with hybrid retrieval and '
    'local large language models," *Revista Tecnológica ESPOL*, vol. 38, no. E1, pp. 50-70, 2026, '
    'doi: 10.37815/rte.v38ne1.1595.',
    'S. Suherwin, M. Zainuddin, and R. Rachmat, "Comparing FAQ-based and retrieval-augmented generation '
    'chatbots for academic service question answering," *G-Tech: Jurnal Teknologi Terapan*, vol. 10, '
    'no. 3, pp. 1093-1105, 2026, doi: 10.70609/g-tech.v10i3.10019.',
    'U. Butt, S. Varanasi, and G. Neumann, "Roman Urdu as a low-resource language: Building the first IR '
    'dataset and baseline," in *Proc. First Workshop on Advancing NLP for Low-Resource Languages '
    '(LowResNLP)*, 2025, pp. 82-87, doi: 10.26615/978-954-452-100-4-009.',
    'Z. Ji, N. Lee, R. Frieske, T. Yu, D. Su, Y. Xu, E. Ishii, Y. J. Bang, A. Madotto, and P. Fung, '
    '"Survey of hallucination in natural language generation," *ACM Computing Surveys*, vol. 55, no. 12, '
    'pp. 1-38, 2023, doi: 10.1145/3571730.',
    'S. Es, J. James, L. Espinosa Anke, and S. Schockaert, "RAGAs: Automated evaluation of retrieval '
    'augmented generation," in *Proc. 18th Conf. European Chapter of the Association for Computational '
    'Linguistics: System Demonstrations*, 2024, pp. 150-158, doi: 10.18653/v1/2024.eacl-demo.16.',
    'K. Mehmood, D. Essam, K. Shafi, and M. K. Malik, "Sentiment analysis for a resource poor '
    'language - Roman Urdu," *ACM Trans. Asian and Low-Resource Language Information Processing*, vol. 19, '
    'no. 1, pp. 1-15, 2019, doi: 10.1145/3329709.',
    'S. Robertson and H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," *Foundations '
    'and Trends in Information Retrieval*, 2009, doi: 10.1561/1500000019.',
    'N. Reimers and I. Gurevych, "Sentence-BERT: Sentence embeddings using Siamese BERT-networks," in '
    '*Proc. 2019 Conf. Empirical Methods in Natural Language Processing and 9th Int. Joint Conf. Natural '
    'Language Processing (EMNLP-IJCNLP)*, Hong Kong, China, 2019, doi: 10.18653/v1/D19-1410.',
    'G. V. Cormack, C. L. A. Clarke, and S. Buettcher, "Reciprocal rank fusion outperforms Condorcet and '
    'individual rank learning methods," in *Proc. 32nd Int. ACM SIGIR Conf. Research and Development in '
    'Information Retrieval*, 2009, pp. 758-759, doi: 10.1145/1571941.1572114.',
    'NED University of Engineering and Technology, "Regulations for the semester system of admission, '
    'studies and examinations (revised), Notification No. Acad/34(88)/4155," Karachi, Jan. 13, 2025. '
    '[Online]. Available: https://reg.neduet.edu.pk/sites/default/files/Registrar/Regulations/Revised_Notification-4155.pdf',
    'NED University of Engineering and Technology, "Examinations regulations (semester system) 2024, '
    'Notification No. Acad/34(86)/56434," Karachi, Jun. 26, 2024. [Online]. Available: '
    'https://reg.neduet.edu.pk/sites/default/files/Registrar/Regulations/Notification-Exam%20Regulations.pdf',
]
for i, ref_text in enumerate(refs, start=1):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.first_line_indent = Cm(-1.0)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(f"[{i}]\t")
    r.font.size = Pt(10.5)
    add_rich(p, ref_text, size=10.5)

# ---------------------------------------------------------------- appendices
page_break()
heading("Appendix A. Sample pilot questions", 1)
qdata = json.loads((HERE.parent / "demo" / "eval_questions.json").read_text(encoding="utf-8"))
sample_ids = {1, 4, 10, 13, 14, 17, 21, 23}
rows = [[str(p["id"]), p["en"], "*" + p["ru"] + "*"] for p in qdata["pairs"] if p["id"] in sample_ids]
rows += [[u["id"], u["en"], "*" + u["ru"] + "*"] for u in qdata["unanswerable"][:3]]
table(["No.", "English question", "Roman Urdu version"], rows, [1.3, 7.3, 7.4], font_size=9)
caption("Table A1. Sample of the pilot test set (U = unanswerable from the regulations)")

heading("Appendix B. Prototype", 1)
para("The prototype source code is submitted with this report in the folder demo. It contains "
     "build_index.py (PDF to clause chunks), rag.py (normalisation, retrievers, refusal check and answer "
     "generation), app.py (Streamlit interface), eval_questions.json and evaluate.py (pilot evaluation). "
     "It runs with: pip install -r requirements.txt, then python build_index.py, then streamlit run app.py. "
     "A second version, ui/NED_Rules_Assistant.html, is a single-file website that presents the whole study (problem, an interactive explanation of each RAG step, research questions, pilot results and literature) and contains the assistant, with the same normalisation, BM25, "
     "fuzzy and hybrid retrieval, refusal check and citations written in JavaScript. It opens in any browser "
     "and works offline, without Python. On the 60 pilot questions it gives the same BM25 results as the "
     "Python version.")

heading("Appendix C. Contribution of group members", 1)
table(["Member", "Main responsibility", "Shared work"], [
    ["Shaikh Muhammad Zain", "Problem statement, RAG foundations [1]-[4], research gap",
     "Test questions, report review, presentation"],
    ["Syed Mohammad Huzaifa", "Regulation chatbot studies [5]-[7], methodology and evaluation design",
     "Test questions, report review, presentation"],
    ["Muhammad Maaz ur Rehman", "Roman Urdu work [8], [11], prototype and pilot evaluation",
     "Test questions, report review, presentation"],
], [5.0, 6.2, 4.8], font_size=9)
caption("Table C1. Division of work (all members reviewed the full study)")

add_page_number_footer(doc.sections[0])
doc.save(OUT)
print(f"Saved {OUT.name}")
