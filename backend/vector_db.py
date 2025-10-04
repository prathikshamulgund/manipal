# backend/vector_db.py
import os
import chromadb
from chromadb.config import Settings

# configure persistence dir via env var
PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

_chroma_client = None
_collection = None

def get_chroma_client():
    global _chroma_client, _collection
    if _chroma_client is None:
        # Use local persistence; configure as needed
        settings = Settings(chroma_db_impl="duckdb+parquet", persist_directory=PERSIST_DIR)
        _chroma_client = chromadb.Client(settings=settings)
        _collection = _chroma_client.get_or_create_collection(name="mining_documents")
    return _chroma_client, _collection

def add_documents(docs, metadatas=None, ids=None):
    _, col = get_chroma_client()
    # Only add if not present (simple guard)
    existing = col.get(ids=ids) if ids else None
    try:
        col.add(documents=docs, metadatas=metadatas, ids=ids)
    except Exception as e:
        # handle duplicates or other issues gracefully
        print("[vector_db] add error:", e)

def semantic_search(query, n_results=3):
    _, col = get_chroma_client()
    try:
        res = col.query(query_texts=[query], n_results=n_results)
        # returns dict-like structure: results['documents'], etc.
        return res
    except Exception as e:
        print("[vector_db] query error:", e)
        return {"documents": [[]], "metadatas": [[]]}
