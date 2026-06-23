from .reader import AutoFileReader
from .store import save_document
from .chunker import chunk_text
from .embedder import embed_document

def ingest(filepath):
    """
    Ingest a single document: read, chunk, embed, and store.
    
    Args:
        filepath: Path to the document (PDF or TXT)
    
    Returns:
        document_id: The ID of the ingested document in SQLite
    """
    filename, content = AutoFileReader(filepath)
    doc_id = save_document(filename, content)
    chunked_text = chunk_text(content)
    embed_document(document_id=doc_id, chunks=chunked_text)
    return doc_id


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = "Sample input/johnwick_charon.txt"
    
    print(f"Ingesting: {filepath}")
    doc_id = ingest(filepath)
    print(f"✅ Document ingested with ID: {doc_id}")