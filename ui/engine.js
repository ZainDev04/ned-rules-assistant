// NED Rules Assistant: the RAG retrieval engine in plain JavaScript (same logic as demo/rag.py).
// Works in the browser (inlined into the HTML page) and in Node (for testing).
(function (root) {
  "use strict";

  function makeEngine(DATA) {
    const ENG_STOP = new Set(DATA.englishStopwords);
    const RU_STOP = new Set(DATA.romanUrduStopwords);
    const LEX = DATA.lexicon;
    const NOT_COUNTED = new Set(DATA.lexiconNotCountedForDetection);
    const chunks = DATA.chunks;

    // ---------- text processing ----------
    const tokenize = (text) => (text.toLowerCase().match(/[a-z0-9]+(?:\.[0-9]+)?/g) || []);
    const SUFFIXES = ["ations", "ation", "ings", "ing", "ies", "es", "s"];
    function lightStem(w) {
      for (const s of SUFFIXES) {
        if (w.length > s.length + 3 && w.endsWith(s)) return w.slice(0, -s.length) + (s === "ies" ? "y" : "");
      }
      return w;
    }
    const contentTokens = (text) => tokenize(text).filter((t) => !ENG_STOP.has(t) && t.length > 1).map(lightStem);

    function detectRomanUrdu(q) {
      const words = tokenize(q);
      if (!words.length) return false;
      const hits = words.filter((w) => RU_STOP.has(w) || (w in LEX && !NOT_COUNTED.has(w))).length;
      return hits >= 2 || hits / words.length >= 0.25;
    }

    const PHRASES = DATA.phrases.map(([p, t]) => [new RegExp(p, "gi"), t]);
    const joinPhrases = (t) => PHRASES.reduce((acc, [re, tok]) => acc.replace(re, tok), t);

    function normaliseQuery(q, useLexicon = true) {
      const kept = [], expansions = [];
      for (const w of tokenize(useLexicon ? joinPhrases(q) : q)) {
        if (useLexicon && Object.prototype.hasOwnProperty.call(LEX, w)) {
          const eng = LEX[w];
          kept.push(eng);
          if (eng.split(" ")[0] !== w) expansions.push(`${w} → ${eng}`);
        } else if (useLexicon && RU_STOP.has(w)) {
          continue;
        } else kept.push(w);
      }
      return { query: kept.join(" "), expansions };
    }

    // ---------- BM25 ----------
    const docTokens = chunks.map((c) => contentTokens(c.text));
    const docLen = docTokens.map((t) => t.length);
    const avgdl = docLen.reduce((a, b) => a + b, 0) / docLen.length;
    const tfs = docTokens.map((toks) => { const m = new Map(); toks.forEach((t) => m.set(t, (m.get(t) || 0) + 1)); return m; });
    const df = new Map();
    docTokens.forEach((toks) => new Set(toks).forEach((t) => df.set(t, (df.get(t) || 0) + 1)));
    const N = chunks.length;
    const idf = new Map();
    df.forEach((f, w) => idf.set(w, Math.log(1 + (N - f + 0.5) / (f + 0.5))));
    const vocab = new Set(df.keys());
    const vocabList = [...vocab];

    function bm25Scores(query, k1 = 1.5, b = 0.75) {
      const q = contentTokens(query);
      return tfs.map((tf, i) => {
        const norm = k1 * (1 - b + (b * docLen[i]) / avgdl);
        let s = 0;
        for (const w of q) { const f = tf.get(w); if (f) s += idf.get(w) * (f * (k1 + 1)) / (f + norm); }
        return s;
      });
    }

    // ---------- character n-gram TF-IDF (like sklearn char_wb, ngram 3-5, sublinear tf, l2) ----------
    function charNgrams(text) {
      const grams = new Map();
      const words = text.toLowerCase().split(/\s+/).filter(Boolean);
      for (const w of words) {
        const padded = " " + w + " ";
        for (let n = 3; n <= 5; n++) {
          if (padded.length < n) continue;
          for (let i = 0; i + n <= padded.length; i++) {
            const g = padded.slice(i, i + n);
            grams.set(g, (grams.get(g) || 0) + 1);
          }
        }
      }
      return grams;
    }
    const docGrams = chunks.map((c) => charNgrams(c.text));
    const gdf = new Map();
    docGrams.forEach((g) => g.forEach((_, k) => gdf.set(k, (gdf.get(k) || 0) + 1)));
    const gidf = new Map();
    gdf.forEach((f, k) => gidf.set(k, Math.log((1 + N) / (1 + f)) + 1));
    function weigh(grams) {
      const v = new Map(); let norm = 0;
      grams.forEach((c, k) => { const w = (1 + Math.log(c)) * (gidf.get(k) || 0); if (w) { v.set(k, w); norm += w * w; } });
      norm = Math.sqrt(norm) || 1;
      v.forEach((w, k) => v.set(k, w / norm));
      return v;
    }
    const docVecs = docGrams.map(weigh);
    function fuzzyScores(query) {
      const q = weigh(charNgrams(query));
      return docVecs.map((d) => { let s = 0; q.forEach((w, k) => { const x = d.get(k); if (x) s += w * x; }); return s; });
    }

    // ---------- hybrid ----------
    function rrf(lists, k = 60) {
      const fused = new Array(N).fill(0);
      for (const scores of lists) {
        argsort(scores).forEach((idx, rank) => { fused[idx] += 1 / (k + rank + 1); });
      }
      return fused;
    }
    // stable descending sort (ties keep document order, like numpy)
    const argsort = (s) => s.map((v, i) => [v, i]).sort((a, b) => b[0] - a[0] || a[1] - b[1]).map((x) => x[1]);

    function score(question, method = "bm25", useLexicon = true) {
      const { query, expansions } = normaliseQuery(question, useLexicon);
      let s;
      if (method === "bm25") s = bm25Scores(query);
      else if (method === "fuzzy") s = fuzzyScores(query);
      else s = rrf([bm25Scores(query), fuzzyScores(query)]);
      return { scores: s, query, expansions };
    }

    // ---------- refusal check (coverage of question words in the rules) ----------
    function similarity(a, b) { // 2*LCS/(|a|+|b|), close to Python's difflib ratio for short words
      const m = a.length, n = b.length; const dp = new Array(n + 1).fill(0);
      for (let i = 1; i <= m; i++) { let prev = 0; for (let j = 1; j <= n; j++) { const tmp = dp[j]; dp[j] = a[i - 1] === b[j - 1] ? prev + 1 : Math.max(dp[j], dp[j - 1]); prev = tmp; } }
      return (2 * dp[n]) / (m + n);
    }
    function closeMatch(t) {
      for (const v of vocabList) {
        if (Math.abs(v.length - t.length) > 2) continue;
        if (similarity(t, v) >= 0.85) return true;
      }
      return false;
    }
    function coverage(question, useLexicon = true) {
      const { query } = normaliseQuery(question, useLexicon);
      const terms = [...new Set(contentTokens(query))].filter((t) => !/^\d+$/.test(t));
      if (!terms.length) return { coverage: 0, unknown: [] };
      const unknown = terms.filter((t) => !vocab.has(t) && !closeMatch(t));
      return { coverage: 1 - unknown.length / terms.length, unknown };
    }
    const isAnswerable = (q, useLexicon = true) => coverage(q, useLexicon).coverage >= 0.8;

    // ---------- answer ----------
    function overlap(qTerms, text) {
      const terms = new Set(contentTokens(text));
      let total = 0, hit = 0;
      qTerms.forEach((t) => { const w = idf.get(t) || 0; total += w; if (terms.has(t)) hit += w; });
      return hit / (total || 1);
    }

    function extractiveAnswer(question, results, romanUrdu) {
      const qTerms = new Set(contentTokens(normaliseQuery(question).query));
      const cands = [];
      results.slice(0, 3).forEach((r, rank) => {
        const parts = r.text.split(/(?<=[.;:])\s+(?=[A-Z0-9(])|\s(?=(?:[ivx]{1,4}\.|[a-h]\)|\([ivx]{1,4}\)|\([a-h]\))\s)/);
        for (let sent of parts) {
          if (!sent) continue;
          sent = sent.trim();
          if (sent.length < 25) continue;
          const sc = overlap(qTerms, sent) * (1 - 0.15 * rank);
          if (sc > 0) cands.push({ sc, sent, id: r.id });
        }
      });
      if (!cands.length) return null;
      cands.sort((a, b) => b.sc - a.sc);
      const chosen = [cands[0]];
      for (const c of cands.slice(1)) { if (c.sc >= 0.7 * cands[0].sc && c.sent !== chosen[0].sent) { chosen.push(c); break; } }
      return chosen.map((c) => ({ text: c.sent, id: c.id }));
    }

    function findConflict(question, results) {
      const qTerms = new Set(contentTokens(normaliseQuery(question).query));
      const ov = results.slice(0, 3).map((r) => [overlap(qTerms, r.text), r]);
      const best = Math.max(0, ...ov.map((x) => x[0]));
      const strong = new Set(ov.filter(([o]) => best && o >= 0.75 * best).map(([, r]) => r.doc_code));
      return strong.has("ADM") && strong.has("EXM");
    }

    function ask(question, { method = "bm25", k = 4, useLexicon = true } = {}) {
      const romanUrdu = detectRomanUrdu(question);
      const { scores, query, expansions } = score(question, method, useLexicon);
      const results = argsort(scores).slice(0, k).map((i) => ({ ...chunks[i], score: scores[i] }));
      const cov = coverage(question, useLexicon);
      const answerable = cov.coverage >= 0.8;
      const sentences = answerable ? extractiveAnswer(question, results, romanUrdu) : null;
      return {
        question, romanUrdu, query, expansions, results, coverage: cov, answerable,
        sentences, conflict: answerable && findConflict(question, results),
      };
    }

    return { ask, score, coverage, isAnswerable, normaliseQuery, detectRomanUrdu, chunks, argsort, docs: DATA.docs };
  }

  if (typeof module !== "undefined" && module.exports) module.exports = { makeEngine };
  else root.makeEngine = makeEngine;
})(typeof window !== "undefined" ? window : globalThis);
