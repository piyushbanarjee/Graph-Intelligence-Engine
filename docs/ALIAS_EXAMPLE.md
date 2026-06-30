# Alias Consolidation - Visual Example

## Scenario

You have three documents mentioning the same person with different names:

**Document 1:**
```
John Wick is a legendary assassin working with Marcus.
```

**Document 2:**
```
Wick eliminated 12 targets at the Continental Hotel.
```

**Document 3:**
```
J. Wick has a professional relationship with Winston Scott.
```

---

## OLD BEHAVIOR (Before Alias Consolidation)

### Extracted Entities
```
From Doc 1: "John Wick", "Marcus", "Continental Hotel"
From Doc 2: "Wick", "Continental Hotel"
From Doc 3: "J. Wick", "Winston Scott", "Continental Hotel"
```

### Database Storage
```
entities table:
┌────┬─────────────┬─────────────────────┬──────────────┐
│ id │ document_id │ name                │ role         │
├────┼─────────────┼─────────────────────┼──────────────┤
│ 1  │ 1           │ John Wick           │ person       │
│ 2  │ 1           │ Marcus              │ person       │
│ 3  │ 1           │ Continental Hotel   │ organization │
│ 4  │ 2           │ Wick                │ person       │ ← DUPLICATE!
│ 5  │ 2           │ Continental Hotel   │ organization │
│ 6  │ 3           │ J. Wick             │ person       │ ← DUPLICATE!
│ 7  │ 3           │ Winston Scott       │ person       │
│ 8  │ 3           │ Continental Hotel   │ organization │
└────┴─────────────┴─────────────────────┴──────────────┘

relationships table:
┌────┬─────────────┬───────────────────┬──────────────┬──────────────────┐
│ id │ document_id │ origin            │ destination  │ label            │
├────┼─────────────┼───────────────────┼──────────────┼──────────────────┤
│ 1  │ 1           │ John Wick         │ Marcus       │ works with       │
│ 2  │ 2           │ Wick              │ Cont. Hotel  │ eliminated at    │
│ 3  │ 3           │ J. Wick           │ Winston S.   │ professional rel.│
└────┴─────────────┴───────────────────┴──────────────┴──────────────────┘
```

### Knowledge Graph
```
           Marcus
             ↑
             │ works with
             │
         John Wick


         Wick ──eliminated at──→ Continental Hotel


         J. Wick ──professional rel.──→ Winston Scott
```

**Problems:**
- ❌ Three separate nodes for the same person!
- ❌ Fragmented relationships across different nodes
- ❌ Can't see the full network of connections
- ❌ Query for "John Wick" misses connections from "Wick" and "J. Wick"

---

## NEW BEHAVIOR (With Alias Consolidation)

### Entity Resolution Process
```
1. Extract "John Wick" → No existing match → Create canonical entity
2. Extract "Marcus" → No existing match → Create canonical entity
3. Extract "Continental Hotel" → No existing match → Create canonical entity

4. Extract "Wick" → Match "John Wick" (confidence: 0.95) → Use canonical name
   └─→ Save alias mapping: "Wick" is alias of "John Wick"

5. Extract "J. Wick" → Match "John Wick" (confidence: 0.92) → Use canonical name
   └─→ Save alias mapping: "J. Wick" is alias of "John Wick"

6. Extract "Winston Scott" → No existing match → Create canonical entity
```

### Database Storage
```
entities table:
┌────┬─────────────┬───────────────────┬──────────────┐
│ id │ document_id │ name              │ role         │
├────┼─────────────┼───────────────────┼──────────────┤
│ 1  │ 1           │ John Wick         │ person       │ ← CANONICAL
│ 2  │ 1           │ Marcus            │ person       │
│ 3  │ 1           │ Continental Hotel │ organization │
│ 4  │ 2           │ John Wick         │ person       │ ← Same canonical
│ 5  │ 2           │ Continental Hotel │ organization │
│ 6  │ 3           │ John Wick         │ person       │ ← Same canonical
│ 7  │ 3           │ Winston Scott     │ person       │
│ 8  │ 3           │ Continental Hotel │ organization │
└────┴─────────────┴───────────────────┴──────────────┘

entity_aliases table (NEW!):
┌────┬────────────────┬────────────┬────────────┐
│ id │ canonical_name │ alias_name │ confidence │
├────┼────────────────┼────────────┼────────────┤
│ 1  │ John Wick      │ Wick       │ 0.95       │
│ 2  │ John Wick      │ J. Wick    │ 0.92       │
└────┴────────────────┴────────────┴────────────┘

relationships table:
┌────┬─────────────┬───────────────────┬──────────────┬──────────────────┐
│ id │ document_id │ origin            │ destination  │ label            │
├────┼─────────────┼───────────────────┼──────────────┼──────────────────┤
│ 1  │ 1           │ John Wick         │ Marcus       │ works with       │
│ 2  │ 2           │ John Wick         │ Cont. Hotel  │ eliminated at    │
│ 3  │ 3           │ John Wick         │ Winston S.   │ professional rel.│
└────┴─────────────┴───────────────────┴──────────────┴──────────────────┘
                      ↑               ↑
                      All use canonical name!
```

