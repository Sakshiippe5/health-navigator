# services/vector_store.py
#
# RESPONSIBILITY: Everything related to embeddings and vector storage.
# This service:
#   1. Converts text chunks → embeddings (numbers)
#   2. Stores them in ChromaDB
#   3. Searches ChromaDB for relevant chunks given a query
#
# WHY a separate service?
# Tomorrow when we build the Q&A endpoint, it just calls
# search_similar_chunks() — it doesn't need to know HOW
# embeddings work. Clean separation of concerns.

import chromadb
from chromadb.utils import embedding_functions
import os
from typing import List, Dict, Any

# ── Constants ────────────────────────────────────────────────────────────────
# Where ChromaDB stores its data on disk
# We go up one level from services/ to reach backend/
CHROMA_DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "chroma_db"
)

# The free, local embedding model we're using
# This runs ON YOUR MACHINE — no API key needed
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# How many similar chunks to return when searching
DEFAULT_N_RESULTS = 3


# ── Initialize ChromaDB Client ───────────────────────────────────────────────
# PersistentClient = saves to disk (survives server restarts)
# If we used Client() instead, data would vanish on restart
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Initialize the embedding function using our local model
# SentenceTransformerEmbeddingFunction downloads the model
# on first run, then caches it locally
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)


# ── Core Functions ────────────────────────────────────────────────────────────

def get_or_create_collection(file_id: str) -> chromadb.Collection:
    """
    Gets an existing ChromaDB collection for a file, or creates one.

    WHY one collection per file?
    Each PDF gets its own "namespace" in ChromaDB.
    When searching, we only search THAT file's chunks —
    not chunks from every PDF ever uploaded.
    This keeps results accurate and relevant.

    Args:
        file_id: The 8-character unique ID of the uploaded PDF

    Returns:
        A ChromaDB Collection object
    """
    # Collection names must be alphanumeric + underscores
    collection_name = f"doc_{file_id}"

    # get_or_create_collection is idempotent —
    # safe to call multiple times, won't duplicate
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn,
        metadata={"file_id": file_id}
    )

    return collection


def embed_and_store_chunks(file_id: str, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Takes parsed chunks and stores them in ChromaDB with embeddings.

    ChromaDB automatically generates embeddings using our embedding_fn.
    We just give it text — it handles the conversion to vectors.

    Args:
        file_id: The PDF's unique ID
        chunks: List of chunk dicts from pdf_parser.py

    Returns:
        Summary of what was stored
    """

    collection = get_or_create_collection(file_id)

    # Check if already embedded — avoid duplicating data
    # if someone calls this endpoint twice for the same file
    existing = collection.count()
    if existing > 0:
        return {
            "status": "already_embedded",
            "message": f"This document already has {existing} chunks embedded.",
            "total_chunks": existing
        }

    # Prepare data in the format ChromaDB expects:
    # - documents: list of text strings (ChromaDB embeds these)
    # - ids: unique string ID per chunk
    # - metadatas: extra info stored alongside each chunk
    documents = []
    ids = []
    metadatas = []

    for chunk in chunks:
        documents.append(chunk["text"])

        # ID must be unique per chunk — combine file_id + chunk index
        ids.append(f"{file_id}_chunk_{chunk['chunk_index']}")

        # Metadata lets us return context with search results
        metadatas.append({
            "chunk_index": chunk["chunk_index"],
            "char_count": chunk["char_count"],
            "word_count": chunk["word_count"],
            "file_id": file_id,
        })

    # THIS is where the magic happens:
    # ChromaDB calls our embedding_fn on each document,
    # converts text → vectors, stores everything
    collection.add(
        documents=documents,
        ids=ids,
        metadatas=metadatas
    )

    return {
        "status": "success",
        "total_chunks_embedded": len(chunks),
        "collection_name": f"doc_{file_id}",
        "embedding_model": EMBEDDING_MODEL,
    }


def search_similar_chunks(
    file_id: str,
    query: str,
    n_results: int = DEFAULT_N_RESULTS
) -> Dict[str, Any]:
    """
    Searches ChromaDB for chunks most similar to the query.

    This is the core of RAG — finding relevant context.
    ChromaDB converts the query to an embedding, then finds
    the chunks with the most similar embeddings.

    Args:
        file_id: Which document to search in
        query: The user's question in plain English
        n_results: How many chunks to return

    Returns:
        List of relevant chunks with similarity scores
    """

    collection = get_or_create_collection(file_id)

    # Check collection has data
    if collection.count() == 0:
        return {
            "status": "not_embedded",
            "message": "This document hasn't been embedded yet. Call /embed first.",
            "results": []
        }

    # query_texts: ChromaDB embeds your question and finds
    # the nearest chunk vectors in the database
    results = collection.query(
        query_texts=[query],      # Your question
        n_results=min(            # Don't request more than we have
            n_results,
            collection.count()
        ),
        include=["documents", "metadatas", "distances"]
    )

    # ChromaDB returns nested lists (supports batch queries)
    # We sent one query so we take index [0]
    raw_docs = results["documents"][0]
    raw_meta = results["metadatas"][0]
    raw_dist = results["distances"][0]

    # Format results cleanly
    # Distance = how different vectors are (lower = more similar)
    # We convert to similarity score: 1 - distance
    formatted = []
    for doc, meta, dist in zip(raw_docs, raw_meta, raw_dist):
        formatted.append({
            "text": doc,
            "chunk_index": meta["chunk_index"],
            "similarity_score": round(1 - dist, 4),  # Higher = more relevant
            "word_count": meta["word_count"],
        })

    return {
        "status": "success",
        "query": query,
        "total_results": len(formatted),
        "results": formatted
    }


def get_collection_info(file_id: str) -> Dict[str, Any]:
    """
    Returns info about a document's vector collection.
    Useful for debugging — check if a doc is embedded.
    """
    collection = get_or_create_collection(file_id)
    count = collection.count()

    return {
        "file_id": file_id,
        "collection_name": f"doc_{file_id}",
        "total_chunks": count,
        "is_embedded": count > 0,
        "embedding_model": EMBEDDING_MODEL,
    }