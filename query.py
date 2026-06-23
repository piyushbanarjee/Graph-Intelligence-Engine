#!/usr/bin/env python3
"""
Interactive query interface for the OSINT Graph Intelligence Engine

Usage:
    ./venv/bin/python query.py "Your question here"
    
Examples:
    ./venv/bin/python query.py "Who is John Wick?"
    ./venv/bin/python query.py "What is the relationship between Wick and Charon?"
"""
import sys
from retrieval.retriever import answer_with_context

def main():
    if len(sys.argv) < 2:
        print("Usage: python query.py \"Your question here\"")
        print("\nExample questions:")
        print("  - Who is John Wick?")
        print("  - What is the relationship between Wick and Charon?")
        print("  - Who executed Charon?")
        print("  - What happened at the Continental?")
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    
    print("=" * 70)
    print(f"QUESTION: {question}")
    print("=" * 70)
    print("\n🔍 Searching knowledge base...\n")
    
    try:
        answer = answer_with_context(
            question, 
            n_results=5,
            model="llama3.1"
        )
        
        print("📝 ANSWER:")
        print("-" * 70)
        print(answer)
        print("-" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
