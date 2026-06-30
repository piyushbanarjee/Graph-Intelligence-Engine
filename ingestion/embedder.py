import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient("data/chromadb")

ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    url='http://localhost:11434/api/embeddings', 
    model_name= 'nomic-embed-text')

collection = client.get_or_create_collection(name = "documents", embedding_function=ollama_ef)

def embed_document(document_id, chunks,target_collection= collection):
    batch_documents= []
    batch_ids= []
    batch_metadata= []

    for idx, chunk in enumerate(chunks):
        clean_chunk = chunk.replace('\n', " ").strip()
        chunk_id = f"{document_id}_{idx}"
        chunk_metadata = {"document_id": document_id, "chunk_index": idx}

        batch_documents.append(clean_chunk)
        batch_ids.append(chunk_id)
        batch_metadata.append(chunk_metadata)
    
    if batch_ids:
        target_collection.upsert(ids=batch_ids, documents=batch_documents, metadatas=batch_metadata)
        print(f"Successfully batch-indexed {len(batch_ids)} chunks for document: {document_id}")


if __name__ == '__main__':
    sample_document_id = "test"
    sample_chunks = [
    "Operation Black Ice update: The server room decryption codes are cycled every 24 hours at midnight PST.",
    "Physical breach protocols require biometric override keys from two Tier-1 executives simultaneously.",
    "A secondary secure data asset is hidden inside an offline cooling system node in the sub-basement repository.",
    "Standard cleaning staff have zero security clearance for Sector 7 areas; any unescorted personnel must be detained immediately."
    ]
    
    # Corrected argument passing order
    embed_document(document_id=sample_document_id, chunks=sample_chunks)
    result = collection.get(
        where = {"document_id": "test"}
        )
    print(result["documents"])
    
    collection.delete(where={"document_id": "test"})