### Knowledge Graph
```
                    Marcus
                      ↑
                      │ works with
                      │
                  John Wick ──eliminated at──→ Continental Hotel
                   (person)
                   aliases:
                   • Wick
                   • J. Wick
                      │
                      │ professional rel.
                      ↓
                 Winston Scott
```

**Benefits:**
- ✅ Single node representing the real person
- ✅ All relationships consolidated
- ✅ Complete view of connections
- ✅ Query for any name variant returns all information
- ✅ Alias information preserved for traceability

---

## Graph Node Attributes

### Old Structure
```python
# Three separate nodes, no connection between them
{
    "John Wick": {"role": "person"},
    "Wick": {"role": "person"},
    "J. Wick": {"role": "person"}
}
```

### New Structure
```python
# One node with alias information
{
    "John Wick": {
        "role": "person",
        "aliases": ["Wick", "J. Wick"],
        "alias_count": 2
    }
}
```

---

## Querying Examples

### Semantic Search Query: "What did John Wick do?"

**Old Behavior:**
```
Only finds chunks mentioning "John Wick" exactly
Misses information from chunks mentioning "Wick" or "J. Wick"
→ Incomplete answer
```

**New Behavior:**
```
Finds entity "John Wick" in graph
Sees all relationships connected to this node
Can include context from all aliases
→ Complete answer covering all mentions
```

### Graph Traversal Query: "How is Marcus connected to Winston Scott?"

**Old Behavior:**
```
Marcus → John Wick (connected)
John Wick → ? (no connection to Winston)
→ Path not found
```

**New Behavior:**
```
Marcus → John Wick → Winston Scott
      (works with)  (professional rel.)
→ Path found! 2 hops
```

---

## Command Examples

### Check Your Current Data
```bash
# See all entities and their aliases
./venv/bin/python3 view_entities_with_aliases.py
```

**Sample Output:**
```
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
```

### Migrate Existing Data
```bash
# If you have old data, consolidate it
./venv/bin/python3 migrate_aliases.py
```

### Test the System
```bash
# Verify everything works correctly
./venv/bin/python3 test_alias_system.py
```

---

## Technical Flow

```
Document Chunk
      ↓
Entity Extraction (LLM)
  "Wick" extracted
      ↓
Entity Resolution (XGBoost)
  Compare "Wick" vs all existing entities
  → Best match: "John Wick" (confidence: 0.95)
  → Threshold check: 0.95 ≥ 0.9 ✓
      ↓
Save to Database
  entities table: INSERT name="John Wick" (canonical)
  entity_aliases table: INSERT canonical="John Wick", alias="Wick"
      ↓
Relationship Extraction (LLM)
  "Wick eliminated at Continental Hotel"
      ↓
Relationship Resolution
  origin="Wick" → resolve → "John Wick" (canonical)
  destination="Continental Hotel" → no alias → keep as-is
      ↓
Save to Database
  relationships table: INSERT origin="John Wick", destination="Continental Hotel"
      ↓
Build Knowledge Graph
  Node: "John Wick" with aliases=["Wick"]
  Edge: "John Wick" → "Continental Hotel"
```

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Nodes** | Multiple per entity | One per entity |
| **Relationships** | Fragmented | Consolidated |
| **Aliases** | Lost | Tracked with confidence |
| **Query Results** | Incomplete | Complete |
| **Graph Traversal** | Broken paths | Connected paths |
| **Traceability** | None | Full provenance |
