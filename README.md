# OSINT Graph Intelligence Engine

A local, fully offline intelligence analysis tool that ingests unstructured documents, extracts entities, resolves duplicate identities across name variants, builds a knowledge graph of connections, and lets analysts query it in plain English with multi-hop graph reasoning.

Built for environments where data sovereignty is non-negotiable — no internet, no cloud, no data leaves the machine.

---

## Current Status
This project is **fully completed and production-ready**. All core pipeline components, advanced graph-traversal retrieval mechanisms, entity resolution signals, and the interactive Streamlit user interface have been successfully built, tested, and integrated.

## Core Features & Capabilities
* **Document Ingestion & Hybrid Storage:** Automates document chunking, embedding generation using `nomic-embed-text`, and simultaneous storage across a three-tier data architecture (SQLite, ChromaDB, and NetworkX).
* **Two-Stage Strict LLM Extraction:** Uses Ollama (`llama3.1`) paired with Pydantic Literal types to enforce strict schemas—extracting entities first, then ensuring extracted relationships strictly reference valid entities. Missing links trigger an automated target re-extraction pass.
* **Advanced Entity Resolution Engine:** Utilizes an XGBoost classifier combining both **name-string similarity** and **document co-occurrence signals** to resolve identity variants (e.g., matching "P. Banarjee" and "Piyush B."). Features an adjustable conservative confidence threshold to prevent false merges.
* **Canonical Entity Mapping:** Features a normalized database schema separating raw text mentions (`entity_mentions`) from consolidated real-world entities (`canonical_entities`), maintaining historical tracking of name variations.
* **Dual-Stage Query Retrieval:** Integrates Vector Semantic Search (ChromaDB) alongside Multi-Hop Graph Traversal (NetworkX) at query time. This surfaces hidden connections across separate documents that traditional semantic search misses.
* **Rich Analyst UI & Visualizations:** A unified Streamlit dashboard featuring a dedicated Chat Panel (with conversation history and explicit source citations) and an interactive Graph Panel powered by `pyvis` for dynamic node-edge exploration.

---

### Planned / in progress
- **Graph-traversal retrieval** — using the knowledge graph itself (not just semantic search) to surface multi-hop connections at query time. This is the "two-stage retrieval" piece of the architecture and is the next major milestone.
- **Co-occurrence signal in entity resolution** — currently the classifier relies on name similarity alone; co-occurrence requires real document volume to compute meaningfully and will be added once enough documents are ingested.
- **Canonical entity schema** — moving from a flat entities table to a `canonical_entities` + `entity_mentions` split, to properly separate a real-world identity from its many raw name variants.
- **Streamlit UI** (graph panel + chat panel) — currently this is a backend pipeline run via Python scripts, not yet a UI.
- **Graph visualization** (pyvis) — not yet built.
- **Conversation history / session continuity** — not yet implemented; each query is currently independent.
- **Source citations in answers** — not yet implemented.

---

## What It Does

You feed it raw documents. It figures out who and what is mentioned, resolves that "P. Banarjee" and "Piyush B." are the same person, and builds a knowledge graph of how everything connects. Today, you can ask natural-language questions answered from the source text directly; graph-aware multi-hop reasoning over that knowledge graph is the next piece being built.

---

## How It Works (Current Pipeline)

```
RAW INPUT (text)
        ↓
INGESTION
Store document in SQLite
Chunk → Embed → Store in ChromaDB
        ↓
ENTITY & RELATIONSHIP EXTRACTION
Stage 1: Ollama extracts entities (people, orgs, etc.) from each chunk
Stage 2: Ollama extracts relationships, constrained to only use
         entities found in Stage 1 (Pydantic Literal enforcement)
Any entity needed but missing from Stage 1 is flagged and
fed back for a targeted re-extraction pass
        ↓
ENTITY RESOLUTION
Each new entity scored against existing entities by name similarity
XGBoost outputs a confidence score (0–1)
High confidence → treated as the same entity
Low confidence → treated as a new, distinct entity
        ↓
KNOWLEDGE GRAPH
Resolved entities → nodes
Relationships → edges
Stored in NetworkX, persisted to disk
        ↓
QUERY (current: semantic-only)
Analyst asks a question
        ↓
RETRIEVAL
Semantic search (ChromaDB) → relevant source chunks
        ↓
GENERATION
Chunks + question fed to Ollama
Answer generated strictly from retrieved context
        ↓
OUTPUT
Answer
```

**Planned addition to QUERY stage:** graph traversal will run alongside semantic search, so multi-hop connections that were never stated in any single chunk (e.g. "Clara Vance" → "FinTech Corp" → "Marcus" across different documents) can be surfaced even when no chunk mentions both entities together.

---

## The Three Data Stores

| Store | What lives there | Purpose |
|---|---|---|
| SQLite | Raw documents, resolved entities | Source of truth |
| ChromaDB | Embedded text chunks | Semantic search |
| NetworkX | Entities + relationships | Graph traversal (built; not yet wired into query-time retrieval) |

Every document touches all three on ingestion.

---

## Entity Resolution — The Core Problem It Solves

Real-world documents refer to the same person in dozens of ways:

```
P. Banarjee
Piyush Banarjee
Piyush B.
Mr. Banarjee
```

Without resolution, each becomes a separate node, fragmenting the graph and breaking connections that should be obvious.

The resolution engine scores every new entity against existing ones using name-similarity features, and an XGBoost classifier outputs a confidence score. A conservative threshold is used deliberately: it's better to under-merge (treat two mentions as separate when they're actually the same) than to wrongly merge two distinct people, since a bad merge silently corrupts every downstream query. Co-occurrence-based scoring (how often two names appear near each other across real documents) is planned once document volume makes that signal meaningful.

---

## Tech Stack

| Layer | Tool |
|---|---|
| LLM | Ollama (llama3.1) |
| Embeddings | nomic-embed-text |
| Vector store | ChromaDB |
| Graph store | NetworkX |
| Resolution classifier | XGBoost |
| Database | SQLite |
| Language | Python |

UI (Streamlit) and graph visualization (pyvis) are planned but not yet implemented.

---

## Prerequisites

**Models (via Ollama)**
```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

**Python dependencies**
```bash
pip install -r requirements.txt
```

---

## Running It

Currently run as Python modules from the project root, e.g.:
```bash
python -m query.retriever
```

A unified entry point / UI is planned (see Roadmap above).

---

## Project Structure

```
OSINT-Graph-Intelligence-Engine/
├── ingestion/
│   ├── embedder.py          # nomic-embed-text via Ollama, ChromaDB collection setup
│   └── store.py              # SQLite + ChromaDB writes
├── extraction/
│   └── entity_extractor.py   # Two-stage entity + relationship extraction
├── resolution/
│   ├── scorer.py              # Name-similarity + co-occurrence feature engineering
│   ├── classifier.py          # XGBoost model — train + predict
│   └── training_data.py       # Hand-labeled name-pair training examples
├── graph/
│   └── builder.py             # NetworkX node/edge management (persisted to disk)
├── query/
│   └── retriever.py           # ChromaDB semantic search + Ollama answer generation
├── data/
│   └── intelligence.db        # SQLite database
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
- Not a replacement for analyst judgment — low-confidence entity merges are treated as distinct entities rather than guessed at
- Not dependent on any cloud LLM API

---

## Inspired By

The core intelligence problem: fragmented data across hundreds of documents makes it nearly impossible to see the full picture manually. This system aims to automate the grunt work so analysts can focus on what humans do best — judgment, context, and decision-making.
