#!/usr/bin/env python3
"""
Migration script to consolidate existing entities and rebuild the graph.
This script will:
1. Find duplicate entities that should be aliases
2. Consolidate them under canonical names
3. Update relationships to use canonical names
4. Rebuild the graph with proper alias tracking
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from resolution.classifier import resolve_entity
from ingestion.store import save_entity_alias, get_all_entity_data
from graph.builder import add_all_entities, add_all_relationships, save_graph, G

def migrate_existing_entities():
    """Migrate existing entities to use canonical names and track aliases."""
    db = sqlite3.connect('data/intelligence.db')
    cursor = db.cursor()
    
    print("Starting entity migration...")
    print("="*80)
    
    # Get all unique entity names
    cursor.execute("SELECT DISTINCT name FROM entities")
    all_names = [row[0] for row in cursor.fetchall()]
    
    print(f"\nFound {len(all_names)} unique entity names")
    
    # Build a mapping of all names to their canonical forms
    canonical_mapping = {}
    processed = set()
    
    for name in all_names:
        if name in processed:
            continue
        
        # Try to resolve against existing entities
        canonical_name, confidence = resolve_entity(list(processed), name)
        
        if canonical_name and confidence > 0.9:
            # This is an alias of an existing entity
            canonical_mapping[name] = canonical_name
            save_entity_alias(canonical_name, name, confidence)
            print(f"  Alias detected: '{name}' -> '{canonical_name}' (confidence: {confidence:.3f})")
        else:
            # This is a new canonical entity
            canonical_mapping[name] = name
            processed.add(name)
            print(f"  Canonical entity: '{name}'")
    
    print(f"\nTotal canonical entities: {len(processed)}")
    print(f"Total aliases found: {len(canonical_mapping) - len(processed)}")
    
    # Update entities table to use canonical names
    print("\nUpdating entities table...")
    for old_name, canonical_name in canonical_mapping.items():
        if old_name != canonical_name:
            cursor.execute("""
                UPDATE entities 
                SET name = ? 
                WHERE name = ?
            """, (canonical_name, old_name))
    
    db.commit()
    print("  Entities updated")
    
    # Update relationships table to use canonical names
    print("\nUpdating relationships table...")
    for old_name, canonical_name in canonical_mapping.items():
        if old_name != canonical_name:
            cursor.execute("""
                UPDATE relationships 
                SET origin = ? 
                WHERE origin = ?
            """, (canonical_name, old_name))
            
            cursor.execute("""
                UPDATE relationships 
                SET destination = ? 
                WHERE destination = ?
            """, (canonical_name, old_name))
    
    db.commit()
    print("  Relationships updated")
    
    # Remove duplicate entities (keeping one per canonical name per document)
    print("\nRemoving duplicate entities...")
    cursor.execute("""
        DELETE FROM entities 
        WHERE rowid NOT IN (
            SELECT MIN(rowid) 
            FROM entities 
            GROUP BY document_id, name
        )
    """)
    db.commit()
    deleted = cursor.rowcount
    print(f"  Removed {deleted} duplicate entries")
    
    db.close()
    
    print("\n" + "="*80)
    print("Migration complete!")
    print("="*80 + "\n")

def rebuild_graph():
    """Rebuild the graph with consolidated entities and aliases."""
    print("Rebuilding graph...")
    
    # Clear existing graph
    G.clear()
    
    # Rebuild with aliases
    add_all_entities()
    add_all_relationships()
    save_graph()
    
    print(f"Graph rebuilt: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print("="*80 + "\n")

if __name__ == "__main__":
    print("\nENTITY ALIAS MIGRATION TOOL")
    print("="*80)
    print("This will consolidate duplicate entities and rebuild the graph.")
    print("="*80 + "\n")
    
    response = input("Proceed with migration? (yes/no): ").strip().lower()
    
    if response == 'yes':
        try:
            migrate_existing_entities()
            from resolution.context_resolver import run_context_alias_resolution
            run_context_alias_resolution()
            rebuild_graph()
            print("\n✓ Migration completed successfully!")
            print("\nRun 'python scripts/view_entities_with_aliases.py' to view the results.")
        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Migration cancelled.")
