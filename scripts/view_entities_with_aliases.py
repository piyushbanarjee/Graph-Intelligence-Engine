#!/usr/bin/env python3
"""
Utility script to view all entities with their aliases.
This helps verify that aliases are properly consolidated under canonical entities.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ingestion.store import get_all_entity_data, get_all_aliases
from graph.builder import load_graph

def view_entities_and_aliases():
    """Display all entities with their aliases."""
    entities, roles = get_all_entity_data()
    alias_map = get_all_aliases()
    
    print("\n" + "="*80)
    print("ENTITIES WITH ALIASES")
    print("="*80 + "\n")
    
    if not entities:
        print("No entities found in database.")
        return
    
    for entity, role in zip(entities, roles):
        aliases = alias_map.get(entity, [])
        
        print(f"Entity: {entity}")
        print(f"  Role: {role}")
        
        if aliases:
            print(f"  Aliases ({len(aliases)}):")
            for alias_name, confidence in aliases:
                print(f"    - {alias_name} (confidence: {confidence:.3f})")
        else:
            print("  Aliases: None")
        print()
    
    print("="*80)
    print(f"Total unique entities: {len(entities)}")
    print(f"Total aliases tracked: {sum(len(aliases) for aliases in alias_map.values())}")
    print("="*80 + "\n")

def view_graph_nodes():
    """Display graph nodes with their attributes including aliases."""
    try:
        G = load_graph()
        
        print("\n" + "="*80)
        print("GRAPH NODES WITH ATTRIBUTES")
        print("="*80 + "\n")
        
        if G.number_of_nodes() == 0:
            print("No nodes found in graph.")
            return
        
        for node, attrs in G.nodes(data=True):
            print(f"Node: {node}")
            print(f"  Role: {attrs.get('role', 'N/A')}")
            
            aliases = attrs.get('aliases', [])
            if aliases:
                print(f"  Aliases ({attrs.get('alias_count', 0)}):")
                for alias in aliases:
                    print(f"    - {alias}")
            else:
                print("  Aliases: None")
            
            # Show relationships
            neighbors = list(G.neighbors(node))
            if neighbors:
                print(f"  Connected to ({len(neighbors)}):")
                for neighbor in neighbors:
                    edge_data = G.get_edge_data(node, neighbor)
                    label = edge_data.get('label', 'N/A') if edge_data else 'N/A'
                    print(f"    - {neighbor} (relation: {label})")
            print()
        
        print("="*80)
        print(f"Total nodes: {G.number_of_nodes()}")
        print(f"Total edges: {G.number_of_edges()}")
        print("="*80 + "\n")
        
    except FileNotFoundError:
        print("Graph file not found. Please run entity extraction first.")
    except Exception as e:
        print(f"Error loading graph: {e}")

if __name__ == "__main__":
    print("Checking entities and aliases in database...")
    view_entities_and_aliases()
    
    print("\nChecking graph structure...")
    view_graph_nodes()
