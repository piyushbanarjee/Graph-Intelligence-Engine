# Quick Start - Alias Consolidation

## What Changed?

**Before**: Aliases like "John Wick", "Wick", and "J. Wick" created separate graph nodes.

**Now**: All aliases merge into one canonical entity with relationships consolidated.

---

## I'm Starting Fresh

Just use the system normally. Alias consolidation happens automatically:

```bash
# Process your documents
./venv/bin/python3 run_full_ingestion.py

# Query as usual
./venv/bin/python3 interactive_query.py
```

That's it! Aliases will be automatically detected and consolidated.

---

## I Have Existing Data

Run the migration script once to consolidate your existing entities:

```bash
# 1. Backup your database (just in case)
cp data/intelligence.db data/intelligence.db.backup

# 2. Run migration
./venv/bin/python3 migrate_aliases.py
```

Follow the prompts. The script will:
- Find duplicate entities
- Consolidate them under canonical names
- Update all relationships
- Rebuild your graph

---

## Verify It's Working

```bash
# Test the system (automated verification)
./venv/bin/python3 test_alias_system.py

# View your entities and their aliases
./venv/bin/python3 view_entities_with_aliases.py
```

---

## Example Output

```bash
$ ./venv/bin/python3 view_entities_with_aliases.py

================================================================================
ENTITIES WITH ALIASES
================================================================================

Entity: John Wick
  Role: person
  Aliases (2):
    - Wick (confidence: 0.950)
    - J. Wick (confidence: 0.920)

Entity: Continental Hotel
  Role: organization
  Aliases: None

Entity: Winston Scott
  Role: person
  Aliases (1):
    - Winston (confidence: 0.980)

================================================================================
GRAPH NODES WITH ATTRIBUTES
================================================================================

Node: John Wick
  Role: person
  Aliases (2):
    - Wick
    - J. Wick
  Connected to (2):
    - Marcus (relation: works with)
    - Continental Hotel (relation: eliminated at)
```

---

## Understanding the Output

### What You'll See in the Graph

**Single Canonical Node:**
- Only "John Wick" appears as a node (not "Wick" or "J. Wick")

**Alias Attributes:**
- Node has `aliases` attribute listing all variants
- Preserves the information about alternative names

**Consolidated Relationships:**
- All edges connect to the canonical node
- Complete view of all connections

---

## Configuration

### Resolution Threshold

The system uses a **0.9 confidence threshold** by default (in `resolution/classifier.py`):

```python
def resolve_entity(names, new_name, threshold=0.9):
```

- **Higher threshold (e.g., 0.95)**: Fewer aliases detected, more conservative
- **Lower threshold (e.g., 0.85)**: More aliases detected, more aggressive

Choose based on your data quality and risk tolerance.

---

## Troubleshooting

### "I still see duplicate nodes"

Run the migration:
```bash
./venv/bin/python3 migrate_aliases.py
```

### "Aliases aren't being detected"

Lower the threshold in `resolution/classifier.py`:
```python
def resolve_entity(names, new_name, threshold=0.85):  # Lower threshold
```

### "Wrong entities are being merged"

Raise the threshold in `resolution/classifier.py`:
```python
def resolve_entity(names, new_name, threshold=0.95):  # Higher threshold
```

---

## Need More Details?

- **Visual Example**: See `ALIAS_EXAMPLE.md`
- **Full Documentation**: See `ALIAS_CONSOLIDATION.md`
- **Changes Summary**: See `CHANGES_SUMMARY.md`
- **Project README**: See `README.md`

---

## Questions?

**Q: Will this change my existing data?**
A: Not until you run `migrate_aliases.py`. New documents automatically use the new system.

**Q: Can I undo the migration?**
A: Yes, if you backed up your database first. Just restore from backup.

**Q: How do I manually merge two entities?**
A: See the "Troubleshooting" section in `ALIAS_CONSOLIDATION.md`.

**Q: Does this affect query results?**
A: Yes, in a good way! Queries now return complete information across all aliases.
