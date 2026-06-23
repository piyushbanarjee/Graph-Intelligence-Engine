#!/usr/bin/env python3
"""
Full Intelligence Pipeline Runner

Ingests all documents from 'Input Files' folder, extracts entities and relationships,
builds the knowledge graph, and generates a visualization.

Usage:
    python3 run_full_ingestion.py
    # or
    ./venv/bin/python run_full_ingestion.py
"""
import os
import glob
import time
from pathlib import Path

from ingestion.pipeline import ingest
from extraction.entity_extractor import extract_from_document
from graph.builder import add_all_entities, add_all_relationships, save_graph
from graph.visualizer import visualize_graph
import sqlite3


def main():
    print("=" * 70)
    print("🚀 OSINT GRAPH INTELLIGENCE ENGINE - FULL PIPELINE")
    print("=" * 70)
    
    # Configuration
    input_folder = "Input Files"
    supported_extensions = [".txt", ".pdf"]
    
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"\n❌ Error: '{input_folder}' folder not found!")
        print(f"   Please create it and add your documents.")
        return
    
    # Find all supported files
    input_files = []
    for ext in supported_extensions:
        input_files.extend(glob.glob(f"{input_folder}/*{ext}"))
    
    if not input_files:
        print(f"\n❌ No files found in '{input_folder}'")
        print(f"   Supported formats: {', '.join(supported_extensions)}")
        return
    
    print(f"\n📂 Found {len(input_files)} file(s) to process:")
    for f in input_files:
        print(f"   • {os.path.basename(f)}")
    
    # Track ingested document IDs
    ingested_doc_ids = []
    
    # Step 1: Ingest all documents
    print(f"\n{'=' * 70}")
    print("STEP 1: INGESTING DOCUMENTS")
    print("=" * 70)
    
    for i, filepath in enumerate(input_files, 1):
        filename = os.path.basename(filepath)
        print(f"\n[{i}/{len(input_files)}] Processing: {filename}")
        
        try:
            # Check if already ingested
            conn = sqlite3.connect('data/intelligence.db')
            cursor = conn.cursor()
            cursor.execute('SELECT document_id FROM documents WHERE filename = ?', (filename,))
            existing = cursor.fetchone()
            
            if existing:
                doc_id = existing[0]
                print(f"   ℹ️  Already ingested (document_id={doc_id}), skipping...")
                ingested_doc_ids.append(doc_id)
                conn.close()
                continue
            
            conn.close()
            
            # Ingest new document
            start = time.time()
            ingest(filepath)
            
            # Get the document_id that was just created
            conn = sqlite3.connect('data/intelligence.db')
            cursor = conn.cursor()
            cursor.execute('SELECT document_id FROM documents WHERE filename = ?', (filename,))
            doc_id = cursor.fetchone()[0]
            ingested_doc_ids.append(doc_id)
            conn.close()
            
            elapsed = time.time() - start
            print(f"   ✅ Ingested successfully (document_id={doc_id}) in {elapsed:.1f}s")
            
        except Exception as e:
            print(f"   ❌ Failed to ingest: {e}")
            continue
    
    if not ingested_doc_ids:
        print("\n⚠️  No documents to process. Exiting.")
        return
    
    # Step 2: Extract entities and relationships
    print(f"\n{'=' * 70}")
    print("STEP 2: EXTRACTING ENTITIES & RELATIONSHIPS")
    print("=" * 70)
    print("⏳ This may take several minutes depending on document size...")
    
    for i, doc_id in enumerate(ingested_doc_ids, 1):
        # Get filename for this doc_id
        conn = sqlite3.connect('data/intelligence.db')
        cursor = conn.cursor()
        cursor.execute('SELECT filename FROM documents WHERE document_id = ?', (doc_id,))
        filename = cursor.fetchone()[0]
        
        # Check if already extracted
        cursor.execute('SELECT COUNT(*) FROM entities WHERE document_id = ?', (doc_id,))
        entity_count = cursor.fetchone()[0]
        conn.close()
        
        if entity_count > 0:
            print(f"\n[{i}/{len(ingested_doc_ids)}] {filename} (doc_id={doc_id})")
            print(f"   ℹ️  Already extracted ({entity_count} entities), skipping...")
            continue
        
        print(f"\n[{i}/{len(ingested_doc_ids)}] {filename} (doc_id={doc_id})")
        
        try:
            start = time.time()
            extract_from_document(doc_id)
            elapsed = time.time() - start
            
            # Count extracted data
            conn = sqlite3.connect('data/intelligence.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM entities WHERE document_id = ?', (doc_id,))
            entity_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM relationships WHERE document_id = ?', (doc_id,))
            rel_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"   ✅ Extracted {entity_count} entities, {rel_count} relationships in {elapsed:.1f}s")
            
        except Exception as e:
            print(f"   ❌ Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Step 3: Build knowledge graph
    print(f"\n{'=' * 70}")
    print("STEP 3: BUILDING KNOWLEDGE GRAPH")
    print("=" * 70)
    
    try:
        print("🔨 Rebuilding graph from database...")
        add_all_entities()
        add_all_relationships()
        save_graph()
        
        # Count nodes and edges
        from graph.builder import load_graph
        G = load_graph()
        print(f"   ✅ Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
    except Exception as e:
        print(f"   ❌ Graph building failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 4: Generate visualization
    print(f"\n{'=' * 70}")
    print("STEP 4: GENERATING GRAPH VISUALIZATION")
    print("=" * 70)
    
    try:
        visualize_graph()
    except Exception as e:
        print(f"   ❌ Visualization failed: {e}")
    
    # Final summary
    print(f"\n{'=' * 70}")
    print("✅ PIPELINE COMPLETE")
    print("=" * 70)
    
    conn = sqlite3.connect('data/intelligence.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM documents')
    doc_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM entities')
    entity_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM relationships')
    rel_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n📊 Database Summary:")
    print(f"   • Documents:     {doc_count}")
    print(f"   • Entities:      {entity_count}")
    print(f"   • Relationships: {rel_count}")
    
    print(f"\n📁 Output Files:")
    print(f"   • Knowledge Graph: graph/ER_Graph.pkl")
    print(f"   • Visualization:   graph/graph_preview.png")
    print(f"   • Database:        data/intelligence.db")
    
    print(f"\n💬 To query the knowledge base:")
    print(f"   ./venv/bin/python test_retrieval.py")
    print(f"   # or use retrieval.retriever.answer_with_context()")
    

if __name__ == "__main__":
    main()
