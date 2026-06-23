# Project Structure

## Core Files

```
OSINT-Graph-Intelligence-Engine/
│
├── run_full_ingestion.py      # Main entry point - runs entire pipeline
├── interactive_query.py        # Interactive Q&A interface
├── query.py                    # Single question CLI
│
├── ingestion/                  # Document ingestion pipeline
│   ├── pipeline.py            # Orchestrates ingestion flow
│   ├── reader.py              # PDF/TXT file readers
│   ├── chunker.py             # Text chunking logic
│   ├── embedder.py            # ChromaDB + embedding setup
│   └── store.py               # SQLite database operations
│
├── extraction/                 # Entity extraction
│   └── entity_extractor.py    # LLM-based entity & relationship extraction
│
├── resolution/                 # Entity resolution
│   ├── classifier.py          # XGBoost duplicate detection
│   ├── scorer.py              # Name similarity + co-occurrence scoring
│   ├── training_data.py       # Training examples for classifier
│   └── XGB_entity_model.pkl   # Pre-trained XGBoost model
│
├── graph/                      # Knowledge graph
│   ├── builder.py             # NetworkX graph construction
│   ├── visualizer.py          # Graph visualization (matplotlib)
│   ├── ER_Graph.pkl           # Generated graph (gitignored)
│   └── graph_preview.png      # Generated visualization (gitignored)
│
├── retrieval/                  # RAG pipeline
│   └── retriever.py           # ChromaDB search + LLM answer generation
│
├── Input Files/                # Drop documents here for processing
│   ├── *.pdf
│   └── *.txt
│
├── data/                       # Generated data (gitignored)
│   ├── intelligence.db        # SQLite database
│   └── chromadb/              # Vector embeddings
│
├── requirements.txt            # Python dependencies
├── README.md                   # Main documentation
├── USAGE.md                    # Detailed usage guide
├── LINKEDIN_POST.md            # LinkedIn post templates
└── .gitignore                  # Git ignore patterns
```

## Data Flow

```
Input Files/*.pdf,*.txt
        ↓
run_full_ingestion.py
        ↓
    ┌───────────────┐
    │  INGESTION    │  → data/intelligence.db (SQLite)
    │               │  → data/chromadb/ (vectors)
    └───────┬───────┘
            ↓
    ┌───────────────┐
    │  EXTRACTION   │  → Entities + Relationships
    │  (LLM-based)  │  → resolution/classifier.py (dedup)
    └───────┬───────┘
            ↓
    ┌───────────────┐
    │  GRAPH BUILD  │  → graph/ER_Graph.pkl
    │  (NetworkX)   │  → graph/graph_preview.png
    └───────┬───────┘
            ↓
    ┌───────────────┐
    │  QUERY (RAG)  │  → interactive_query.py
    │               │  → query.py
    └───────────────┘
```

## Key Components

### Ingestion (`ingestion/`)
- Reads PDFs and text files
- Chunks text (500 chars with overlap)
- Generates embeddings via `nomic-embed-text`
- Stores in ChromaDB and SQLite

### Extraction (`extraction/`)
- Uses `llama3.1` with structured output (Pydantic)
- Extracts entities (people, orgs, locations)
- Extracts relationships between entities
- Handles missing entities through iterative refinement

### Resolution (`resolution/`)
- Detects duplicate entity names using XGBoost
- Features: fuzzy name matching + document co-occurrence
- Merges "John Wick" = "J. Wick" = "Wick" into single node

### Graph (`graph/`)
- NetworkX graph structure
- Nodes: entities with attributes (name, role)
- Edges: relationships with labels
- Visualization: matplotlib spring layout

### Retrieval (`retrieval/`)
- RAG (Retrieval-Augmented Generation) pipeline
- ChromaDB semantic search for context
- LLM generates cited answers
- No hallucination - grounded in source documents

## Entry Points

| File | Purpose | Usage |
|------|---------|-------|
| `run_full_ingestion.py` | Process all documents | `./venv/bin/python run_full_ingestion.py` |
| `interactive_query.py` | Ask questions interactively | `./venv/bin/python interactive_query.py` |
| `query.py` | Single question | `./venv/bin/python query.py "question"` |

## Generated Files (Gitignored)

- `data/intelligence.db` - SQLite database with entities/relationships
- `data/chromadb/` - Vector embeddings for semantic search
- `graph/ER_Graph.pkl` - NetworkX graph pickle
- `graph/graph_preview.png` - Visual graph rendering
- `*/__pycache__/` - Python bytecode cache

## Documentation

- `README.md` - Main project overview and quick start
- `USAGE.md` - Detailed usage instructions and examples
- `LINKEDIN_POST.md` - Social media post templates
- `PROJECT_STRUCTURE.md` - This file

## Dependencies

See `requirements.txt` for full list. Key dependencies:
- `ollama` - Local LLM inference
- `chromadb` - Vector database
- `networkx` - Graph data structure
- `xgboost` - Entity resolution classifier
- `matplotlib` - Graph visualization
- `pymupdf` - PDF reading
- `rapidfuzz` - Fuzzy string matching
