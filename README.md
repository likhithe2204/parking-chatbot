<h1 align="center">Parking Space Reservation Chatbot</h1>

<p align="center">
    An AI assistant for a parking facility. It answers questions about the facility,
    checks live prices and availability, collects reservation details with validation,
    and protects sensitive data. Built with Python, LangChain and LangGraph on a
    Retrieval-Augmented Generation (RAG) architecture
</p>

<p align="center">
  <a href="https://github.com/likhithe2204/parking-chatbot/actions/workflows/ci.yml">
    <img src="https://github.com/likhithe2204/parking-chatbot/actions/workflows/ci.yml/badge.svg" alt="CI status">
  </a>
  <img src="https://img.shields.io/badge/python-3.12-blue" alt="Python 3.12">
  <img src="https://img.shields.io/badge/tests-68%20passed-brightgreen" alt="68 tests passed">
  <img src="https://img.shields.io/badge/LangChain-LangGraph-purple" alt="LangChain and LangGraph">
</p>

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [How It Works](#how-it-works)
4. [Demo](#demo)
5. [Setup](#setup)
6. [Usage](#usage)
7. [Evaluation](#evaluation)
8. [Testing and CI](#testing-and-ci)
9. [Security](#security)
10. [Project Structure](#project-structure)
11. [Roadmap](#roadmap)

---

## Overview

Built with Python, LangChain and LangGraph on a Retrieval-Augmented Generation (RAG)
architecture. This repository currently covers **Stage 1**: the RAG chatbot, the
guardrails and the evaluation.

**Presentation:** [docs/parking_chatbot_stage1.pptx](docs/parking_chatbot_stage1.pptx)

**Features**

1. Answers questions about the facility: general information, location, zones, EV charging, booking process.
2. Reports live data: working hours, prices and free spaces.
3. Collects reservation details one field at a time and validates each answer.
4. Masks sensitive data (email, phone, card number) and blocks prompt injection.
5. Ships with an evaluation report: Recall@K, Precision@K, MRR and latency.

**Tech stack**

| Area | Choice |
|---|---|
| Language | Python 3.12 |
| Agent framework | LangChain, LangGraph |
| LLM | GPT via EPAM DIAL (Azure OpenAI interface) |
| Vector database | Chroma |
| Embeddings | `all-MiniLM-L6-v2` (sentence-transformers) |
| Dynamic data | SQLite |
| Guardrails | Microsoft Presidio and spaCy |
| Testing | pytest, GitHub Actions |

---

## Architecture

<p align="center">
  <img src="docs/architecture.png" alt="System architecture" width="95%">
</p>

---

## How It Works

**1. Static data goes to the vector database.**
General information, zones, location and the booking process are split into chunks,
embedded and stored in Chroma. A question about the facility retrieves the 3 closest chunks.

**2. Dynamic data goes to SQL.**
Working hours, prices and availability change often, so they live in SQLite and are read
through parameterized, read-only queries.

**3. The agent chooses the right tool.**
The agent reads each question and decides whether to search the vector database, query SQL,
or start the reservation flow.

**4. Reservations are validated field by field.**
Each answer is checked the moment it is given: names contain letters only, car numbers look
like `TS09AB1234`, dates are in the future, and the end comes after the start. The bot never
says a booking is confirmed, because an administrator must approve it (Stage 2).

**5. Guardrails protect both directions.**
The input guardrail masks sensitive data and blocks prompt injection. The output guardrail
masks anything sensitive that slips into a reply.

---

## Demo

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
  <img src="docs/screenshots/06b_ci_pipeline.png" alt="Green CI pipeline" width="90%">
</p>

<p align="center">
  <img src="docs/screenshots/06a_tests_passed.png" alt="44 tests passed" width="90%">
</p>


---

## Setup

**Requirements:** Python 3.12, [uv](https://docs.astral.sh/uv/), and an EPAM DIAL API key
(the VPN is needed to call the model).

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

**2. Add your API key**

```bash
# Windows
copy .env.example .env
# Mac/Linux
cp .env.example .env
```

Open `.env` and paste your DIAL API key.

**3. Build the data stores**

```bash
python -m app.seed_db   # creates data/parking.db (dynamic data)
python -m app.ingest    # fills the Chroma vector database (static data)
```

---

## Usage

Start the chatbot:

```bash
python -m app.chat
```

**Example conversation**

| You | The bot |
|---|---|
| Where is the parking located? | Gives the address and the nearest metro |
| How much does it cost for a car? | Reads prices from SQL |
| Are there free spaces in Zone C? | Reads live availability from SQL |
| I want to book a parking space | Starts the reservation flow |

**Other commands**

| Command | Purpose |
|---|---|
| `python -m app.check_retrieval` | Quick retrieval check |
| `python -m app.demo_guardrails` | Shows the guardrails in action |
| `python -m app.evaluate` | Full evaluation, writes `docs/evaluation_report.md` |
| `python -m app.evaluate --skip-llm` | Evaluation without LLM calls |
| `python -m pytest -v` | Runs all tests |

---

## Evaluation

Full report: [docs/evaluation_report.md](docs/evaluation_report.md)

**Retrieval quality** (13 questions)

| K | Precision@K | Recall@K |
|---|---|---|
| 1 | 0.92 | 0.85 |
| 2 | 0.62 | 0.92 |
| 3 | 0.44 | 1.00 |

MRR: **0.95**

**End-to-end answer accuracy:** 16 of 16 runs passed.

**Latency**

| Component | Mean |
|---|---|
| Retrieval (embedding and Chroma) | 8.1 ms |
| Input guardrail (Presidio) | 2.7 ms |
| SQL lookup tools | 0.2 ms |
| Full chatbot reply | about 6.2 s |

Almost all of the full reply time is the LLM call. Precision counts chunks and Recall counts
source documents, so with only a few chunks per document, Precision@3 is naturally lower
than Recall@3.

---

## Testing and CI

68 pytest tests cover SQL lookups, reservation validation, tools, guardrails and the
evaluation metrics. GitHub Actions runs them on every push
(`.github/workflows/ci.yml`). The tests never call the LLM, so they need no API key.

Every core module in app/ has at least 2 tests. The three demo scripts (smoke_test, check_retrieval, demo_guardrails) are excluded because they only print results.

```bash
python -m pytest -v
```

---

## Security

1. SQL queries are parameterized and the database is opened read-only.
2. Sensitive data is masked in user input and in model output.
3. Prompt injection phrases are blocked before they reach the model.
4. The system prompt forbids sharing staff or customer details.
5. API keys live in `.env`, which is excluded from Git. `.env.example` shows the format.

`data/static/internal_staff_notes.md` contains fake staff and customer details on purpose,
to demonstrate that the guardrails stop private data from leaking.

---

## Project Structure

```text
parking-chatbot/
  app/
    config.py            paths and chunking settings
    llm.py               DIAL / Azure OpenAI model loader
    vector_store.py      Chroma and embeddings
    ingest.py            loads, chunks and stores static data
    rag.py               retrieval and RAG answer chain
    seed_db.py           creates the SQLite database
    dynamic_data.py      read-only SQL lookups
    reservation.py       reservation validation
    tools.py             agent tools
    guardrails.py        input and output protection
    agent.py             agent, prompt and chat function
    chat.py              interactive chat loop
    evaluation.py        metric functions
    evaluate.py          evaluation runner and report writer
  data/
    static/              knowledge base (markdown files)
    eval/                evaluation questions
  docs/
    architecture.png
    screenshots/
    evaluation_report.md
  tests/                 pytest tests
  .github/workflows/     CI pipeline
```

---

## Roadmap

| Stage | Scope | Status |
|---|---|---|
| 1 | RAG chatbot, vector database, guardrails, evaluation | Done |
| 2 | Human-in-the-loop administrator agent | Planned |
| 3 | MCP server that records confirmed reservations | Planned |
| 4 | Full orchestration with LangGraph | Planned |