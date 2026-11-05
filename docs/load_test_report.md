# Load Test Report

Generated: 2026-11-01 20:02

Each run starts its own servers on free local ports with temporary storage,
so the real data is never touched.

## Results

| Component | Operations | Concurrency | Errors | Throughput (ops/s) | Mean ms | p50 ms | p95 ms | Max ms |
|---|---|---|---|---|---|---|---|---|
| Administrator confirmation (create and approve) | 50 | 10 | 0 | 11.0 | 889.3 | 845.3 | 1439.4 | 1454.3 |
| MCP server recording | 50 | 10 | 0 | 11.5 | 809.0 | 853.2 | 998.5 | 1021.5 |
| Chatbot dialogue | 9 | 3 | 0 | 0.48 | 5973.4 | 4458.9 | 9558.5 | 9558.5 |

## Integrity checks

- Administrator confirmation (create and approve): approved requests stored: 50 of 50
- Administrator confirmation (create and approve): result consistent
- MCP server recording: lines written: 50 of 50
- MCP server recording: unique lines: 50 of 50
- MCP server recording: well formed (4 columns): yes
- MCP server recording: repeated bookings ignored: 10 of 10
- MCP server recording: result consistent
- Chatbot dialogue: concurrent conversations: 3
- Chatbot dialogue: result consistent
