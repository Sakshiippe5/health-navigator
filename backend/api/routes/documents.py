# api/routes/documents.py
#
# UPDATED: Added Pydantic response_model to every endpoint.
# All schemas imported from api/schemas.py
#
# Endpoints:
#   POST   /upload                          → upload PDF
#   GET    /documents                       → list all PDFs
#   GET    /documents/embedded              → list embedded docs
#   GET    /documents/{file_id}/parse       → parse PDF into chunks
#   POST   /documents/{file_id}/embed       → embed into ChromaDB
#   GET    /documents/{file_id}/info        → check embedding status
#   GET    /documents/{file_id}/search      → semantic search
#   GET    /documents/{file_id}/compare-chunking → compare strategies
#   POST   /chat/multi                      → multi-doc chat

import os
import uuid
import aiofiles
from datetime import datetime, timezone
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel
from typing import List

from api.schemas import (
    UploadResponse,
    DocumentListResponse,
    EmbedResponse,
    CollectionInfo,
    EmbeddedDocumentsResponse,
    MultiDocQuestionRequest,
    MultiDocChatResponse,
    ParseResponse
)
from services.vector_store import (
    embed_and_store_chunks,
    search_similar_chunks,
    get_collection_info,
    list_embedded_documents
)
from services.pdf_parser import (
    parse_and_chunk_pdf,
    parse_and_chunk_pdf_smart
)
from services.rag_service import (
    ask_across_documents,
    clear_session,
    get_session_history
)

# ── Router Setup ──────────────────────────────────────────────────────────────
router = APIRouter()

# ── Constants ─────────────────────────────────────────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
MAX_FILE_SIZE_MB = 10
ALLOWED_TYPES = ["application/pdf"]


