// Builds the CCP presentation (PowerPoint) for the NED Rules Assistant RAG study.
// Run from the folder that has pptxgenjs installed:  node make_slides.js <path-to-report-folder>
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const REPORT = process.argv[2] || __dirname;
const RESULTS = JSON.parse(fs.readFileSync(path.join(REPORT, "..", "demo", "results.json"), "utf8"));
const SKILL = process.env.PPTX_SKILL;
const { applyTheme } = require(path.join(SKILL, "scripts", "apply_theme.js"));

const THEME = {
  name: "NED Rules",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "15232B", lt1: "FFFFFF", dk2: "0B3C49", lt2: "EAF2F1",
    accent1: "0B3C49", accent2: "F2A541", accent3: "2E8A7E", accent4: "C8553D",
    accent5: "7FA7A0", accent6: "51627A", hlink: "2E8A7E", folHlink: "51627A",
  },
};
const HEX = THEME.colors;

async function icon(Comp, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
  pres.title = "Grounded question answering over NED academic regulations";
  pres.author = "Shaikh Muhammad Zain, Syed Mohammad Huzaifa, Muhammad Maaz ur Rehman";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  // ---------- layouts ----------
  pres.defineSlideMaster({
    title: "DARK",
    background: { color: C.text2 },
    objects: [],
  });
  pres.defineSlideMaster({
    title: "CONTENT",
    background: { color: C.background1 },
    margin: [0.5, 0.6, 0.5, 0.6],
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.85,
        fontFace: THEME.headFontFace, fontSize: 32, bold: true, color: C.text2, valign: "middle", margin: 0 },
        text: "" } },
      { text: { text: "NLP CCP  |  NED University, Dept. of CSIT", options: { x: 0.6, y: 7.05, w: 6, h: 0.3,
        fontSize: 10, color: C.accent6, margin: 0 } } },
    ],
    slideNumber: { x: 12.2, y: 7.05, w: 0.5, h: 0.3, fontSize: 10, color: C.accent6, align: "right" },
  });

  const I = {
    search: await icon(fa.FaSearch, HEX.lt1), book: await icon(fa.FaBookOpen, HEX.lt1),
    quote: await icon(fa.FaQuoteRight, HEX.lt1), q: await icon(fa.FaQuestion, HEX.lt1),
    lang: await icon(fa.FaLanguage, HEX.lt1), shield: await icon(fa.FaShieldAlt, HEX.lt1),
    scale: await icon(fa.FaBalanceScale, HEX.lt1), layers: await icon(fa.FaLayerGroup, HEX.lt1),
    user: await icon(fa.FaUserGraduate, HEX.lt1), robot: await icon(fa.FaRobot, HEX.lt1),
    check: await icon(fa.FaCheckCircle, HEX.accent3), times: await icon(fa.FaTimesCircle, HEX.accent4),
    file: await icon(fa.FaFileAlt, HEX.lt1), uni: await icon(fa.FaUniversity, HEX.lt1),
    flask: await icon(fa.FaFlask, HEX.lt1), warn: await icon(fa.FaExclamationTriangle, HEX.dk2),
  };

  const iconCircle = (slide, img, x, y, d = 0.7, fill = C.accent1) => {
    slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { type: "none" }, objectName: "icon circle" });
    const pad = d * 0.24;
    slide.addImage({ data: img, x: x + pad, y: y + pad, w: d - 2 * pad, h: d - 2 * pad, objectName: "icon" });
  };
  const card = (slide, x, y, w, h, fill = C.background2) =>
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill },
      line: { type: "none" }, objectName: "card" });
  const text = (slide, t, o) => slide.addText(t, { isTextBox: true, margin: 0, valign: "top", fontSize: 15, color: C.text1, ...o });

  // ===== 1. Title =====
  pres.addSection({ title: "Introduction" });
  let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Introduction" });
  text(s, "NLP Complex Computing Problem  |  Research area: Retrieval-Augmented Generation", { x: 0.8, y: 0.7, w: 11.5, h: 0.4, fontSize: 14, color: C.accent2 });
  text(s, "Grounded question answering over university academic regulations", { x: 0.8, y: 1.5, w: 11.5, h: 1.6, fontFace: THEME.headFontFace, fontSize: 40, bold: true, color: C.background1 });
  text(s, "A RAG study for English and Roman Urdu student questions at NED University", { x: 0.8, y: 3.15, w: 11.5, h: 0.6, fontSize: 20, color: C.accent5 });
  text(s, [
    { text: "Shaikh Muhammad Zain", options: { breakLine: true } },
    { text: "Syed Mohammad Huzaifa", options: { breakLine: true } },
    { text: "Muhammad Maaz ur Rehman" },
  ], { x: 0.8, y: 4.5, w: 6, h: 1.2, fontSize: 16, color: C.background1, paraSpaceAfter: 4 });
  text(s, [
    { text: "Submitted to Dr. Muhammad Imran", options: { breakLine: true } },
    { text: "Department of CSIT, NED University of Engineering and Technology", options: { breakLine: true } },
    { text: "BS Artificial Intelligence  |  15 November 2026" },
  ], { x: 0.8, y: 5.9, w: 9, h: 1.0, fontSize: 13, color: C.accent5, paraSpaceAfter: 3 });
  s.addNotes("Presenter: Zain. Introduce the group and the topic in one line: we studied how a RAG chatbot can answer NED rule questions correctly, with a source, in English and in Roman Urdu.");

  // ===== 2. Problem =====
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
  s.addText("Students ask rule questions, chatbots guess the answers", { placeholder: "title" });
  card(s, 0.6, 1.5, 6.3, 5.2, C.background2);
  iconCircle(s, I.user, 0.9, 1.8, 0.6, C.accent3);
  text(s, "\"Final exam dene ke liye kam az kam kitni hazri chahiye?\"", { x: 1.7, y: 1.8, w: 5.0, h: 0.8, fontSize: 16, italic: true });
  iconCircle(s, I.robot, 0.9, 2.95, 0.6, C.accent4);
  text(s, "General chatbot: \"Usually 60% to 75%, it depends on the university.\"", { x: 1.7, y: 2.95, w: 5.0, h: 0.8, fontSize: 15 });
  text(s, "No source, possibly wrong, not about NED.", { x: 1.7, y: 3.7, w: 5.0, h: 0.4, fontSize: 13, color: C.accent4, bold: true });
  iconCircle(s, I.book, 0.9, 4.45, 0.6, C.accent1);
  text(s, "NED rule: at least 75% attendance per course; condonation possible between 65% and 75% aggregate with evidence [ADM 7.5].", { x: 1.7, y: 4.45, w: 5.0, h: 1.3, fontSize: 15 });
  text(s, "This is the answer a student needs, with the clause to check.", { x: 1.7, y: 5.8, w: 5.0, h: 0.6, fontSize: 13, color: C.accent3, bold: true });
  const stats = [["34", "pages of official rules"], ["150+", "numbered clauses"], ["2", "notifications (2024, 2025)"]];
  stats.forEach(([n, l], i) => {
    text(s, n, { x: 7.5, y: 1.55 + i * 1.75, w: 2.3, h: 1.0, fontFace: THEME.headFontFace, fontSize: 54, bold: true, color: C.accent1 });
    text(s, l, { x: 9.8, y: 1.85 + i * 1.75, w: 3.0, h: 0.6, fontSize: 17, color: C.text1 });
  });
  s.addNotes("Presenter: Zain. Students need exact answers on attendance, probation, withdrawal. The rules exist but are long and formal. General chatbots answer from memory, with no source, and they do not know NED's current notifications. This is the hallucination problem.");

  // ===== 3. What is RAG =====
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Introduction" });
  s.addText("RAG works like an open-book exam", { placeholder: "title" });
  text(s, "Retrieval-augmented generation [1]: first find the right page in the rule book, then answer only from that page, and show where the answer came from.", { x: 0.6, y: 1.35, w: 12.1, h: 0.8, fontSize: 18 });
  const steps = [
    [I.search, "1. Search", "The retriever finds the clauses that match the question (BM25 keywords or embeddings)."],
    [I.book, "2. Read", "The top clauses are given to the language model as the only allowed source."],
    [I.quote, "3. Answer with citation", "The model answers in 2 to 5 sentences and cites the clause, e.g. [EXM 3.5]. If the rules do not cover it, it says so."],
  ];
  steps.forEach(([img, h, b], i) => {
    const x = 0.6 + i * 4.1;
    card(s, x, 2.5, 3.8, 3.9);
    iconCircle(s, img, x + 0.35, 2.8, 0.8);
    text(s, h, { x: x + 0.35, y: 3.8, w: 3.2, h: 0.5, fontFace: THEME.headFontFace, fontSize: 20, bold: true, color: C.text2 });
    text(s, b, { x: x + 0.35, y: 4.4, w: 3.2, h: 1.9, fontSize: 17 });
    if (i < 2) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 3.82, y: 4.2, w: 0.26, h: 0.4, fill: { color: C.accent2 }, line: { type: "none" }, objectName: "arrow" });
  });
  text(s, "Because answers are tied to the documents, updating the rules only needs a new index, not retraining.", { x: 0.6, y: 6.55, w: 12.1, h: 0.4, fontSize: 14, color: C.accent6, italic: true });
  s.addNotes("Presenter: Zain. Explain with the open-book exam analogy. Normal chatbot = closed-book exam from memory. RAG = open book: search, read, answer with page number. Lewis et al. 2020 introduced RAG.");

  // ===== 4. Objectives and RQs =====
  pres.addSection({ title: "Research design" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Research design" });
  s.addText("Three research questions", { placeholder: "title" });
  const rqs = [
    [I.layers, "RQ1  Which retriever?", "BM25 keywords, dense multilingual embeddings or a hybrid: which finds the correct NED clause most often?"],
    [I.shield, "RQ2  Fewer wrong answers?", "How much does grounding reduce wrong and unsupported answers compared with the same LLM without retrieval, and can it refuse out-of-scope questions?"],
    [I.lang, "RQ3  Roman Urdu?", "How much does quality drop for Roman Urdu questions, and how much can a light normalisation step recover?"],
  ];
  rqs.forEach(([img, h, b], i) => {
    const y = 1.45 + i * 1.8;
    card(s, 0.6, y, 12.1, 1.6);
    iconCircle(s, img, 0.9, y + 0.4, 0.8, i === 2 ? C.accent3 : C.accent1);
    text(s, h, { x: 2.0, y: y + 0.25, w: 10.4, h: 0.5, fontFace: THEME.headFontFace, fontSize: 21, bold: true, color: C.text2 });
    text(s, b, { x: 2.0, y: y + 0.78, w: 10.4, h: 0.75, fontSize: 16 });
  });
  s.addNotes("Presenter: Zain. Our objectives: review the literature, find the gap, design a method, and test feasibility with a prototype. Each RQ comes directly from a gap we found, as the next slides show.");

  // ===== 5. Literature groups =====
  pres.addSection({ title: "Literature" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Literature" });
  s.addText("We reviewed eight peer-reviewed studies in four groups", { placeholder: "title" });
  const groups = [
    ["RAG foundations", "[1] Lewis et al., NeurIPS 2020: RAG beats memory-only models\n[2] Karpukhin et al., EMNLP 2020: dense retrieval beats BM25 on Wikipedia"],
    ["Hallucination and noise", "[3] Shuster et al., Findings EMNLP 2021: retrieval reduces hallucination\n[4] Chen et al., AAAI 2024: LLMs weak at rejecting unanswerable questions"],
    ["RAG for university rules", "[5] PoliChat, Poland, ICCS 2025: BM25 beat dense on long rules\n[6] Ecuador, Rev. Tecnol. ESPOL 2026: hybrid; users trusted it less than scores\n[7] Indonesia, G-Tech 2026: RAG 88% vs FAQ 68% accuracy"],
    ["Roman Urdu retrieval", "[8] Butt et al., LowResNLP 2025: first Roman Urdu IR dataset; no fixed spelling, code-mixing"],
  ];
  groups.forEach(([h, b], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.45 + Math.floor(i / 2) * 2.75;
    card(s, x, y, 5.95, 2.55);
    text(s, h, { x: x + 0.3, y: y + 0.22, w: 5.4, h: 0.45, fontFace: THEME.headFontFace, fontSize: 19, bold: true, color: C.accent3 });
    text(s, b.split("\n").map((t, k, a) => ({ text: t, options: { bullet: true, breakLine: k < a.length - 1 } })),
      { x: x + 0.3, y: y + 0.75, w: 5.4, h: 1.7, fontSize: 16, paraSpaceAfter: 6 });
  });
  s.addNotes("Presenter: Huzaifa. Walk through the four groups. Stress that all eight are peer reviewed and every reference has a DOI in the report. The important papers for our gap are 5, 6, 7 (rule chatbots in other languages) and 8 (Roman Urdu).");

  // ===== 6. Comparison table =====
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Literature" });
  s.addText("Comparison of existing studies", { placeholder: "title" });
  const hdr = (t) => ({ text: t, options: { bold: true, color: HEX.lt1, fill: { color: HEX.dk2 } } });
  const rows = [[hdr("Study"), hdr("Language"), hdr("Main finding"), hdr("What it does not cover")],
    ["[1] Lewis 2020", "English", "RAG more factual than memory-only", "Refusal, citations"],
    ["[2] Karpukhin 2020", "English", "Dense beats BM25 (Wikipedia)", "Needs in-domain training data"],
    ["[3] Shuster 2021", "English", "Retrieval reduces hallucination", "Institutional documents"],
    ["[4] Chen 2024", "English, Chinese", "Weak negative rejection", "Regulations, romanised input"],
    ["[5] Wojtasik 2025", "Polish", "BM25 beat dense on long rules", "Informal or code-mixed questions"],
    ["[6] Guadalupe Andrade 2026", "Spanish", "Faithfulness 0.97, user trust 57.9%", "Other languages, refusal"],
    ["[7] Suherwin 2026", "Indonesian", "RAG 88.33% vs FAQ 68.33%", "Stronger retrieval baselines"],
    ["[8] Butt 2025", "Roman Urdu", "MRR@10 0.19 vs 0.08 lexical", "Domain documents, answers"],
  ];
  s.addTable(rows, { x: 0.6, y: 1.4, w: 12.1, colW: [3.0, 2.1, 3.6, 3.4], fontSize: 13, fontFace: THEME.bodyFontFace,
    color: HEX.dk1, border: { type: "solid", pt: 0.5, color: "C9D6D4" }, fill: { color: HEX.lt1 }, rowH: 0.5, valign: "middle", margin: 0.06 });
  s.addNotes("Presenter: Huzaifa. Read the last column: each study leaves out something we need. No study covers university rules plus Roman Urdu questions together. Full table with method details is Table 1 in the report.");

  // ===== 7. Gap =====
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Literature" });
  s.addText("The research gap", { placeholder: "title" });
  const gaps = [
    [I.lang, "Language", "Rule chatbots tested only in Polish, Spanish, Indonesian [5-7]. Roman Urdu IR exists only for web data [8]. No study tests Roman Urdu questions on university rules.", "RQ3"],
    [I.layers, "Retriever", "Dense won on Wikipedia [2], BM25 won on Polish rules [5], hybrid used in Spanish [6]. Results conflict.", "RQ1"],
    [I.shield, "Refusal and trust", "LLMs rarely reject unanswerable questions [4]; users trusted the Spanish bot far less than its scores [6].", "RQ2"],
    [I.scale, "Conflicting rules", "NED condonation: 65-75% in ADM 7.5 (2025) but 70-75% in EXM 3.5 (2024). No reviewed study handles this.", "RQ2"],
  ];
  gaps.forEach(([img, h, b, rq], i) => {
    const x = 0.6 + (i % 2) * 6.15, y = 1.45 + Math.floor(i / 2) * 2.75;
    card(s, x, y, 5.95, 2.55);
    iconCircle(s, img, x + 0.3, y + 0.3, 0.7, i === 3 ? C.accent4 : C.accent1);
    text(s, h, { x: x + 1.2, y: y + 0.38, w: 3.6, h: 0.5, fontFace: THEME.headFontFace, fontSize: 19, bold: true, color: C.text2 });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 4.85, y: y + 0.38, w: 0.85, h: 0.42, rectRadius: 0.08, fill: { color: C.accent2 }, line: { type: "none" }, objectName: "rq tag" });
    text(s, rq, { x: x + 4.85, y: y + 0.38, w: 0.85, h: 0.42, fontSize: 13, bold: true, align: "center", valign: "middle", color: C.text1 });
    text(s, b, { x: x + 0.3, y: y + 1.05, w: 5.4, h: 1.4, fontSize: 16.5 });
  });
  s.addNotes("Presenter: Huzaifa. Each gap is backed by the papers, not by opinion. Point out the fourth gap: we found it ourselves while reading NED's two notifications, they give different attendance condonation ranges.");

  // ===== 8. Methodology pipeline =====
  pres.addSection({ title: "Methodology" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Methodology" });
  s.addText("Proposed methodology", { placeholder: "title" });
  s.addImage({ path: path.join(REPORT, "pipeline.png"), x: 0.9, y: 1.35, w: 11.5, h: 4.75, objectName: "pipeline diagram" });
  text(s, "Clause-level chunks give exact citations. Each stage is measured separately, so an error can be traced to retrieval or to generation.", { x: 0.6, y: 6.3, w: 12.1, h: 0.5, fontSize: 15, color: C.accent6, italic: true });
  s.addNotes("Presenter: Huzaifa. Indexing happens once: PDFs, split by clause number, three indexes. Per question: Roman Urdu normalisation, retrieval, grounded answer that cites or refuses. Then evaluation.");

  // ===== 9. Data and evaluation =====
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Methodology" });
  s.addText("Dataset and evaluation measures", { placeholder: "title" });
  card(s, 0.6, 1.45, 5.9, 5.3);
  iconCircle(s, I.file, 0.9, 1.7, 0.7, C.accent3);
  text(s, "NED-RulesQA test set", { x: 1.8, y: 1.82, w: 4.5, h: 0.5, fontFace: THEME.headFontFace, fontSize: 20, bold: true, color: C.text2 });
  text(s, [
    "Knowledge base: NED Admission & Studies Regulations (2025) and Examinations Regulations (2024)",
    "150 questions, each in English and Roman Urdu (300 total)",
    "About 20% unanswerable (e.g. hostel fees) to test refusal",
    "Gold clause ids labelled by two members; agreement with Cohen's kappa",
  ].map((t, k, a) => ({ text: t, options: { bullet: true, breakLine: k < a.length - 1 } })),
  { x: 0.9, y: 2.65, w: 5.3, h: 3.9, fontSize: 18, paraSpaceAfter: 12 });
  card(s, 6.8, 1.45, 5.9, 5.3);
  iconCircle(s, I.flask, 7.1, 1.7, 0.7, C.accent1);
  text(s, "What we measure", { x: 8.0, y: 1.82, w: 4.5, h: 0.5, fontFace: THEME.headFontFace, fontSize: 20, bold: true, color: C.text2 });
  text(s, [
    "RQ1: Recall@1/3/5 and MRR@10 per retriever and language",
    "RQ2: answer correctness (human), faithfulness (RAGAS [10]), citation accuracy, refusal rate; RAG vs no-retrieval LLM, McNemar's test",
    "RQ3: drop from English to Roman Urdu, with and without normalisation",
  ].map((t, k, a) => ({ text: t, options: { bullet: true, breakLine: k < a.length - 1 } })),
  { x: 7.1, y: 2.65, w: 5.3, h: 3.9, fontSize: 18, paraSpaceAfter: 12 });
  s.addNotes("Presenter: Huzaifa. Recall@k: is the right clause in the top k? MRR: how high is it ranked? Faithfulness: is every claim supported by the retrieved text? Because the Spanish study found automatic scores overrate quality, we also check a sample by hand.");

  // ===== 10. Prototype =====
  pres.addSection({ title: "Prototype and pilot" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Prototype and pilot" });
  s.addText("Prototype: NED Rules Assistant", { placeholder: "title" });
  const shot = path.join(REPORT, "demo_screenshot.png");
  if (fs.existsSync(shot)) {
    s.addImage({ path: shot, x: 0.6, y: 1.4, w: 7.6, h: 5.3, sizing: { type: "contain", w: 7.6, h: 5.3 }, objectName: "demo screenshot" });
  } else {
    card(s, 0.6, 1.4, 7.6, 5.3);
    text(s, "Live demo", { x: 0.6, y: 3.7, w: 7.6, h: 0.8, fontSize: 28, bold: true, align: "center", color: C.accent6 });
  }
  text(s, [
    "Offline one-file website with guided tour, plus a Python + Streamlit version",
    "174 clause chunks from the two NED PDFs",
    "BM25, character n-gram, multilingual dense and hybrid (RRF) retrieval",
    "Roman Urdu lexicon: hazri -> attendance, nakal -> unfair means",
    "Claude writes the answer with clause citations; offline mode shows the best sentences",
    "Refuses when the question's words are not in the rules; warns when two notifications match",
  ].map((t, k, a) => ({ text: t, options: { bullet: true, breakLine: k < a.length - 1 } })),
  { x: 8.5, y: 1.45, w: 4.2, h: 5.3, fontSize: 16, paraSpaceAfter: 8 });
  s.addNotes("Presenter: Maaz. Switch to the live demo here: streamlit run app.py. Ask the Roman Urdu attendance question, then the probation question, then the hostel fee question to show refusal. Open 'How the question was processed' to show the Roman Urdu mapping.");

  // ===== 11. Pilot results chart =====
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Prototype and pilot" });
  s.addText("Pilot: Roman Urdu normalisation closes the gap", { placeholder: "title" });
  const find = (m, lang, lex) => RESULTS.rows.find(r => r.method.startsWith(m) && r.lang === lang && r.lexicon === lex);
  const methods = RESULTS.rows.map(r => r.method).filter((v, i, a) => a.indexOf(v) === i);
  const short = (m) => m.split(" ")[0];
  const series = [
    { name: "English", values: methods.map(m => find(short(m), "en", true)["MRR@10"]) },
    { name: "Roman Urdu, no normalisation", values: methods.map(m => find(short(m), "ru", false)["MRR@10"]) },
    { name: "Roman Urdu, with normalisation", values: methods.map(m => find(short(m), "ru", true)["MRR@10"]) },
  ].map(sr => ({ ...sr, labels: methods.map(short), values: sr.values.map(v => Math.round(v * 100) / 100) }));
  s.addChart(pres.charts.BAR, series, {
    x: 0.6, y: 1.35, w: 8.0, h: 5.4, barDir: "col", barGrouping: "clustered",
    chartColors: [HEX.dk2, HEX.accent4, HEX.accent3],
    showTitle: true, title: "MRR@10 by retriever (higher is better)", titleFontSize: 14, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 11, dataLabelColor: HEX.dk1, dataLabelFormatCode: "0.00", dataLabelFontFace: "+mn-lt",
    valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0.0", valAxisLabelColor: HEX.accent6, catAxisLabelColor: HEX.dk1,
    valAxisLabelFontFace: "+mn-lt", catAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 12, valAxisLabelFontSize: 11,
    valGridLine: { color: "DDE6E4", size: 0.5 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: "+mn-lt", legendColor: HEX.dk1,
  });
  const bmEn = find("BM25", "en", true), bmRaw = find("BM25", "ru", false), bmRu = find("BM25", "ru", true);
  const ref = RESULTS.refusal;
  const callouts = [
    [`${bmRaw["Recall@5"].toFixed(2)} -> ${bmRu["Recall@5"].toFixed(2)}`, "BM25 Recall@5 on Roman Urdu, before and after normalisation"],
    [`${bmEn["MRR@10"].toFixed(2)} vs ${find("Dense", "en", true)["MRR@10"].toFixed(2)}`, "BM25 vs small dense model, MRR@10 on English: keywords win on formal rules, as in PoliChat [5]"],
    [ref.en.unanswerable_refused, "unanswerable questions refused: word matching is not enough (RQ2)"],
  ];
  callouts.forEach(([n, l], i) => {
    text(s, n, { x: 8.95, y: 1.4 + i * 1.8, w: 3.8, h: 0.75, fontFace: THEME.headFontFace, fontSize: 34, bold: true, color: i === 2 ? C.accent4 : C.accent3 });
    text(s, l, { x: 8.95, y: 2.15 + i * 1.8, w: 3.8, h: 0.9, fontSize: 14 });
  });
  text(s, "Pilot: 25 question pairs + 5 unanswerable pairs written by the group. Shows feasibility, not final results.", { x: 0.6, y: 6.75, w: 8.0, h: 0.3, fontSize: 11, color: C.accent6, italic: true });
  s.addNotes("Presenter: Maaz. Dense bars are low: the small embedding model reads only 128 tokens and 46 of 174 clauses are longer; it also pulls the hybrid down. Red bars: Roman Urdu without help drops a lot. Green bars: after the lexicon, Roman Urdu is close to English. This early evidence answers RQ3. Refusal is still weak: a question like 'When will Fall 2026 start?' uses words that exist in the rules, so the word check lets it through. That is why RQ2 matters.");

  // ===== 12. Conflict finding =====
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Prototype and pilot" });
  s.addText("A finding from NED's own documents", { placeholder: "title" });
  card(s, 0.6, 1.5, 5.85, 3.6);
  text(s, "ADM 7.5  |  Notification 4155, 13-01-2025", { x: 0.9, y: 1.75, w: 5.3, h: 0.4, fontSize: 14, bold: true, color: C.accent6 });
  text(s, "65% to 75%", { x: 0.9, y: 2.3, w: 5.3, h: 1.0, fontFace: THEME.headFontFace, fontSize: 48, bold: true, color: C.accent1 });
  text(s, "aggregate attendance may be condoned on a case-to-case basis with documentary evidence", { x: 0.9, y: 3.45, w: 5.3, h: 1.3, fontSize: 15 });
  card(s, 6.85, 1.5, 5.85, 3.6);
  text(s, "EXM 3.5  |  Notification 56434, 26-06-2024", { x: 7.15, y: 1.75, w: 5.3, h: 0.4, fontSize: 14, bold: true, color: C.accent6 });
  text(s, "70% to 75%", { x: 7.15, y: 2.3, w: 5.3, h: 1.0, fontFace: THEME.headFontFace, fontSize: 48, bold: true, color: C.accent4 });
  text(s, "aggregate attendance may be condoned by the concerned Dean, case to case", { x: 7.15, y: 3.45, w: 5.3, h: 1.3, fontSize: 15 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.4, w: 12.1, h: 1.3, rectRadius: 0.08, fill: { color: C.accent2 }, line: { type: "none" }, objectName: "takeaway" });
  s.addImage({ data: I.warn, x: 0.9, y: 5.75, w: 0.6, h: 0.6, objectName: "warning icon" });
  text(s, "A chatbot that picks one clause silently could mislead a student. Our assistant shows both clauses with their dates and tells the student to confirm with the department.", { x: 1.75, y: 5.6, w: 10.7, h: 0.95, fontSize: 16, valign: "middle" });
  s.addNotes("Presenter: Maaz. This shows why citations matter. The two current notifications disagree on the condonation range. We did not choose for the university; the assistant flags it.");

  // ===== 13. Contributions and limitations =====
  pres.addSection({ title: "Conclusion" });
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Conclusion" });
  s.addText("Expected contributions and limitations", { placeholder: "title" });
  const contrib = [
    "Students: correct, cited answers in the language they type, any time",
    "NED offices: fewer repeated queries; unclear or conflicting rules brought to light",
    "Research: first evaluation of RAG on university rules with Roman Urdu questions, plus a parallel test set",
    "Other universities: reuse the method by swapping in their documents",
  ];
  const limits = [
    "Only two NED documents; no fee schedules or department notices",
    "Test questions written by the group, not real student logs",
    "Hand-made Roman Urdu lexicon misses some spellings",
    "LLM results depend on model and version; API cost",
  ];
  [[contrib, "Contributions", I.check, C.accent3, 0.6], [limits, "Limitations", I.times, C.accent4, 6.85]].forEach(([items, h, img, col, x]) => {
    card(s, x, 1.45, 5.85, 5.3);
    s.addImage({ data: img, x: x + 0.3, y: 1.72, w: 0.55, h: 0.55, objectName: h + " icon" });
    text(s, h, { x: x + 1.05, y: 1.75, w: 4.5, h: 0.5, fontFace: THEME.headFontFace, fontSize: 21, bold: true, color: col });
    text(s, items.map((t, k, a) => ({ text: t, options: { bullet: true, breakLine: k < a.length - 1 } })),
      { x: x + 0.3, y: 2.6, w: 5.25, h: 4.0, fontSize: 19, paraSpaceAfter: 14 });
  });
  s.addNotes("Presenter: Maaz. Be honest about limitations: small pilot, our own questions, hand-made lexicon. These are exactly what the full study would fix.");

  // ===== 14. Conclusion =====
  s = pres.addSlide({ masterName: "DARK", sectionTitle: "Conclusion" });
  text(s, "Conclusion", { x: 0.8, y: 0.7, w: 11.5, h: 0.8, fontFace: THEME.headFontFace, fontSize: 40, bold: true, color: C.background1 });
  text(s, [
    "RAG grounds answers in NED's official rules and lets students check the source",
    "Gap: no study tests rule chatbots with Roman Urdu questions; the best retriever is disputed; refusal is weak",
    "Pilot: normalisation lifts Roman Urdu retrieval close to English; BM25 beats a small embedding model; safe refusal needs more than word matching",
    "Next: build the 300-question test set and run the full comparison",
  ].map((t, k, a) => ({ text: t, options: { bullet: true, breakLine: k < a.length - 1 } })),
  { x: 0.8, y: 1.8, w: 11.5, h: 3.6, fontSize: 20, color: C.background1, paraSpaceAfter: 14 });
  text(s, "Thank you. Questions?", { x: 0.8, y: 5.8, w: 11.5, h: 0.8, fontFace: THEME.headFontFace, fontSize: 32, bold: true, color: C.accent2 });
  s.addNotes("Presenter: Zain closes. One-line summary: we found a real gap, proposed three research questions and a method, and showed with a working prototype that the method is feasible.");

  const out = path.join(REPORT, "NLP_CCP_RAG_Presentation.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("Saved " + out);
})();
