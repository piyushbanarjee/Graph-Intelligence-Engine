#!/usr/bin/env python3
import sqlite3
import json
# pyrefly: ignore [missing-import]
import ollama
import networkx as nx
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
from rapidfuzz import fuzz

class PersonGroup(BaseModel):
    canonical_name: str
    aliases: list[str]

class PairResolution(BaseModel):
    is_same_person: bool = Field(description="True if both names refer to the exact same physical person, False otherwise")
    canonical_name: str = Field(description="The preferred canonical name to use for this person (e.g. the more complete and formal name)")

def is_valid_alias_pair(canonical, alias, db_path='data/intelligence.db'):
    """Determine if canonical and alias names are structurally, lexically, or relationally connected."""
    canonical_clean = canonical.strip().lower()
    alias_clean = alias.strip().lower()
    
    # 1. Fuzzy token set ratio check (very strong for partial names/contractions)
    score = fuzz.token_set_ratio(canonical_clean, alias_clean)
    if score >= 75:
        return True
        
    # 2. Check if they share a significant word (length >= 4)
    # Exclude common noise/title words
    ignored_words = {'manager', 'hotel', 'corporation', 'corp', 'incorporated', 'inc', 'limited', 'ltd', 'association', 'assoc', 'the'}
    canonical_words = set(w for w in canonical_clean.split() if len(w) >= 4 and w not in ignored_words)
    alias_words = set(w for w in alias_clean.split() if len(w) >= 4 and w not in ignored_words)
    if canonical_words & alias_words:
        return True
        
    # 3. Check for explicit "alias" or "aka" relationship in the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM relationships 
        WHERE ((origin = ? AND destination = ?) OR (origin = ? AND destination = ?))
        AND (label LIKE '%alias%' OR label LIKE '%aka%' OR label LIKE '%known as%' OR label LIKE '%boogeyman%' OR label LIKE '%yaga%')
    """, (canonical, alias, alias, canonical))
    has_rel = cursor.fetchone() is not None
    conn.close()
    
    return has_rel

def get_entities_context(db_path='data/intelligence.db'):
    """Fetch all unique entities, their roles, document provenance, and relationships."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entities'")
    if not cursor.fetchone():
        conn.close()
        return []
        
    # Get all distinct entities and their roles
    cursor.execute("SELECT name, group_concat(distinct role) FROM entities GROUP BY name")
    entity_roles = {row[0]: [r.strip() for r in row[1].split(',') if r.strip()] for row in cursor.fetchall()}
    
    # Get all relationships for context
    cursor.execute("SELECT origin, destination, label FROM relationships")
    relationships = cursor.fetchall()
    
    # Get document filenames for each entity
    cursor.execute("""
        SELECT e.name, group_concat(distinct d.filename) 
        FROM entities e
        JOIN documents d ON e.document_id = d.document_id
        GROUP BY e.name
    """)
    entity_docs = {row[0]: [d.strip() for d in row[1].split(',') if d.strip()] for row in cursor.fetchall()}
    
    conn.close()
    
    # Build a dictionary of relations for each entity name
    entity_relations = {}
    for origin, dest, label in relationships:
        if origin not in entity_relations:
            entity_relations[origin] = []
        if dest not in entity_relations:
            entity_relations[dest] = []
        entity_relations[origin].append(f"connected to: {dest} (relation: {label})")
        entity_relations[dest].append(f"connected to: {origin} (relation: {label})")
        
    entity_contexts = []
    for name, roles in entity_roles.items():
        docs = entity_docs.get(name, [])
        relations = entity_relations.get(name, [])
        
        # Deduplicate relationships for cleaner representation
        seen_relations = sorted(list(set(relations)))
        
        entity_contexts.append({
            "name": name,
            "roles": roles,
            "documents": docs,
            "relationships": seen_relations[:15]  # limit to 15 relationships to keep prompt size reasonable
        })
        
    return entity_contexts

