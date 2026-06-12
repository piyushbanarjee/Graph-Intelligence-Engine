# OSINT Graph Intelligence Engine

A local, fully offline intelligence analysis tool that ingests unstructured documents, extracts entities, resolves duplicate identities across name variants, builds a knowledge graph of connections, and lets analysts query it in plain English.

Built for environments where data sovereignty is non-negotiable — no internet, no cloud, no data leaves the machine.

---

## What It Does

You feed it raw documents. It figures out who and what is mentioned, resolves that "P. Banarjee" and "Piyush B." are the same person, builds a visual web of how everything connects, and answers natural language questions over that web — with source citations.

---

## The Two Ways to Use It

**Visual Graph Panel**
An interactive, explorable graph of all entities and their connections. Drag nodes, zoom in, click to see aliases and source documents. For when you don't have a specific question — just want to find patterns.

**Chat Interface Panel**
Type a natural language question. Get a cited answer that draws on both the graph structure and the original source text.

Both panels live in the same Streamlit app, reading from the same underlying graph.

---

## How It Works

```
RAW INPUT (PDF / text / paste)
        ↓
INGESTION
Store document in SQLite
Chunk → Embed → Store in ChromaDB
        ↓
ENTITY EXTRACTION
Ollama reads each chunk
Returns structured JSON:
people, orgs, locations, events
        ↓
ENTITY RESOLUTION
Every new entity scored against existing ones
Signals: name similarity + co-occurrence + shared attributes
XGBoost outputs confidence score (0–1)
High confidence → auto merge with aliases
Low confidence → flagged for analyst review
        ↓
KNOWLEDGE GRAPH
Resolved entities → nodes
Relationships → edges
Stored in NetworkX
        ↓
QUERY
Analyst asks a question
        ↓
TWO-STEP RETRIEVAL
Graph traversal (NetworkX) → structural context
Semantic search (ChromaDB) → source text context
Conversation history → session continuity
        ↓
GENERATION
All three fed to Ollama
Returns cited natural language answer
        ↓
OUTPUT
Answer + source citations + live graph update
```

---

## The Three Data Stores

| Store | What lives there | Purpose |
|---|---|---|
| SQLite | Raw documents, entity candidates | Source of truth |
| ChromaDB | Embedded text chunks | Semantic search |
| NetworkX | Entities + relationships | Graph traversal |

Every document touches all three on ingestion.

---

## Direct vs Indirect Connections

**Direct (1 hop)** — explicitly stated in source text. The LLM extracted it from a sentence. Becomes a graph edge immediately.

**Indirect (2+ hops)** — implied by graph structure across multiple documents. Never stated anywhere. Surfaced automatically by NetworkX traversal when a question is asked.

The analyst never has to think about this distinction. The system handles it.

---

## Entity Resolution — The Core Problem It Solves

Real-world documents refer to the same person in dozens of ways:

```
P. Banarjee
Piyush Banarjee
Piyush B.
Mr. Banarjee
```

Without resolution, each becomes a separate node. The graph fragments. Connections break. Intelligence is lost.

The resolution engine scores every new entity against all existing ones using multiple signals — not just name similarity, but co-occurrence in documents, shared location mentions, and shared organizational context. The XGBoost classifier outputs a confidence score with a human-readable explanation of *why* it thinks two names are the same person. Analysts can review and override low-confidence merges.

---

## Follow-up Questions

Every follow-up question triggers a fresh graph traversal and fresh semantic search, with the conversation history summarized and passed as context. The system knows "he" refers to Piyush because it tracks the session. Long sessions are periodically summarized to stay within the LLM's context window.

---

## Tech Stack

| Layer | Tool |
|---|---|
| LLM | Ollama (llama3.2) |
| Embeddings | nomic-embed-text |
| Vector store | ChromaDB |
| Graph store | NetworkX |
| Graph visualization | pyvis |
| Resolution classifier | XGBoost |
| Database | SQLite |
| UI | Streamlit |
| Language | Python |

---

## Prerequisites

**Models (via Ollama)**
```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

**Python dependencies**
```bash
pip install -r requirements.txt
```

---

## Running the App

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Project Structure

```
OSINT-Graph-Intelligence-Engine/
├── app.py                  # Streamlit UI — graph panel + chat panel
├── ingestion/
│   ├── chunker.py          # Document chunking logic
│   ├── embedder.py         # nomic-embed-text via Ollama
│   └── store.py            # SQLite + ChromaDB writes
├── extraction/
│   └── entity_extractor.py # Ollama JSON extraction prompt
├── resolution/
│   ├── scorer.py           # Fuzzy + co-occurrence feature engineering
│   └── classifier.py       # XGBoost model — train + predict
├── graph/
│   ├── builder.py          # NetworkX node/edge management
│   └── visualizer.py       # pyvis rendering
├── query/
│   ├── retriever.py        # Graph traversal + ChromaDB search
│   └── generator.py        # Ollama answer generation with citations
├── data/
│   └── intelligence.db     # SQLite database
├── requirements.txt
└── README.md
```

---

## Why Fully Offline

The intended users — intelligence agencies, law enforcement, defense organizations — operate on sensitive data that cannot touch external servers. Every query, every document, every entity name stays on the local machine. Sovereign by design, not by accident.

---

## What It Is Not

- Not a live threat monitoring tool
- Not a web scraper
- Not a replacement for analyst judgment — low-confidence entity merges always go to human review
- Not dependent on any cloud LLM API

---

## Inspired By

The core intelligence problem: fragmented data across hundreds of documents makes it nearly impossible to see the full picture manually. This system automates the grunt work so analysts can focus on what humans do best — judgment, context, and decision-making.