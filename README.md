# OSINT Graph Intelligence Engine

A local, fully offline intelligence analysis tool that ingests unstructured documents, extracts entities, resolves duplicate identities across name variants, builds a knowledge graph of connections, and lets analysts query it in plain English.

Built for environments where data sovereignty is non-negotiable — no internet, no cloud, no data leaves the machine.

---

## Current Status

This project is under active development. The sections below are split into **what's working today** and **planned / in-progress** so the gap is always clear.

### Working today
- Document ingestion → chunking → embedding → ChromaDB storage
- Two-stage LLM entity & relationship extraction (entities first, then relationships constrained to only reference extracted entities — enforced via Pydantic `Literal` types, not just prompted)
- Entity resolution via a fuzzy-similarity-based XGBoost classifier, with a conservative confidence threshold to avoid false merges
- NetworkX knowledge graph built from resolved entities and extracted relationships, persisted to disk
- Semantic-search-based question answering: query → ChromaDB retrieval → context-grounded LLM answer generation

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

### Alias Consolidation

**All aliases are now consolidated under a single canonical entity.** When the system identifies that "John Wick", "Wick", and "J. Wick" refer to the same person, it:

1. **Stores one canonical entity** (e.g., "John Wick") in the database and graph
2. **Tracks all aliases** ("Wick", "J. Wick") in a separate alias table with confidence scores
3. **Uses the canonical name in all relationships** — so edges connect to "John Wick", not the individual aliases
4. **Attaches alias metadata to graph nodes** — you can see all known aliases for any entity

This means:
- **No duplicate nodes** for the same person/organization
- **No fragmented relationships** — all connections route through the canonical entity
- **Full alias visibility** — you can still see which name variants were found in the source documents

**View consolidated entities:**
```bash
# See all entities with their aliases
python scripts/view_entities_with_aliases.py
```

**Migrate existing data:**
```bash
# If you already have data, run this once to consolidate it
python scripts/migrate_aliases.py
```

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

## Prerequisites

### 1. Install Ollama and Pull Models
```bash
# Install Ollama from https://ollama.ai
# Then pull required models:
ollama pull llama3.1
ollama pull nomic-embed-text
```

### 2. Set Up Python Environment
```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt

# Windows (Command Prompt)
python -m venv venv
.\venv\Scripts\activate.bat
pip install -r requirements.txt
```

---

## Quick Start (Single Command)

### 1. Add Your Documents
```bash
# Linux/Mac
cp ~/my_documents/*.pdf "input_files/"

# Windows (PowerShell)
Copy-Item "C:\Users\YourName\Documents\*.pdf" -Destination "input_files\"
```

### 2. Run Everything
```bash
# Linux/Mac
./venv/bin/python run.py

# Windows
.\venv\Scripts\python run.py
```

**What it does:**
1. ✅ Processes all documents in `input_files/`
2. ✅ Builds the knowledge graph
3. ✅ Opens the graph visualization automatically
4. ✅ Launches interactive query interface

That's it! One command, complete workflow.

---

## Example Session

```bash
# Linux/Mac
$ ./venv/bin/python run.py

# Windows
> .\venv\Scripts\python run.py

🔍 OSINT GRAPH INTELLIGENCE ENGINE
======================================================================

STEP 1: DOCUMENT INGESTION & ENTITY EXTRACTION
======================================================================

📂 Found 3 file(s) to process:
   • document1.pdf
   • document2.pdf
   • document3.txt

[Processing each file...]

✅ PIPELINE COMPLETE

📊 Knowledge Base:
   • Documents:     3
   • Entities:      45
   • Relationships: 67

STEP 2: OPENING GRAPH VISUALIZATION
======================================================================
📊 Opening graph visualization...
[Graph image opens automatically in your default image viewer]

STEP 3: INTERACTIVE QUERY INTERFACE
======================================================================

Ask questions about your documents.
Type 'help' for examples, 'exit' to quit.

❓ Your question: Who is John Wick?
🔍 Searching knowledge base...

📝 Answer:
----------------------------------------------------------------------
John Wick is a tactical operator with EXTREME THREAT LEVEL...
----------------------------------------------------------------------

❓ Your question: What is the relationship between Wick and Charon?
🔍 Searching knowledge base...

📝 Answer:
----------------------------------------------------------------------
[Answer appears here...]
----------------------------------------------------------------------

❓ Your question: exit
👋 Goodbye!
```

