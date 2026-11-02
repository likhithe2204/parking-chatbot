# Evaluation Report

Generated: 2026-11-02 11:09

## Configuration

- Embedding model: sentence-transformers/all-MiniLM-L6-v2
- Chunk size / overlap: 300 / 50
- LLM deployment: gpt-5-mini-2025-08-07
- Retrieval questions: 34

## Retrieval quality

| K | Precision@K | Recall@K |
|---|---|---|
| 1 | 0.88 | 0.53 |
| 2 | 0.76 | 0.73 |
| 3 | 0.66 | 0.82 |

MRR: 0.94

Precision counts chunks, Recall counts source documents. The knowledge base is
small (a few chunks per document), so Precision@K is naturally lower than Recall@K.

Questions where Recall@3 was below 1.0:

- Where is the parking located? -> got ['about_the_facility.md', 'location.md', 'general_info.md'], wanted ['directions_and_transport.md', 'location.md']
- How do I reserve a parking space? -> got ['reservation_rules.md', 'about_the_facility.md', 'parking_details.md'], wanted ['booking_process.md', 'reservation_rules.md']
- Can I cancel my reservation? -> got ['faq.md', 'cancellations_and_changes.md', 'cancellations_and_changes.md'], wanted ['booking_process.md', 'cancellations_and_changes.md', 'faq.md']
- Who approves the reservation? -> got ['assistant_capabilities_and_privacy.md', 'zones_and_vehicles.md', 'reservation_rules.md'], wanted ['booking_process.md', 'general_info.md', 'reservation_rules.md']
- Which zone has EV charging? -> got ['ev_charging.md', 'ev_charging.md', 'ev_charging.md'], wanted ['ev_charging.md', 'parking_details.md', 'zones_and_vehicles.md']
- Are buses allowed? -> got ['parking_details.md', 'faq.md', 'faq.md'], wanted ['faq.md', 'parking_details.md', 'zones_and_vehicles.md']
- Is there CCTV security? -> got ['security_and_safety.md', 'faq.md', 'about_the_facility.md'], wanted ['about_the_facility.md', 'general_info.md', 'security_and_safety.md']
- Is the parking monitored all day? -> got ['general_info.md', 'faq.md', 'about_the_facility.md'], wanted ['about_the_facility.md', 'general_info.md', 'security_and_safety.md']
- Can I park a two-wheeler? -> got ['faq.md', 'faq.md', 'parking_rules.md'], wanted ['faq.md', 'parking_details.md', 'zones_and_vehicles.md']
- What happens if the administrator refuses my request? -> got ['reservation_rules.md', 'assistant_capabilities_and_privacy.md', 'reservation_rules.md'], wanted ['booking_process.md', 'faq.md', 'reservation_rules.md']
- Will the assistant ask for my card number or UPI PIN? -> got ['payments.md', 'faq.md', 'faq.md'], wanted ['assistant_capabilities_and_privacy.md', 'payments.md']
- Are there security cameras and emergency exits? -> got ['security_and_safety.md', 'faq.md', 'about_the_facility.md'], wanted ['general_info.md', 'security_and_safety.md']

## Answer accuracy (end to end)

Passed 15 of 16 runs (94%).

- What time do you open on Sunday? -> 'We open at 06:00 on Sundays.'

## Latency (milliseconds)

| Component | Runs | Mean | p50 | p95 | Max |
|---|---|---|---|---|---|
| Retrieval (embedding + Chroma) | 34 | 22.4 | 21.8 | 28.7 | 33.3 |
| Input guardrail (Presidio) | 40 | 9.9 | 9.8 | 11.9 | 13.1 |
| SQL lookup tools | 60 | 1.1 | 1.0 | 1.6 | 5.0 |
| Full chatbot reply (guardrails + agent + LLM) | 16 | 5553.7 | 5022.4 | 8498.6 | 8498.6 |