# ── Helper ────────────────────────────────────────────────────────────────────
def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def find_file_by_id(file_id: str) -> str:
    """
    Finds a file in uploads/ by its ID prefix.
    Raises 404 if not found.
    Extracted as helper to avoid repeating this logic in every endpoint.
    """
    ensure_upload_dir()
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(file_id):
            return filename
    raise HTTPException(
        status_code=404,
        detail=f"No document found with file_id '{file_id}'"
    )


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=201,
    summary="Upload a medical PDF document"
)
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts a PDF file upload, validates it, and saves it to disk.
    - **file**: A PDF file (max 10MB)
    """

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Only PDFs allowed."
        )

    # Read and check size
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({file_size_mb:.1f}MB). Max is {MAX_FILE_SIZE_MB}MB."
        )

    # Generate unique filename
    original_name = file.filename
    unique_prefix = str(uuid.uuid4())[:8]
    safe_filename = f"{unique_prefix}_{original_name}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # Save to disk
    ensure_upload_dir()
    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(contents)

    return {
        "message": "File uploaded successfully",
        "file_id": unique_prefix,
        "filename": safe_filename,
        "original_name": original_name,
        "size_mb": round(file_size_mb, 3),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }


# ── List Documents ────────────────────────────────────────────────────────────

@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List all uploaded documents"
)
def list_documents():
    """Returns a list of all uploaded PDF files."""
    ensure_upload_dir()

    files = []
    for filename in os.listdir(UPLOAD_DIR):
        if filename.endswith(".pdf"):
            file_path = os.path.join(UPLOAD_DIR, filename)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            files.append({
                "filename": filename,
                "size_mb": round(size_mb, 3),
            })

    return {
        "total": len(files),
        "documents": files
    }


# ── List Embedded Documents ───────────────────────────────────────────────────

@router.get(
    "/documents/embedded",
    response_model=EmbeddedDocumentsResponse,
    summary="List all embedded documents"
)
def get_embedded_documents():
    """
    Returns all documents currently stored in ChromaDB.
    Use this to see which file_ids you can search across.
    """
    return list_embedded_documents()


# ── Parse Document ────────────────────────────────────────────────────────────

@router.get(
    "/documents/{file_id}/parse",
    summary="Parse and chunk a PDF"
)
def parse_document(file_id: str):
    """
    Finds an uploaded PDF by its file_id, extracts all text,
    and splits it into chunks ready for embedding.
    """
    matched_file = find_file_by_id(file_id)
    file_path = os.path.join(UPLOAD_DIR, matched_file)
    result = parse_and_chunk_pdf(file_path)

    return {
        "file_id": file_id,
        "filename": matched_file,
        "total_pages": result["total_pages"],
        "total_characters": result["total_characters"],
        "total_chunks": result["total_chunks"],
        "chunks_preview": result["chunks"][:5],
        "all_chunks": result["chunks"]
    }


# ── Embed Document ────────────────────────────────────────────────────────────

@router.post(
    "/documents/{file_id}/embed",
    response_model=EmbedResponse,
    summary="Embed a PDF into ChromaDB"
)
def embed_document(file_id: str):
    """
    Parses the PDF, generates embeddings for each chunk,
    and stores everything in ChromaDB.

    Run AFTER uploading. Run BEFORE asking questions.
    """
    matched_file = find_file_by_id(file_id)
    file_path = os.path.join(UPLOAD_DIR, matched_file)

    # Parse into chunks
    parse_result = parse_and_chunk_pdf(file_path)

    # Embed and store
    embed_result = embed_and_store_chunks(
        file_id=file_id,
        chunks=parse_result["chunks"]
    )

    return {
        "file_id": file_id,
        "filename": matched_file,
        "parsing": {
            "total_pages": parse_result["total_pages"],
            "total_chunks": parse_result["total_chunks"],
        },
        "embedding": embed_result
    }


# ── Document Info ─────────────────────────────────────────────────────────────

@router.get(
    "/documents/{file_id}/info",
    response_model=CollectionInfo,
    summary="Check embedding status"
)
def document_info(file_id: str):
    """
    Check if a document has been embedded and how many
    chunks are stored in ChromaDB.
    """
    return get_collection_info(file_id)


# ── Semantic Search ───────────────────────────────────────────────────────────

@router.get(
    "/documents/{file_id}/search",
    summary="Search PDF by meaning"
)
def search_document(file_id: str, query: str, n_results: int = 3):
    """
    Searches the embedded PDF for chunks relevant to your query.
    Uses semantic search — finds meaning, not just keywords.
    """
    result = search_similar_chunks(
        file_id=file_id,
        query=query,
        n_results=n_results
    )

    if result["status"] == "not_embedded":
        raise HTTPException(
            status_code=400,
            detail="Document not embedded yet. POST to /embed first."
        )

    return result


# ── Compare Chunking ──────────────────────────────────────────────────────────

@router.get(
    "/documents/{file_id}/compare-chunking",
    summary="Compare basic vs smart chunking"
)
def compare_chunking(file_id: str):
    """
    Runs both chunking strategies on the same PDF and
    returns a side-by-side comparison.
    """
    matched_file = find_file_by_id(file_id)
    file_path = os.path.join(UPLOAD_DIR, matched_file)

    basic_result = parse_and_chunk_pdf(file_path)
    smart_result = parse_and_chunk_pdf_smart(file_path)

    return {
        "file_id": file_id,
        "comparison": {
            "basic_chunking": {
                "total_chunks": basic_result["total_chunks"],
                "sample_chunk": basic_result["chunks"][0]["text"][:200]
                    if basic_result["chunks"] else None,
            },
            "smart_chunking": {
                "total_chunks": smart_result["total_chunks"],
                "stats": smart_result["chunking_stats"],
                "sample_chunk": smart_result["chunks"][0]["text"][:200]
                    if smart_result["chunks"] else None,
                "sample_section_type": smart_result["chunks"][0].get(
                    "section_type", "N/A"
                ) if smart_result["chunks"] else None,
            }
        }
    }


# ── Multi-Document Chat ───────────────────────────────────────────────────────

@router.post(
    "/chat/multi",
    response_model=MultiDocChatResponse,
    summary="Chat across multiple PDFs"
)
def multi_document_chat(request: MultiDocQuestionRequest):
    """
    Ask a question that searches across MULTIPLE uploaded PDFs.
    Returns the most relevant information from all documents combined.
    """
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    if not request.file_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one file_id is required."
        )

    session_id = request.session_id or str(uuid.uuid4())[:8]

    result = ask_across_documents(
        file_ids=request.file_ids,
        question=request.question,
        session_id=session_id,
        n_results=request.n_results
    )

    if result["status"] == "error":
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result