---

### Step 1: Add Your Documents
```bash
# Place PDFs or text files in the input_files folder
cp ~/my_documents/*.pdf "input_files/"
```

### Step 2: Run the Full Pipeline
```bash
# This single command does everything:
# - Ingests all documents
# - Extracts entities and relationships
# - Builds the knowledge graph
# - Generates visualization
./venv/bin/python run_full_ingestion.py
```

**Output:**
```
✅ PIPELINE COMPLETE

📊 Database Summary:
   • Documents:     3
   • Entities:      30
   • Relationships: 63

📁 Output Files:
   • Knowledge Graph: output/ER_Graph.pkl
   • Visualization:   output/graph_preview.png
   • Database:        data/intelligence.db
```

### Step 3: Query the Knowledge Base

**Interactive Session (Recommended)**
```bash
./venv/bin/python scripts/interactive_query.py
```

Ask questions interactively:
```
❓ Your question: Who is John Wick?
🔍 Searching knowledge base...

📝 Answer:
----------------------------------------------------------------------
John Wick is a tactical operator with EXTREME THREAT LEVEL...
----------------------------------------------------------------------

❓ Your question: exit
👋 Goodbye!
```

**Alternative: Single Question**
```bash
./venv/bin/python scripts/query.py "Who is John Wick?"
```

**Alternative: From Python Code**
```python
from retrieval.retriever import answer_with_context

answer = answer_with_context("Who is John Wick?")
print(answer)
```

---

## View the Knowledge Graph

The graph visualization is automatically generated:

```bash
# View the graph
xdg-open output/graph_preview.png  # Linux
open output/graph_preview.png      # Mac
start output/graph_preview.png     # Windows
```

---

## Running It

## Advanced Usage

### Merge Duplicate Entities

If you notice duplicate entities in your graph (e.g., "John Wick", "Wick", "J. Wick" as separate nodes), run the duplicate merger:

```bash
# Linux/Mac
./venv/bin/python scripts/migrate_aliases.py

# Windows
.\venv\Scripts\python scripts/migrate_aliases.py
```

This uses the LLM to intelligently identify and merge duplicates. It will:
- Analyze all entities for potential duplicates
- Show you what it found
- Ask for confirmation before merging
- Update the database and rebuild the graph

### Individual Pipeline Stages

For granular control over individual pipeline stages:

### Linux/Mac
```bash
# Ingest a single file
./venv/bin/python -m ingestion.pipeline "path/to/document.pdf"

# Extract entities from document_id 1
./venv/bin/python -c "from extraction.entity_extractor import extract_from_document; extract_from_document(1)"

# Rebuild graph from database
./venv/bin/python -c "from graph.builder import add_all_entities, add_all_relationships, save_graph; add_all_entities(); add_all_relationships(); save_graph()"

# Regenerate visualization
./venv/bin/python -m graph.visualizer

# Single question query
./venv/bin/python scripts/query.py "Your question here"

# Interactive query session
./venv/bin/python scripts/interactive_query.py
```

### Windows
```powershell
# Ingest a single file
.\venv\Scripts\python -m ingestion.pipeline "path\to\document.pdf"

# Extract entities from document_id 1
.\venv\Scripts\python -c "from extraction.entity_extractor import extract_from_document; extract_from_document(1)"

# Rebuild graph from database
.\venv\Scripts\python -c "from graph.builder import add_all_entities, add_all_relationships, save_graph; add_all_entities(); add_all_relationships(); save_graph()"

# Regenerate visualization
.\venv\Scripts\python -m graph.visualizer

# Single question query
.\venv\Scripts\python scripts/query.py "Your question here"

# Interactive query session
.\venv\Scripts\python scripts/interactive_query.py
```

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