#!/usr/bin/env python3
"""
Interactive Query Interface for OSINT Graph Intelligence Engine

Launch an interactive session where you can ask questions continuously.
Type 'exit' or 'quit' to end the session.

Usage:
    ./venv/bin/python interactive_query.py
"""
from retrieval.retriever import answer_with_context
import sys

def print_banner():
    print("\n" + "=" * 70)
    print("🔍 OSINT GRAPH INTELLIGENCE ENGINE - INTERACTIVE QUERY")
    print("=" * 70)
    print("\nAsk questions about your ingested documents.")
    print("Type 'exit' or 'quit' to end the session.")
    print("Type 'help' for example questions.\n")

def show_help():
    print("\n💡 Example questions:")
    print("  • Who is John Wick?")
    print("  • What is the relationship between John Wick and Charon?")
    print("  • Who executed Charon?")
    print("  • What happened during the siege of New York?")
    print("  • Who works at the Continental?")
    print("  • Tell me about Winston Scott")
    print()

def main():
    print_banner()
    
    while True:
        try:
            # Get user input
            question = input("\n❓ Your question: ").strip()
            
            # Handle commands
            if not question:
                continue
            
            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            if question.lower() in ['help', 'h', '?']:
                show_help()
                continue
            
            # Query the system
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
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Make sure documents are ingested and Ollama is running.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        
        except EOFError:
            print("\n\n👋 Goodbye!\n")
            break

if __name__ == "__main__":
    main()
