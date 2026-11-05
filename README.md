<h1 align="center">Parking Space Reservation Chatbot</h1>

<p align="center">
  An AI assistant for a parking facility. It answers questions, checks live prices and
  availability, collects reservation details, protects sensitive data, sends every booking to
  a human administrator for approval, and records approved bookings through an MCP server.
  All components run as one LangGraph workflow, on a Retrieval-Augmented Generation (RAG)
  architecture built with Python and LangChain.
</p>

<p align="center">
  <a href="https://github.com/likhithe2204/parking-chatbot/actions/workflows/ci.yml">
    <img src="https://github.com/likhithe2204/parking-chatbot/actions/workflows/ci.yml/badge.svg" alt="CI status">
  </a>
  <img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12">
  <img src="https://img.shields.io/badge/tests-235%20passed-brightgreen" alt="235 tests passed">
  <img src="https://img.shields.io/badge/LangChain-LangGraph-purple" alt="LangChain and LangGraph">
</p>

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [How It Works](#how-it-works)
4. [Knowledge Base](#knowledge-base)
5. [Stage 1 Demo](#stage-1-demo)
6. [Stage 2: Human-in-the-Loop Administrator](#stage-2-human-in-the-loop-administrator)
7. [Stage 3: MCP Server](#stage-3-mcp-server)
8. [Stage 4: LangGraph Orchestration](#stage-4-langgraph-orchestration)
9. [Setup and Deployment](#setup-and-deployment)
10. [Usage](#usage)
11. [Evaluation](#evaluation)
12. [Testing and CI](#testing-and-ci)
13. [Security](#security)
14. [Project Structure](#project-structure)
15. [Limitations](#limitations)
16. [Roadmap](#roadmap)

---

## Overview

The project was built in four stages. Each stage is tagged in Git: `stage-1`, `stage-2`, `stage-3`
and `stage-4`.

| Stage | Scope |
|---|---|
| 1 | RAG chatbot, vector database, guardrails, evaluation |
| 2 | Human-in-the-loop administrator approval |
| 3 | MCP server that records approved reservations |
| 4 | LangGraph orchestration of all components, load and integration tests |

**Presentations:** [Stage 1](docs/parking_chatbot_stage1.pptx),
[Stage 2](docs/parking_chatbot_stage2.pptx), [Stage 3](docs/parking_chatbot_stage3.pptx) and
[Stage 4](docs/parking_chatbot_stage4.pptx)

**Features**

1. Answers questions about the facility from a 17-document knowledge base.
2. Reports live data: working hours, prices and free spaces, per period.
3. Collects reservation details one field at a time and validates each answer.
4. Masks sensitive data (email, phone, card number) and blocks prompt injection.
5. Sends each reservation to a human administrator, who approves or refuses it.
6. Takes a parking space for each approved booking and writes it to a text file through a secured MCP server.
7. Tells the customer the decision in the chat as soon as it arrives.
8. Ships with evaluation, load test and integration test reports.

**Tech stack**

| Area | Choice |
|---|---|
| Language | Python 3.12 |
| Orchestration | LangGraph |
| Agents | LangChain |
| LLM | GPT via EPAM DIAL (Azure OpenAI interface) |
| Vector database | Chroma |
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) |
| Dynamic data | SQLite |
| Admin service | FastAPI, httpx |
| MCP server | MCP Python SDK (`mcp>=1.25,<2`) mounted in FastAPI |
| Guardrails | Microsoft Presidio and spaCy |
| Testing | pytest, GitHub Actions |

---

## Architecture

<p align="center">
  <img src="docs/screenshots/s4_architecture.png" alt="System architecture" width="95%">
</p>

---

## How It Works

**1. Static data goes to the vector database.**
The knowledge base is split into chunks, embedded and stored in Chroma. A question about the
facility retrieves the 3 closest chunks.

**2. Dynamic data goes to SQL.**
Working hours, prices and availability change often, so they live in SQLite and are read through
parameterized, read-only queries. Approved bookings are recorded in a `bookings` table.

**3. The agent chooses the right tool.**
The chatbot agent decides whether to search the vector database, query SQL, or start the
reservation flow.

**4. Reservations are collected and validated field by field.**
Each detail is saved in a draft the moment the customer gives it. The code accepts a detail only
if it appears in the customer's own message, so the model cannot invent values.

**5. Every booking goes to a human.**
After the customer confirms, the workflow hands the booking to the admin agent. The bot never says
a booking is confirmed until the administrator has decided.

**6. Approval takes a space and saves the booking.**
When the administrator approves, the system takes a space in the zone with the most free spaces
for that period, and the MCP server appends one line to a text file.

**7. Guardrails protect both directions.**
The input guardrail masks sensitive data and blocks prompt injection. The output guardrail masks
anything sensitive that slips into a reply.

---

## Knowledge Base

The static knowledge base lives in `data/static/` and has 17 documents.

| Topic | Documents |
|---|---|
| The facility | `general_info.md`, `about_the_facility.md`, `parking_details.md`, `zones_and_vehicles.md` |
| Getting there | `location.md`, `directions_and_transport.md` |
| Booking | `booking_process.md`, `reservation_rules.md`, `cancellations_and_changes.md` |
| On site | `parking_rules.md`, `payments.md`, `ev_charging.md`, `accessibility.md`, `security_and_safety.md` |
| The assistant | `assistant_capabilities_and_privacy.md`, `faq.md` |
| Guardrail test | `internal_staff_notes.md` |

Prices, opening hours and free spaces are deliberately not in the documents. They come from SQL, so
they are always current. Each paragraph is short and names the facility, so every chunk makes sense
on its own.

`internal_staff_notes.md` holds fake staff and customer details on purpose, to prove that the
guardrails stop private data from leaking. A real deployment would keep such a file out of the
index.

---

## Stage 1 Demo

<p align="center">
  <img src="docs/architecture.png" alt="Stage 1 flow" width="95%">
</p>

### 1. Vector database ingestion and retrieval check

<p align="center">
  <img src="docs/screenshots/01_ingestion.png" alt="Vector database ingestion" width="90%">
</p>

---

### 2. Answering information, price and availability questions

<p align="center">
  <img src="docs/screenshots/02_chat_info.png" alt="Chat answering questions" width="90%">
</p>

---

### 3. Reservation flow with validation

<p align="center">
  <img src="docs/screenshots/03_reservation_flow.png" alt="Reservation flow" width="90%">
</p>

---

### 4. Guardrails for sensitive data

<p align="center">
  <img src="docs/screenshots/04_guardrail.png" alt="Guardrails" width="90%">
</p>

---

### 5. Evaluation report

<p align="center">
  <img src="docs/screenshots/05_evaluation.png" alt="Evaluation report" width="90%">
</p>

---

### 6. Automated tests and CI

<p align="center">
  <img src="docs/screenshots/06a_tests_passed.png" alt="Tests passed" width="90%">
</p>

<p align="center">
  <img src="docs/screenshots/06b_ci_pipeline.png" alt="Green CI pipeline" width="90%">
</p>

---

## Stage 2: Human-in-the-Loop Administrator

After the customer confirms a booking, the chatbot hands it to a second agent. The admin agent
writes a short note for the administrator, including the free spaces for the requested period, and
sends the request to a small REST service. A human administrator approves or refuses it in a
terminal console.

<p align="center">
  <img src="docs/screenshots/s2_architecture.png" alt="Stage 2 flow" width="95%">
</p>

**Design points**

1. The admin agent only writes the note. Customer details are attached by code, and the decision
   text is produced by code, so a refusal can never be worded as an approval.
2. If the model fails, the request is still sent with a default note. If the admin service is down,
   the customer is told the request was not sent.
3. The admin service requires an API key, validates every request again, and accepts only one
   decision per request.

Changes since Stage 1: [stage-1...stage-2](https://github.com/likhithe2204/parking-chatbot/compare/stage-1...stage-2)

---

### 1. Admin service API

<p align="center">
  <img src="docs/screenshots/s2_01_admin_api_docs.png" alt="Admin service API" width="90%">
</p>

---

### 2. Administrator console

<p align="center">
  <img src="docs/screenshots/s2_02_admin_console.png" alt="Administrator console" width="90%">
</p>

---

### 3. Admin agent

<p align="center">
  <img src="docs/screenshots/s2_03_admin_agent.png" alt="Admin agent" width="90%">
</p>

---

### 4. End to end: request, pending, approved

<p align="center">
  <img src="docs/screenshots/s2_04_end_to_end.png" alt="End to end approval" width="90%">
</p>

---

### 5. End to end: refused

<p align="center">
  <img src="docs/screenshots/s2_05_refusal.png" alt="End to end refusal" width="90%">
</p>

---

### 6. Tests and CI

<p align="center">
  <img src="docs/screenshots/s2_06a_tests_passed.png" alt="Stage 2 tests passed" width="90%">
</p>

<p align="center">
  <img src="docs/screenshots/s2_06b_ci_pipeline.png" alt="Stage 2 CI pipeline" width="90%">
</p>

---

## Stage 3: MCP Server

Once the administrator approves a booking, the admin side calls an MCP server. The server checks the
API key and every field, then appends one line to a text file in this format:

```text
Name | Car Number | Reservation Period | Approval Time
Likhith Edupuganti | TS09AB1234 | 2026-12-08 10:00 to 2026-12-08 14:00 | 2026-10-29 16:13:45
```

<p align="center">
  <img src="docs/screenshots/s3_architecture.png" alt="Stage 3 flow" width="95%">
</p>

**Design points**

1. The server is Python: an MCP tool (`save_reservation`) built with the MCP SDK and mounted in a
   FastAPI app that also serves `/health`. It exposes one tool only.
2. Code decides, not the model. The language model never decides whether a record is written.
3. Security: every route except `/health` needs the API key (checked in constant time), every field
   is validated again, names cannot contain the separator or line breaks, and the reservations file
   is excluded from Git.
4. Reliability: writes are locked, flushed to disk and appended, the same booking is never written
   twice, and the client has a timeout and reports failures instead of hiding them.

Changes since Stage 2: [stage-2...stage-3](https://github.com/likhithe2204/parking-chatbot/compare/stage-2...stage-3)

---

### 1. Security checks

<p align="center">
  <img src="docs/screenshots/s3_01_security_checks.png" alt="MCP security checks" width="90%">
</p>

---

### 2. Approval saves the booking

<p align="center">
  <img src="docs/screenshots/s3_02_console_save.png" alt="Console saving through the MCP server" width="90%">
</p>

---

### 3. End to end: approved and saved

<p align="center">
  <img src="docs/screenshots/s3_03_end_to_end.png" alt="End to end with the MCP server" width="90%">
</p>

---

### 4. The reservations file

<p align="center">
  <img src="docs/screenshots/s3_04_reservation_file.png" alt="Reservations file" width="90%">
</p>

---

### 5. Tests and CI

<p align="center">
  <img src="docs/screenshots/s3_05a_tests_passed.png" alt="Stage 3 tests passed" width="90%">
</p>

<p align="center">
  <img src="docs/screenshots/s3_05b_ci_pipeline.png" alt="Stage 3 CI pipeline" width="90%">
</p>

---

## Stage 4: LangGraph Orchestration

All components run as one LangGraph graph. The customer's message goes through the chatbot node. A
confirmed booking continues to the administrator, the graph pauses until the human decides, an
approval is saved through the MCP server, and the customer is told the result.

```mermaid
flowchart TD
    start([Customer message]) --> chatbot
    chatbot -->|normal question| reply([Reply])
    chatbot -->|booking confirmed| escalate
    escalate -->|administrator unreachable| reply
    escalate -->|request sent| await_approval
    await_approval -->|approved| record
    await_approval -->|refused| notify
    record --> notify
    notify --> done([Customer is told the decision])
```

<p align="center">
  <img src="docs/screenshots/s4_01_workflow_graph.png" alt="LangGraph workflow" width="60%">
</p>

### Agent and server logic

| Component | Files | What it does |
|---|---|---|
| Workflow | `workflow.py`, `chat.py` | The LangGraph graph and the chat loop. Runs one graph per customer message, pauses at `await_approval`, resumes when the decision arrives, and polls every 3 seconds. |
| Chatbot agent | `agent.py`, `tools.py`, `draft.py`, `guardrails.py` | Answers questions with RAG and SQL tools, collects the reservation draft, and protects data in both directions. |
| Admin agent | `admin_agent.py` | The second agent. Writes the note with free spaces for the period, sends the request, reads the decision, takes a space and saves the booking. |
| Admin service | `admin_api.py`, `admin_store.py` | FastAPI and SQLite. Stores requests, needs an API key, accepts one decision per request. |
| Administrator console | `admin_console.py` | Terminal where the human approves or refuses. |
| MCP server | `mcp_server.py`, `reservation_file.py` | Validates every field and appends one line per approved booking. Needs an API key. |
| MCP client | `mcp_client.py` | Calls the MCP tool with a timeout and clear errors. |
| Booking ledger | `bookings.py` | Takes a space for an approved booking and counts free spaces per zone and per period. |

**Decisions made by code, not by the language model**

1. Whether a detail is valid, and whether it came from the customer.
2. Whether a request is sent, and the text of the decision shown to the customer.
3. Whether a space is taken and a line is written. The step is repeated up to 3 times if it fails.

### Availability model

Free spaces for a period are the zone's free spaces minus the approved bookings that overlap that
period. An approved booking takes one space in the zone with the most free spaces. A booking only
reduces availability during its own period, so a December booking never changes what is free today.
If no space is left when a booking is approved, nothing is saved and the customer is told.

### End to end: approved

<p align="center">
  <img src="docs/screenshots/s4_02_end_to_end_approve.png" alt="Chat, booking approved" width="90%">
</p>

<p align="center">
  <img src="docs/screenshots/s4_03_admin_console_approve.png" alt="Administrator approves" width="90%">
</p>

---

### End to end: refused

<p align="center">
  <img src="docs/screenshots/s4_02_end_to_end_reject.png" alt="Chat, booking refused" width="90%">
</p>

<p align="center">
  <img src="docs/screenshots/s4_03_admin_console_reject.png" alt="Administrator refuses" width="90%">
</p>

---

### The reservations file and live availability

<p align="center">
  <img src="docs/screenshots/s4_04_reservations_file.png" alt="Reservations file" width="90%">
</p>

<p align="center">
  <img src="docs/screenshots/s4_08_availability_updates.png" alt="Availability drops after an approval" width="90%">
</p>

---

### Load tests

`python -m app.load_test` starts its own temporary servers and runs three tests: 50 concurrent
administrator confirmations, 50 concurrent MCP recordings, and 3 concurrent chatbot conversations.
It also checks that every booking is stored once and that repeated bookings are ignored. Full
report: [docs/load_test_report.md](docs/load_test_report.md)

<p align="center">
  <img src="docs/screenshots/s4_05_load_test.png" alt="Load test" width="90%">
</p>

---

### Integration tests

The integration tests run the real admin service and the real MCP server, and replace only the
language model with a scripted one. They cover approval, refusal, a down MCP server, recovery after
a restart, and the space taken by an approved booking.

<p align="center">
  <img src="docs/screenshots/s4_06_orchestration_tests.png" alt="Orchestration tests" width="90%">
</p>

---

### Tests and CI

<p align="center">
  <img src="docs/screenshots/s4_07a_tests_passed.png" alt="Stage 4 tests passed" width="90%">
</p>

<p align="center">
  <img src="docs/screenshots/s4_07b_ci_pipeline.png" alt="Stage 4 CI pipeline" width="90%">
</p>

Changes since Stage 3: [stage-3...stage-4](https://github.com/likhithe2204/parking-chatbot/compare/stage-3...stage-4)

---

## Setup and Deployment

**Requirements:** Python 3.12, [uv](https://docs.astral.sh/uv/), and an EPAM DIAL API key (the VPN
is needed to call the model).

**1. Clone and create the environment**

```bash
git clone https://github.com/likhithe2204/parking-chatbot.git
cd parking-chatbot

uv venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

uv pip install -r requirements.txt
```

**2. Add your keys**

```bash
# Windows
copy .env.example .env
# Mac/Linux
cp .env.example .env
```

| Variable | Purpose |
|---|---|
| `DIAL_API_KEY` | Key for the language model |
| `DIAL_ENDPOINT`, `DIAL_API_VERSION`, `DIAL_DEPLOYMENT` | Model endpoint settings |
| `ADMIN_API_KEY` | Key the admin service requires |
| `ADMIN_API_URL` | Address of the admin service (default `http://127.0.0.1:8000`) |
| `MCP_API_KEY` | Key the MCP server requires |
| `MCP_SERVER_URL` | Address of the MCP server (default `http://127.0.0.1:8001/mcp`) |

Generate each key with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

**3. Build the data stores**

```bash
python -m app.seed_db   # creates data/parking.db (prices, hours, availability, bookings)
python -m app.ingest    # fills the Chroma vector database (knowledge base)
```

**4. Run the system** (three terminals, environment active in each)

```bash
python scripts/start_services.py   # admin service on 8000 and MCP server on 8001
python -m app.chat                 # customer chat
python -m app.admin_console        # administrator
```

`start_services.py` stops with a clear message if either port is already in use. Both servers answer
`/health`.

### Deployment guidelines

1. Run the admin service and the MCP server as separate processes. They listen on `127.0.0.1` by
   default. In production, put them behind a reverse proxy with TLS.
2. Run each server with a single worker. The file lock and the duplicate check of the MCP server work
   inside one process.
3. Keep secrets out of Git and images. Provide them through the platform's secret store.
4. Keep `data/` (SQLite files, the Chroma index and the reservations file) on a persistent volume and
   back it up. The reservations file holds customer data.
5. Check `/health` on both servers for monitoring. The chat writes problems to `logs/chat.log`.
6. Deploy only commits whose GitHub Actions run is green.

---

## Usage

**Example conversation**

| You | The bot |
|---|---|
| Where is the parking located? | Gives the address and the nearest metro |
| How much does it cost for a car? | Reads prices from SQL |
| How many spaces are free on 2026-12-10 from 10:00 to 14:00? | Reads availability for that period |
| I want to book a parking space | Collects the details, then sends the request to the administrator |
| What is the status of my request? | Reports pending, approved or refused, with the reason |

While the chat is open, the decision appears by itself as an `[Update]` line. Approved bookings that
were decided while no chat was running are saved the next time the chat starts.

**Administrator**

```bash
python -m app.admin_console
```

Pick a request id, then type `approve` or `refuse` and an optional reason. Add `--save` to also save
approvals directly through the MCP server, as in Stage 3.

**Other commands**

| Command | Purpose |
|---|---|
| `python -m app.check_retrieval` | Quick retrieval check |
| `python -m app.demo_guardrails` | Shows the guardrails in action |
| `python -m app.demo_admin_agent` | Sends a sample request through the admin agent |
| `python -m app.demo_mcp_security` | Shows the MCP server blocking bad requests |
| `python -m app.show_graph` | Draws the LangGraph workflow |
| `python -m app.evaluate` | Evaluation, writes `docs/evaluation_report.md` |
| `python -m app.load_test` | Load tests, writes `docs/load_test_report.md` |
| `python scripts/build_deck_stage4.py` | Rebuilds the Stage 4 presentation |
| `python -m pytest -v` | Runs all tests |

---

## Evaluation

Full report of the latest run: [docs/evaluation_report.md](docs/evaluation_report.md)

<!-- The knowledge base grew from 5 to 17 documents in Stage 4, and the evaluation from 13 to 34
questions. Each question lists every document that contains the answer.

<p align="center">
  <img src="docs/screenshots/s4_09_knowledge_base_evaluation.png" alt="Evaluation with the larger knowledge base" width="90%">
</p> -->

**Stage 1 results** (5 documents, 13 questions)

| K | Precision@K | Recall@K |
|---|---|---|
| 1 | 0.92 | 0.85 |
| 2 | 0.62 | 0.92 |
| 3 | 0.44 | 1.00 |

MRR: **0.95**. End-to-end answer accuracy: 16 of 16 runs passed. Precision counts chunks and Recall
counts source documents, so with few chunks per document Precision@3 is naturally lower than
Recall@3.

---

## Testing and CI

235 pytest tests cover SQL lookups, availability and bookings, reservation validation, the
reservation draft and reply guard, tools, guardrails, the evaluation metrics, the admin store, API,
client, console and agent, the reservation file writer, MCP server and client, the LangGraph
workflow, the chat loop, and the load test helpers. GitHub Actions runs them on every push
(`.github/workflows/ci.yml`). The tests never call the language model, so they need no API key.

Every core module in `app/` has at least 2 tests. The demo scripts (`smoke_test`, `check_retrieval`,
`demo_guardrails`, `demo_admin_agent`, `demo_mcp_security`, `show_graph`) are excluded because they
only print results.

```bash
python -m pytest -q -W error
```

---

## Security

1. SQL queries are parameterized, and reads open the database read-only.
2. Sensitive data is masked in user input and in model output.
3. Prompt injection phrases are blocked before they reach the model.
4. The system prompt forbids sharing staff or customer details.
5. API keys live in `.env`, which is excluded from Git. `.env.example` shows the format.
6. The admin service needs an API key and accepts one decision per request.
7. Reservation details must come from the customer's own words, so the model cannot invent them.
8. The MCP server needs the API key on every route except `/health`, exposes one tool, validates every
   field, and rejects separators and line breaks in names.
9. The reservations file and the chat log hold customer data, so both are excluded from Git.
10. Both servers listen on `127.0.0.1` by default. Do not expose them to a network without TLS.

---

## Project Structure

```text
parking-chatbot/
  app/
    config.py            paths and chunking settings
    llm.py               DIAL / Azure OpenAI model loader
    vector_store.py      Chroma and embeddings
    ingest.py            loads, chunks and stores the knowledge base
    rag.py               retrieval and RAG answer chain
    seed_db.py           creates the SQLite database
    dynamic_data.py      read-only SQL lookups
    bookings.py          takes spaces for approved bookings, counts free spaces
    reservation.py       reservation validation
    draft.py             reservation draft, customer-words checks, reply guard
    messages.py          customer-facing decision and saving messages
    tools.py             chatbot tools
    guardrails.py        input and output protection
    agent.py             chatbot agent, prompt and chat function
    workflow.py          the LangGraph workflow
    chat.py              interactive chat loop with live updates
    admin_store.py       reservation requests and decisions (SQLite)
    admin_api.py         admin REST service (FastAPI)
    admin_client.py      REST client used by the agent and the console
    admin_agent.py       second agent: note, send, read decision, save approved booking
    admin_console.py     terminal for the human administrator
    reservation_file.py  validates and appends reservation lines
    mcp_server.py        MCP server with API key protection (FastAPI)
    mcp_client.py        client that calls the MCP server
    evaluation.py        metric functions
    evaluate.py          evaluation runner and report writer
    load_test.py         load tests and report writer
    show_graph.py        draws the workflow graph
  data/
    static/              knowledge base (17 markdown files)
    eval/                evaluation questions
  docs/
    screenshots/         architecture diagrams and proof screenshots
    evaluation_report.md
    load_test_report.md
    workflow_graph.mmd
  scripts/               service starter and presentation builders
  tests/                 pytest tests
  .github/workflows/     CI pipeline
```

`data/confirmed_reservations.txt` and `logs/` are created at runtime and are not stored in Git.

---

## Limitations

1. The waiting state of the workflow is kept in memory. If the chat restarts, bookings approved in the
   meantime are saved at the next start, but the customer is not told about them.
2. The baseline free spaces per zone are demo data. Walk-in occupancy is not modelled.
3. The zone is assigned automatically. Customers cannot choose a zone, and EV charging is not
   guaranteed by a reservation.
4. The assistant cannot cancel or change a submitted request. The knowledge base sends customers to
   the parking office.
5. The MCP server uses a file and a process-level lock, so it must run with a single worker.

---

## Roadmap

| Stage | Scope | Status |
|---|---|---|
| 1 | RAG chatbot, vector database, guardrails, evaluation | Done |
| 2 | Human-in-the-loop administrator agent | Done |
| 3 | MCP server that records approved reservations | Done |
| 4 | Full orchestration with LangGraph | Done |