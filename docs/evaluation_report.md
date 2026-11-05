# Evaluation Report

Generated: 2026-11-05 19:22

## Configuration

- Embedding model: sentence-transformers/all-MiniLM-L6-v2
- Chunk size / overlap: 300 / 50
- LLM deployment: gpt-5-mini-2025-08-07
- Retrieval questions: 34

## Retrieval quality

| K | Precision@K | Recall@K | Hit@K |
|---|---|---|---|
| 1 | 0.88 | 0.53 | 0.88 |
| 2 | 0.76 | 0.73 | 0.97 |
| 3 | 0.66 | 0.82 | 1.00 |

MRR: 0.94

Precision counts chunks, Recall and Hit count source documents.
Recall@K is strict: it needs every document that holds the answer. Several
documents repeat the same fact, and K chunks can cover at most K documents, so
Recall@K stays below 1.0 by design. Hit@K asks the practical question: is at
least one document that holds the answer among the top K?

Every question found at least one relevant document in the top 3.

## Answer accuracy (end to end)

Passed 18 of 18 runs (100%).

## Latency (milliseconds)

| Component | Runs | Mean | p50 | p95 | Max |
|---|---|---|---|---|---|
| Retrieval (embedding + Chroma) | 34 | 18.0 | 15.4 | 42.6 | 46.8 |
| Input guardrail (Presidio) | 40 | 5.9 | 5.7 | 7.1 | 7.5 |
| SQL lookup tools | 60 | 0.6 | 0.5 | 1.2 | 3.0 |
| Full chatbot reply (guardrails + agent + LLM) | 18 | 6091.8 | 5606.2 | 9418.2 | 9418.2 |
