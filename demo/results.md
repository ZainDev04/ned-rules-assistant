# Pilot retrieval results

Corpus: 174 clause chunks from 2 NED regulation documents. Test set: 25 question pairs (English and Roman Urdu) + 5 unanswerable pairs.

| Retriever | Question language | Roman Urdu lexicon | Recall@1 | Recall@3 | Recall@5 | MRR@10 |
|---|---|---|---|---|---|---|
| BM25 (keywords) | English | on | 0.72 | 0.92 | 0.96 | 0.84 |
| BM25 (keywords) | Roman Urdu | on | 0.72 | 0.92 | 1.00 | 0.83 |
| BM25 (keywords) | Roman Urdu | off | 0.48 | 0.76 | 0.84 | 0.63 |
| Fuzzy (character n-grams) | English | on | 0.72 | 0.92 | 0.96 | 0.82 |
| Fuzzy (character n-grams) | Roman Urdu | on | 0.60 | 0.88 | 0.96 | 0.74 |
| Fuzzy (character n-grams) | Roman Urdu | off | 0.56 | 0.80 | 0.88 | 0.68 |
| Dense (multilingual embeddings) | English | on | 0.48 | 0.64 | 0.76 | 0.58 |
| Dense (multilingual embeddings) | Roman Urdu | on | 0.36 | 0.60 | 0.64 | 0.49 |
| Dense (multilingual embeddings) | Roman Urdu | off | 0.32 | 0.36 | 0.40 | 0.37 |
| Hybrid (RRF) | English | on | 0.64 | 0.88 | 0.88 | 0.75 |
| Hybrid (RRF) | Roman Urdu | on | 0.56 | 0.72 | 0.88 | 0.67 |
| Hybrid (RRF) | Roman Urdu | off | 0.40 | 0.68 | 0.80 | 0.56 |

## Refusal check (confidence threshold)

- English: answerable questions answered 25/25, unanswerable questions refused 3/5
- Roman Urdu: answerable questions answered 25/25, unanswerable questions refused 3/5

## Questions missed in the top 5

- BM25 (keywords), English, lexicon on: [14]
- BM25 (keywords), Roman Urdu, lexicon off: [1, 7, 17, 22]
- Fuzzy (character n-grams), English, lexicon on: [14]
- Fuzzy (character n-grams), Roman Urdu, lexicon on: [22]
- Fuzzy (character n-grams), Roman Urdu, lexicon off: [1, 7, 22]
- Dense (multilingual embeddings), English, lexicon on: [6, 17, 18, 20, 21, 22]
- Dense (multilingual embeddings), Roman Urdu, lexicon on: [1, 7, 11, 14, 15, 17, 20, 21, 22]
- Dense (multilingual embeddings), Roman Urdu, lexicon off: [1, 3, 4, 5, 7, 8, 10, 11, 14, 15, 17, 20, 21, 22, 24]
- Hybrid (RRF), English, lexicon on: [14, 17, 22]
- Hybrid (RRF), Roman Urdu, lexicon on: [20, 21, 22]
- Hybrid (RRF), Roman Urdu, lexicon off: [1, 11, 17, 21, 22]
