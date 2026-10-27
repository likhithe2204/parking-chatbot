# Evaluation Report

Generated: 2026-10-27 17:32

## Configuration

- Embedding model: sentence-transformers/all-MiniLM-L6-v2
- Chunk size / overlap: 300 / 50
- LLM deployment: gpt-5-mini-2025-08-07
- Retrieval questions: 13

## Retrieval quality

| K | Precision@K | Recall@K |
|---|---|---|
| 1 | 0.92 | 0.85 |
| 2 | 0.62 | 0.92 |
| 3 | 0.44 | 1.00 |

MRR: 0.95

Precision counts chunks, Recall counts source documents. The knowledge base is
small (a few chunks per document), so Precision@K is naturally lower than Recall@K.

## Answer accuracy (end to end)

Passed 16 of 16 runs (100%).

## Latency (milliseconds)

| Component | Runs | Mean | p50 | p95 | Max |
|---|---|---|---|---|---|
| Retrieval (embedding + Chroma) | 13 | 8.1 | 8.0 | 10.3 | 10.3 |
| Input guardrail (Presidio) | 40 | 2.7 | 2.4 | 4.3 | 6.2 |
| SQL lookup tools | 60 | 0.2 | 0.2 | 0.5 | 1.0 |
| Full chatbot reply (guardrails + agent + LLM) | 16 | 6243.5 | 6166.2 | 9619.5 | 9619.5 |
