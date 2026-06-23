import ollama
import chromadb
from chromadb.utils import embedding_functions

# --- ChromaDB setup (mirrors embedder.py) ---
_client = chromadb.PersistentClient("data/chromadb")

_ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url="http://localhost:11434/api/embeddings",
    model_name="nomic-embed-text",
)

_collection = _client.get_or_create_collection(
    name="documents", embedding_function=_ollama_ef
)


def retrieve_context(query,n_results= 5,document_id = None):

    where_filter = {"document_id": str(document_id)} if document_id is not None else None

    results = _collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter,
    )

    # results["documents"] is a list-of-lists (one list per query_text)
    chunks = results["documents"][0] if results["documents"] else []
    return chunks


def answer_with_context(
    query: str,
    n_results: int = 5,
    document_id: int | None = None,
    model: str = "llama3.1",
) -> str:
    chunks = retrieve_context(query, n_results=n_results, document_id=document_id)

    if not chunks:
        return "No relevant context found in the knowledge base to answer that question."

    # Build the context block
    context_block = "\n\n".join(
        f"[Chunk {i + 1}]:\n{chunk}" for i, chunk in enumerate(chunks)
    )

    prompt = f"""You are an intelligence analyst assistant. Answer the question using ONLY the context provided below.
If the answer cannot be found in the context, say "I don't have enough information to answer that."

--- CONTEXT ---
{context_block}
--- END CONTEXT ---

Question: {query}

Answer:"""

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    return response["message"]["content"]


if __name__ == "__main__":
    # Quick smoke test — make sure Ollama is running and documents are ingested first
    question = "What is the relationship between John Wick and Charon?"
    print(f"Question: {question}\n")

    context = retrieve_context(question)
    print("Retrieved chunks:")
    for i, chunk in enumerate(context, 1):
        print(f"  [{i}] {chunk[:120]}...")

    print("\n--- LLM Answer ---")
    answer = answer_with_context(question)
    print(answer)
