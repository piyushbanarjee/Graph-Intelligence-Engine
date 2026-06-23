#!/usr/bin/env python3
"""
OSINT Graph Intelligence Engine - Complete Workflow

This script runs the entire pipeline in sequence:
1. Ingests all documents from 'Input Files/'
2. Extracts entities and builds knowledge graph
3. Opens the graph visualization
4. Launches interactive query interface

Usage:
    ./venv/bin/python run.py
"""
import os
import glob
import time
import sqlite3
import subprocess
import platform
from pathlib import Path

from ingestion.pipeline import ingest
from extraction.entity_extractor import extract_from_document
from graph.builder import add_all_entities, add_all_relationships, save_graph
from graph.visualizer import visualize_graph
from retrieval.retriever import answer_with_context


def open_file(filepath):
    """Open a file with the default system application"""
    system = platform.system()
    try:
        if system == 'Darwin':  # macOS
            subprocess.run(['open', filepath], check=True)
        elif system == 'Windows':
            os.startfile(filepath)
        else:  # Linux and others
            subprocess.run(['xdg-open', filepath], check=True)
        return True
    except Exception as e:
        print(f"   ⚠️  Could not auto-open file: {e}")
        print(f"   📁 Please manually open: {filepath}")
        return False


def run_ingestion_pipeline():
    """Step 1: Ingest all documents from Input Files folder"""
    print("\n" + "=" * 70)
    print("STEP 1: DOCUMENT INGESTION & ENTITY EXTRACTION")
    print("=" * 70)
    
    input_folder = "Input Files"
    supported_extensions = [".txt", ".pdf"]
    
    if not os.path.exists(input_folder):
        print(f"\n❌ Error: '{input_folder}' folder not found!")
        print(f"   Creating it now...")
        os.makedirs(input_folder)
        print(f"\n   Please add your documents to '{input_folder}/' and run again.")
        return False
    
    # Find all supported files
    input_files = []
    for ext in supported_extensions:
        input_files.extend(glob.glob(f"{input_folder}/*{ext}"))
    
    if not input_files:
        print(f"\n❌ No files found in '{input_folder}'")
        print(f"   Supported formats: {', '.join(supported_extensions)}")
        print(f"\n   Add documents and run again.")
        return False
    
    print(f"\n📂 Found {len(input_files)} file(s) to process:")
    for f in input_files:
        print(f"   • {os.path.basename(f)}")
    
    ingested_doc_ids = []
    
    # Ingest all documents
    for i, filepath in enumerate(input_files, 1):
        filename = os.path.basename(filepath)
        print(f"\n[{i}/{len(input_files)}] Processing: {filename}")
        
        try:
            conn = sqlite3.connect('data/intelligence.db')
            cursor = conn.cursor()
            cursor.execute('SELECT document_id FROM documents WHERE filename = ?', (filename,))
            existing = cursor.fetchone()
            
            if existing:
                doc_id = existing[0]
                print(f"   ℹ️  Already ingested (document_id={doc_id})")
                ingested_doc_ids.append(doc_id)
                conn.close()
                continue
            
            conn.close()
            
            start = time.time()
            ingest(filepath)
            
            conn = sqlite3.connect('data/intelligence.db')
            cursor = conn.cursor()
            cursor.execute('SELECT document_id FROM documents WHERE filename = ?', (filename,))
            doc_id = cursor.fetchone()[0]
            ingested_doc_ids.append(doc_id)
            conn.close()
            
            elapsed = time.time() - start
            print(f"   ✅ Ingested in {elapsed:.1f}s (document_id={doc_id})")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            continue
    
    if not ingested_doc_ids:
        print("\n⚠️  No documents to process.")
        return False
    
    # Extract entities and relationships
    print(f"\n{'=' * 70}")
    print("⏳ Extracting entities and relationships (may take a few minutes)...")
    print("=" * 70)
    
    for i, doc_id in enumerate(ingested_doc_ids, 1):
        conn = sqlite3.connect('data/intelligence.db')
        cursor = conn.cursor()
        cursor.execute('SELECT filename FROM documents WHERE document_id = ?', (doc_id,))
        filename = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM entities WHERE document_id = ?', (doc_id,))
        entity_count = cursor.fetchone()[0]
        conn.close()
        
        if entity_count > 0:
            print(f"[{i}/{len(ingested_doc_ids)}] {filename}: Already extracted ({entity_count} entities)")
            continue
        
        print(f"[{i}/{len(ingested_doc_ids)}] {filename}: Extracting...")
        
        try:
            start = time.time()
            extract_from_document(doc_id)
            elapsed = time.time() - start
            
            conn = sqlite3.connect('data/intelligence.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM entities WHERE document_id = ?', (doc_id,))
            entity_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM relationships WHERE document_id = ?', (doc_id,))
            rel_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"   ✅ {entity_count} entities, {rel_count} relationships ({elapsed:.1f}s)")
            
        except Exception as e:
            print(f"   ❌ Extraction failed: {e}")
            continue
    
    # Build knowledge graph
    print(f"\n{'=' * 70}")
    print("Building knowledge graph...")
    print("=" * 70)
    
    try:
        add_all_entities()
        add_all_relationships()
        save_graph()
        
        from graph.builder import load_graph
        G = load_graph()
        print(f"✅ Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
    except Exception as e:
        print(f"❌ Graph building failed: {e}")
        return False
    
    # Generate visualization
    print(f"\nGenerating visualization...")
    
    try:
        visualize_graph()
    except Exception as e:
        print(f"❌ Visualization failed: {e}")
    
    # Show summary
    conn = sqlite3.connect('data/intelligence.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM documents')
    doc_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM entities')
    entity_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM relationships')
    rel_count = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n{'=' * 70}")
    print("✅ PIPELINE COMPLETE")
    print("=" * 70)
    print(f"\n📊 Knowledge Base:")
    print(f"   • Documents:     {doc_count}")
    print(f"   • Entities:      {entity_count}")
    print(f"   • Relationships: {rel_count}")
    
    return True


def show_graph():
    """Step 2: Open the graph visualization"""
    print(f"\n{'=' * 70}")
    print("STEP 2: OPENING GRAPH VISUALIZATION")
    print("=" * 70)
    
    graph_path = "graph/graph_preview.png"
    
    if not os.path.exists(graph_path):
        print(f"\n⚠️  Graph visualization not found at {graph_path}")
        return
    
    print(f"\n📊 Opening graph visualization...")
    open_file(graph_path)


def interactive_query():
    """Step 3: Launch interactive query interface"""
    print(f"\n{'=' * 70}")
    print("STEP 3: INTERACTIVE QUERY INTERFACE")
    print("=" * 70)
    print("\nAsk questions about your documents.")
    print("Type 'help' for examples, 'exit' to quit.\n")
    
    while True:
        try:
            question = input("❓ Your question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            if question.lower() in ['help', 'h', '?']:
                print("\n💡 Example questions:")
                print("  • Who is John Wick?")
                print("  • What is the relationship between X and Y?")
                print("  • Tell me about the Continental")
                print("  • What happened during the siege?")
                print()
                continue
            
            print("\n🔍 Searching knowledge base...")
            
            try:
                answer = answer_with_context(
                    question,
                    n_results=5,
                    model="llama3.1"
                )
                
                print("\n📝 Answer:")
                print("-" * 70)
                print(answer)
                print("-" * 70)
                print()
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Make sure Ollama is running with llama3.1 model.\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        
        except EOFError:
            print("\n\n👋 Goodbye!\n")
            break


def main():
    """Main workflow orchestrator"""
    print("\n" + "=" * 70)
    print("🔍 OSINT GRAPH INTELLIGENCE ENGINE")
    print("=" * 70)
    print("\nThis will:")
    print("  1. Process all documents in 'Input Files/'")
    print("  2. Build and visualize the knowledge graph")
    print("  3. Launch interactive query interface")
    print()
    
    # Step 1: Run ingestion pipeline
    success = run_ingestion_pipeline()
    
    if not success:
        print("\n⚠️  Pipeline did not complete successfully.")
        print("   Please check the errors above and try again.")
        return
    
    # Step 2: Show graph
    show_graph()
    
    # Small delay to let graph window open
    time.sleep(1)
    
    # Step 3: Interactive queries
    interactive_query()


if __name__ == "__main__":
    main()
