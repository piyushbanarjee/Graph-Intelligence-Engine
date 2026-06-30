# OSINT Graph Intelligence Engine - Usage Guide

## Single-Command Full Pipeline

Process all documents in one go:

```bash
./venv/bin/python run_full_ingestion.py
```

This will:
1. ✅ Ingest all files from `input_files/` folder (PDF, TXT)
2. ✅ Extract entities and relationships using LLM
3. ✅ Build the knowledge graph
4. ✅ Generate a visualization PNG

---

## Step-by-Step Setup

### 1. Prepare Your Documents

Place all documents you want to analyze in the `input_files/` folder:

```bash
input_files/
├── document1.pdf
├── document2.txt
└── report.pdf
```

**Supported formats:** `.pdf`, `.txt`

### 2. Run the Full Pipeline

```bash
./venv/bin/python run_full_ingestion.py
```

**What happens:**
- Reads each file
- Chunks text into 500-character segments with overlap
- Embeds chunks using `nomic-embed-text` 
- Stores in ChromaDB for semantic search
- Extracts entities (people, orgs, locations) using `llama3.1`
- Extracts relationships between entities
- Resolves duplicate names (e.g., "John Wick" = "J. Wick")
- Builds NetworkX knowledge graph
- Generates visual graph PNG

**Time:** ~1-2 minutes per document depending on length

### 3. Query the Knowledge Base

**Option A: Interactive Session (Recommended)**
```bash
./venv/bin/python interactive_query.py
```
Keep asking questions until you type `exit`. Perfect for exploration!

**Option B: Single Question**
```bash
./venv/bin/python query.py "Who is John Wick?"
```

**Option C: From Python Code**
```python
from retrieval.retriever import answer_with_context

answer = answer_with_context(
    "What is the relationship between John Wick and Winston Scott?",
    n_results=5
)
print(answer)
```

---

## Output Files

After running the pipeline:

| File | Description |
|------|-------------|
| `data/intelligence.db` | SQLite database with documents, entities, relationships |
| `data/chromadb/` | Vector embeddings for semantic search |
| `output/ER_Graph.pkl` | NetworkX knowledge graph (Python pickle) |
| `output/graph_preview.png` | Visual graph visualization (PNG) |

---

## Features

### ✅ Smart Deduplication
The system detects when "John Wick", "J. Wick", and "Wick" refer to the same person and merges them into one entity.

### ✅ Incremental Processing
- Already ingested documents are skipped
- Already extracted entities are skipped
- You can add new files to `input_files/` and run again

### ✅ Source Citations
Answers cite which document chunks they're based on - no hallucination.

### ✅ Relationship Discovery
Finds both:
- **Direct connections:** Explicitly stated in text
- **Indirect connections:** Implied through graph traversal

---

## Command Reference

```bash
# Full pipeline (recommended)
./venv/bin/python run_full_ingestion.py

# Ingest single file manually
./venv/bin/python -m ingestion.pipeline "path/to/file.pdf"

# Extract entities from document ID 2
./venv/bin/python -c "from extraction.entity_extractor import extract_from_document; extract_from_document(2)"

# Rebuild graph from database
./venv/bin/python -c "from graph.builder import add_all_entities, add_all_relationships, save_graph; add_all_entities(); add_all_relationships(); save_graph()"

# Generate visualization
./venv/bin/python -m graph.visualizer

# Query the system
./venv/bin/python test_retrieval.py
```

---

## Prerequisites

1. **Ollama running** with models pulled:
   ```bash
   ollama pull llama3.1
   ollama pull nomic-embed-text
   ```

2. **Virtual environment** activated (or use `./venv/bin/python`)

---

## Database Schema

### documents
- `document_id` (primary key)
- `filename`
- `raw_text`
- `created_at`

### entities
- `entity_id` (primary key)
- `document_id` (foreign key)
- `name` (deduplicated canonical name)
- `role` (person, organization, location, etc.)
- `created_at`

### relationships
- `relation_id` (primary key)
- `document_id` (foreign key)
- `origin` (entity name)
- `destination` (entity name)
- `label` (relationship description)
- `created_at`

---

## Example Workflow

```bash
# 1. Add documents to process
cp ~/Downloads/dossier*.pdf "input_files/"

# 2. Run full pipeline
./venv/bin/python run_full_ingestion.py

# Expected output:
# ✅ Ingested 3 documents
# ✅ Extracted 45 entities
# ✅ Built graph with 45 nodes, 67 edges
# ✅ Generated output/graph_preview.png

# 3. View the graph
xdg-open output/graph_preview.png

# 4. Query the knowledge base
./venv/bin/python -c "
from retrieval.retriever import answer_with_context
print(answer_with_context('Who are the key players in the Continental?'))
"
```

---

## Troubleshooting

### "No files found in input_files"
Make sure you've created the folder and added documents:
```bash
mkdir -p "input_files"
cp your_document.pdf "input_files/"
```

### Ollama connection errors
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve
```

### Out of memory during extraction
Reduce the number of files or process them one at a time:
```bash
./venv/bin/python -m ingestion.pipeline "input_files/large_doc.pdf"
./venv/bin/python -c "from extraction.entity_extractor import extract_from_document; extract_from_document(1)"
```

---

## Next Steps

- View `output/graph_preview.png` to explore entity connections
- Query the system using `retrieval.retriever.answer_with_context()`
- Build a Streamlit UI for interactive exploration (see `README.md`)
- Add more documents to `input_files/` and run again