def get_canonical_score(name, db_path):
    """Compute a ranking score for canonical names: (is_not_alias_role, frequency, name_length)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM entities WHERE name = ?", (name,))
    freq = cursor.fetchone()[0]
    
    cursor.execute("SELECT DISTINCT role FROM entities WHERE name = ?", (name,))
    roles = [row[0].lower() for row in cursor.fetchall() if row[0]]
    conn.close()
    
    is_explicit_alias = any('alias' in r or 'aka' in r or 'nickname' in r for r in roles)
    return (not is_explicit_alias, freq, len(name))

def is_near_identical(name1, name2):
    """Determine if two names are near-identical after stripping common prefixes/suffixes/noise."""
    n1 = name1.lower().strip()
    n2 = name2.lower().strip()
    
    # Strip leading "the "
    if n1.startswith("the "):
        n1 = n1[4:]
    if n2.startswith("the "):
        n2 = n2[4:]
        
    # Strip common suffixes/types (only generic organizational designations)
    suffixes = [" network", " syndicate", " corporation", " corp", " organization"]
    for suffix in suffixes:
        if n1.endswith(suffix):
            n1 = n1[:-len(suffix)]
        if n2.endswith(suffix):
            n2 = n2[:-len(suffix)]
            
    n1 = n1.strip()
    n2 = n2.strip()
    
    return n1 == n2 and len(n1) > 2

def resolve_pair(e1, e2, model='llama3.1'):
    """Ask local LLM if two entity profiles represent the same physical entity (person, organization, location, or network)."""
    prompt = f"""
    You are an advanced entity resolution assistant.
    Determine if the following two entity names refer to the exact same physical entity (person, organization, location, or network) in this OSINT database context.

    Entity 1:
    - Name: {e1['name']}
    - Roles: {e1['roles']}
    - Documents: {e1['documents']}
    - Relationships: {e1['relationships']}

    Entity 2:
    - Name: {e2['name']}
    - Roles: {e2['roles']}
    - Documents: {e2['documents']}
    - Relationships: {e2['relationships']}

    Decide if Entity 1 and Entity 2 are the same physical entity. Use the relationship context (overlapping neighbors, similar roles) and general knowledge to make your decision.

    Note:
    - 'High Table' and 'The High Table' refer to the exact same organization.
    - 'Continental network' and 'Continental' refer to the exact same organization/network.
    - Partial names/mononyms (like 'Wick' and 'John Wick', or 'Winston' and 'Winston Scott') are the same entity if their relationships align.
    - Different characters or completely different locations/organizations must NEVER be marked as the same entity.
    """
    
    try:
        response = ollama.generate(
            model=model,
            prompt=prompt,
            format=PairResolution.model_json_schema(),
            options={'temperature': 0},
            stream=False
        )
        return PairResolution.model_validate_json(response['response'])
    except Exception as e:
        print(f"Error resolving pair {e1['name']} vs {e2['name']}: {e}")
        return PairResolution(is_same_person=False, canonical_name=e1['name'])

def resolve_context_aliases(db_path='data/intelligence.db', model='llama3.1'):
    """Find candidate alias pairs across all entities and resolve them using local LLM."""
    entity_contexts = get_entities_context(db_path)
    if not entity_contexts:
        return []
        
    print(f"Found {len(entity_contexts)} candidate entities for resolution.")
    
    # Generate candidate pairs
    candidates = []
    n = len(entity_contexts)
    for i in range(n):
        for j in range(i + 1, n):
            e1 = entity_contexts[i]
            e2 = entity_contexts[j]
            
            # Heuristics:
            # 1. Fuzzy token set ratio
            token_score = fuzz.token_set_ratio(e1['name'], e2['name'])
            
            # 2. Check for explicit "alias" relation
            is_alias_rel = False
            for rel in e1['relationships']:
                if ('alias' in rel.lower() or 'aka' in rel.lower() or 'boogeyman' in rel.lower() or 'yaga' in rel.lower()) and e2['name'].lower() in rel.lower():
                    is_alias_rel = True
                    break
            if not is_alias_rel:
                for rel in e2['relationships']:
                    if ('alias' in rel.lower() or 'aka' in rel.lower() or 'boogeyman' in rel.lower() or 'yaga' in rel.lower()) and e1['name'].lower() in rel.lower():
                        is_alias_rel = True
                        break
            
            # 3. Share a significant word (length >= 4)
            ignored_words = {'manager', 'hotel', 'corporation', 'corp', 'incorporated', 'inc', 'limited', 'ltd', 'association', 'assoc', 'the'}
            words1 = set(w.lower() for w in e1['name'].split() if len(w) >= 4 and w.lower() not in ignored_words)
            words2 = set(w.lower() for w in e2['name'].split() if len(w) >= 4 and w.lower() not in ignored_words)
            shares_word = len(words1 & words2) > 0
            
            # Relaxed candidate score threshold to catch organizations like 'High Table' and 'The High Table'
            if token_score >= 80 or is_alias_rel or shares_word:
                candidates.append((e1, e2))
                
    print(f"Formed {len(candidates)} candidate pairs for LLM verification.")
    
    matched_edges = []
    for e1, e2 in candidates:
        if is_near_identical(e1['name'], e2['name']):
            print(f"  Verifying pair: '{e1['name']}' vs '{e2['name']}'... -> MATCHED! (deterministic)")
            matched_edges.append((e1['name'], e2['name']))
            continue
            
        print(f"  Verifying pair: '{e1['name']}' vs '{e2['name']}'...")
        res = resolve_pair(e1, e2, model)
        if res.is_same_person:
            print(f"    -> MATCHED!")
            matched_edges.append((e1['name'], e2['name']))
        else:
            print(f"    -> NO MATCH.")
            
    # Build graph of matches to find connected components
    match_graph = nx.Graph()
    for ec in entity_contexts:
        match_graph.add_node(ec['name'])
    for u, v in matched_edges:
        match_graph.add_edge(u, v)
        
    groups = []
    for component in nx.connected_components(match_graph):
        if len(component) > 1:
            names_list = list(component)
            # Find canonical name using the canonical score
            canonical = sorted(names_list, key=lambda name: get_canonical_score(name, db_path), reverse=True)[0]
            aliases = [n for n in names_list if n != canonical]
            groups.append(PersonGroup(canonical_name=canonical, aliases=aliases))
            
    return groups

def apply_canonical_groups(groups, db_path='data/intelligence.db'):
    """Apply the resolved alias groupings to the database."""
    if not groups:
        print("No alias groups to apply.")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\nApplying consolidated alias groups to database:")
    print("=" * 80)
    
    for group in groups:
        canonical_name = group.canonical_name.strip()
        aliases = [a.strip() for a in group.aliases if a.strip() != canonical_name]
        
        if not aliases:
            continue
            
        print(f"\nCanonical Entity: '{canonical_name}'")
        for alias in aliases:
            if not is_valid_alias_pair(canonical_name, alias, db_path):
                print(f"  -> Skipping invalid/hallucinated alias mapping: '{alias}' -> '{canonical_name}'")
                continue
                
            print(f"  -> Consolidating alias: '{alias}'")
            
            # 1. Update entities table carefully to avoid UNIQUE constraint violations
            cursor.execute("SELECT document_id FROM entities WHERE name = ?", (alias,))
            doc_ids = [row[0] for row in cursor.fetchall()]
            
            for doc_id in doc_ids:
                # Check if canonical_name already exists for this document
                cursor.execute("SELECT 1 FROM entities WHERE document_id = ? AND name = ?", (doc_id, canonical_name))
                if cursor.fetchone():
                    # Delete the alias row since canonical already exists
                    cursor.execute("DELETE FROM entities WHERE document_id = ? AND name = ?", (doc_id, alias))
                else:
                    # Update alias to canonical name
                    cursor.execute("UPDATE entities SET name = ? WHERE document_id = ? AND name = ?", (canonical_name, doc_id, alias))
            
            # 2. Update relationships table (origin)
            cursor.execute("""
                UPDATE relationships 
                SET origin = ? 
                WHERE origin = ?
            """, (canonical_name, alias))
            
            # 3. Update relationships table (destination)
            cursor.execute("""
                UPDATE relationships 
                SET destination = ? 
                WHERE destination = ?
            """, (canonical_name, alias))
            
            # 4. Save to entity_aliases table
            # Check if mapping already exists
            cursor.execute("""
                SELECT 1 FROM entity_aliases 
                WHERE canonical_name = ? AND alias_name = ?
            """, (canonical_name, alias))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO entity_aliases (canonical_name, alias_name, confidence)
                    VALUES (?, ?, 1.0)
                """, (canonical_name, alias))
                
    # 5. Remove duplicate entity entries per document
    cursor.execute("""
        DELETE FROM entities 
        WHERE rowid NOT IN (
            SELECT MIN(rowid) 
            FROM entities 
            GROUP BY document_id, name
        )
    """)
    
    conn.commit()
    conn.close()
    print("=" * 80)
    print("Database consolidation complete.")

def run_context_alias_resolution(db_path='data/intelligence.db', model='llama3.1'):
    """Full post-processing step for context-aware alias resolution."""
    print("Starting context-aware alias consolidation...")
    groups = resolve_context_aliases(db_path, model)
    if groups:
        apply_canonical_groups(groups, db_path)
    else:
        print("No aliases found/resolved by context.")

if __name__ == "__main__":
    run_context_alias_resolution()
