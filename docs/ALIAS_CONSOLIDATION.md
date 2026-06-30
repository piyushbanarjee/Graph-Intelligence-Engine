# Alias Consolidation Implementation

## Overview

The system now properly consolidates all aliases under a single canonical entity. This ensures that:
- **No duplicate nodes** exist in the knowledge graph for the same person/organization
- **All relationships** use the canonical entity name, not individual aliases
- **Alias information** is preserved and accessible as node attributes

## What Changed

### 1. Database Schema (`ingestion/store.py`)
- **New table:** `entity_aliases` tracks all alias mappings
  - `canonical_name`: The primary/canonical name for the entity
  - `alias_name`: The alternative name (alias)
  - `confidence`: Resolution confidence score (0.0 - 1.0)

- **New functions:**
  - `save_entity_alias()`: Store an alias mapping
  - `get_all_aliases()`: Retrieve all aliases grouped by canonical entity

### 2. Entity Extraction (`extraction/entity_extractor.py`)
- When an entity is resolved to a canonical name, the system now:
  1. Saves the entity using the **canonical name**
  2. Saves the alias mapping if the extracted name differs from canonical
  3. Updates all relationships to use **canonical names**

### 3. Graph Building (`graph/builder.py`)
- Graph nodes now include alias information as attributes:
  - `role`: Entity type (person, organization, etc.)
  - `aliases`: List of all known aliases for this entity
  - `alias_count`: Number of aliases tracked
- Relationships connect canonical entities, not individual aliases

## How It Works

### Example Flow

**Input Documents mention:**
- Document 1: "John Wick is a skilled assassin"
- Document 2: "Wick works with Marcus"
- Document 3: "J. Wick knows Winston"

**Without Alias Consolidation (Old Behavior):**
```
Graph has 3 separate nodes:
- "John Wick"
- "Wick" 
- "J. Wick"

Relationships are fragmented across these nodes.
```

**With Alias Consolidation (New Behavior):**
```
Graph has 1 canonical node:
- "John Wick"
  - aliases: ["Wick", "J. Wick"]
  - alias_count: 2

All relationships connect to "John Wick":
- "John Wick" → "Marcus" (label: works with)
- "John Wick" → "Winston" (label: knows)
```

## Usage

### View Entities and Aliases

Check which entities exist and what aliases they have:

```bash
python3 view_entities_with_aliases.py
```

**Output example:**
```
================================================================================
ENTITIES WITH ALIASES
================================================================================

Entity: John Wick
  Role: person
  Aliases (2):
    - Wick (confidence: 0.950)
    - J. Wick (confidence: 0.920)

Entity: Marcus
  Role: person
  Aliases: None

Entity: Winston Scott
  Role: person
  Aliases (1):
    - Winston (confidence: 0.980)

================================================================================
Total unique entities: 3
Total aliases tracked: 3
================================================================================
```

### Migrate Existing Data

If you have already processed documents before this update, run the migration script to consolidate existing entities:

```bash
python3 migrate_aliases.py
```

This will:
1. Analyze all existing entities for potential duplicates
2. Consolidate them under canonical names
3. Update all relationships to use canonical names
4. Build the alias tracking table
5. Rebuild the graph with proper alias attributes

**Important:** Back up your database before running migration:
```bash
cp data/intelligence.db data/intelligence.db.backup
```

### New Document Processing

When processing new documents, alias consolidation happens automatically:

```bash
python3 run_full_ingestion.py
```

The system will:
- Extract entities from each document chunk
- Resolve entities against existing canonical entities
- Track new aliases automatically
- Build relationships using canonical names

## Technical Details

### Resolution Confidence Threshold

The system uses a **0.9 confidence threshold** for entity resolution. This means:
- If similarity score ≥ 0.9 → treat as same entity (create alias mapping)
- If similarity score < 0.9 → treat as distinct entity

This conservative threshold prevents false merges that would corrupt the knowledge graph.

### Alias Storage

Aliases are stored with their confidence scores:
```sql
CREATE TABLE entity_aliases(
    alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT,
    alias_name TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(canonical_name, alias_name)
);
```

### Graph Node Attributes

Each node in the NetworkX graph includes:
```python
{
    "role": "person",              # Entity type
    "aliases": ["Wick", "J. Wick"], # List of aliases
    "alias_count": 2                # Number of aliases
}
```

### Relationship Mapping

Before saving relationships, names are mapped to canonical forms:
```python
# Resolution cache maps extracted names to canonical forms
canonical_name, confidence = resolve_entity([], extracted_name)
final_name = canonical_name if canonical_name else extracted_name

# Relationships use final_name (canonical)
save_relationships(
    document_id=doc_id,
    origin=final_name_origin,
    destination=final_name_dest,
    label=relationship_label
)
```

## Benefits

1. **Cleaner Knowledge Graph**
   - No duplicate nodes cluttering the visualization
   - Clear, consolidated entity representation

2. **Accurate Relationship Tracking**
   - All connections point to the same canonical entity
   - Multi-hop graph traversal works correctly

3. **Preserved Information**
   - Original alias names are not lost
   - Confidence scores track resolution quality
   - Can trace back to source document mentions

4. **Better Query Results**
   - Queries for "John Wick" return all information
   - No need to search multiple name variants
   - Graph traversal finds all connections

## Files Modified

1. **`ingestion/store.py`**
   - Added `entity_aliases` table schema
   - Added `save_entity_alias()` function
   - Added `get_all_aliases()` function

2. **`extraction/entity_extractor.py`**
   - Import `save_entity_alias`
   - Save alias mappings when entities are resolved
   - Use canonical names in relationships

3. **`graph/builder.py`**
   - Import `get_all_aliases`
   - Include alias information in node attributes
   - Add alias metadata to graph nodes

## New Files

1. **`view_entities_with_aliases.py`**
   - Utility to view all entities with their aliases
   - Shows both database and graph representations

2. **`migrate_aliases.py`**
   - Migration script for existing data
   - Consolidates duplicate entities
   - Rebuilds graph with alias tracking

3. **`ALIAS_CONSOLIDATION.md`** (this file)
   - Complete documentation of the alias system

## Troubleshooting

### "I still see duplicate nodes in my graph"

Run the migration script to consolidate existing data:
```bash
python3 migrate_aliases.py
```

### "Aliases aren't being detected"

Check the resolution confidence threshold in `resolution/classifier.py`:
```python
def resolve_entity(names, new_name, threshold=0.9):
```

Lower threshold = more aggressive merging (more aliases detected)
Higher threshold = more conservative (fewer aliases, fewer false positives)

### "I want to manually merge two entities"

You can manually add an alias mapping:
```python
from ingestion.store import save_entity_alias
save_entity_alias(
    canonical_name="John Wick",
    alias_name="Baba Yaga", 
    confidence=1.0
)
```

Then rebuild the graph:
```python
from graph.builder import add_all_entities, add_all_relationships, save_graph, G
G.clear()
add_all_entities()
add_all_relationships()
save_graph()
```

## Future Enhancements

1. **Interactive Alias Management**
   - UI to review and approve/reject alias suggestions
   - Manual merge/split capabilities

2. **Co-occurrence Boosting**
   - Use document co-occurrence to improve resolution
   - Entities mentioned together likely refer to same person

3. **Context-Aware Resolution**
   - Consider entity roles and relationships in resolution
   - "John Smith (CEO)" vs "John Smith (Engineer)" = different people

4. **Alias Provenance**
   - Track which document first introduced each alias
   - Show alias usage frequency across documents
