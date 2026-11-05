# Evaluation Report

Generated: 2026-11-02 16:11

## Configuration

- Embedding model: sentence-transformers/all-MiniLM-L6-v2
- Chunk size / overlap: 300 / 50
- LLM deployment: gpt-5-mini-2025-08-07
- Retrieval questions: 13

## Retrieval quality

| K | Precision@K | Recall@K | Hit@K |
|---|---|---|---|
| 1 | 0.31 | 0.31 | 0.31 |
| 2 | 0.27 | 0.54 | 0.54 |
| 3 | 0.21 | 0.62 | 0.62 |

MRR: 0.95

Precision counts chunks, Recall and Hit count source documents.
Recall@K is strict: it needs every document that holds the answer. Several
documents repeat the same fact, and K chunks can cover at most K documents, so
Recall@K stays below 1.0 by design. Hit@K asks the practical question: is at
least one document that holds the answer among the top K?

Questions where no relevant document was found in the top 3:

- How do I reserve a parking space? -> got ['reservation_rules.md', 'about_the_facility.md', 'parking_details.md'], wanted one of ['booking_process.md']
- Can I cancel my reservation? -> got ['faq.md', 'cancellations_and_changes.md', 'cancellations_and_changes.md'], wanted one of ['booking_process.md']
- Who approves the reservation? -> got ['assistant_capabilities_and_privacy.md', 'zones_and_vehicles.md', 'reservation_rules.md'], wanted one of ['booking_process.md', 'general_info.md']
- Which zone has EV charging? -> got ['ev_charging.md', 'ev_charging.md', 'ev_charging.md'], wanted one of ['general_info.md', 'parking_details.md']
- Is there CCTV security? -> got ['security_and_safety.md', 'faq.md', 'about_the_facility.md'], wanted one of ['general_info.md']

## Answer accuracy (end to end)

Passed 18 of 18 runs (100%).

## Latency (milliseconds)

| Component | Runs | Mean | p50 | p95 | Max |
|---|---|---|---|---|---|
| Retrieval (embedding + Chroma) | 13 | 7.8 | 7.8 | 8.4 | 8.4 |
| Input guardrail (Presidio) | 40 | 2.4 | 2.3 | 2.6 | 3.7 |
| SQL lookup tools | 60 | 0.2 | 0.2 | 0.2 | 0.8 |
| Full chatbot reply (guardrails + agent + LLM) | 18 | 5600.5 | 4770.0 | 11125.2 | 11125.2 |
