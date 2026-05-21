# api/routes/documents.py
#
# This file handles everything related to document management:
# - Uploading PDFs
# - Listing uploaded files
# - (Later) Triggering RAG pipeline on a document
#
# WHY a separate file? Single Responsibility Principle — each file
# owns one domain of your app. documents.py owns document logic,
# health.py owns health checks. Easy to find, easy to maintain.

import os
import uuid
import aiofiles
from datetime import datetime, timezone
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from services.pdf_parser import parse_and_chunk_pdf
from services.pdf_parser import parse_and_chunk_pdf, parse_and_chunk_pdf_smart
from services.vector_store import (
    embed_and_store_chunks,
    search_similar_chunks,
    get_collection_info
)

from services.vector_store import (
    embed_and_store_chunks,
    search_similar_chunks,
    get_collection_info,
    list_embedded_documents        # ← ADD THIS
)
from services.rag_service import (
    ask_question_with_memory,
    ask_across_documents,          # ← ADD THIS
    clear_session,
    get_session_history
)
from pydantic import BaseModel
from typing import List, Optional

class MultiDocQuestionRequest(BaseModel):
    file_ids: List[str]          # List of doc IDs to search
    question: str                # The question
    session_id: Optional[str] = None
    n_results: int = 5           # Total chunks across all docs
# ── Router Setup ────────────────────────────────────────────────────────────
router = APIRouter()

# ── Constants ───────────────────────────────────────────────────────────────
# os.path.dirname(__file__) = the folder THIS file lives in (api/routes/)
# We go up two levels (../../) to reach backend/, then into uploads/
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
MAX_FILE_SIZE_MB = 10
ALLOWED_TYPES = ["application/pdf"]


# ── Helper Function ──────────────────────────────────────────────────────────
def ensure_upload_dir():
    """
    Creates the uploads/ directory if it doesn't exist.
    os.makedirs with exist_ok=True means: create it, but don't
    crash if it already exists. Safe to call every time.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/upload", summary="Upload a medical PDF document")
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts a PDF file upload, validates it, and saves it to disk.

    - **file**: A PDF file (max 10MB)

    Returns metadata about the saved file.
    """

    # ── 1. Validate file type ────────────────────────────────────────────
    # UploadFile gives us content_type — the MIME type the browser declared.
    # We check it's actually a PDF, not a disguised .exe or .jpg
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Only PDFs are allowed."
        )

    # ── 2. Read file into memory & check size ────────────────────────────
    # await = "pause here until the file is fully read, but don't block
    #          other requests while waiting"
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)  # bytes → MB

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({file_size_mb:.1f}MB). Maximum allowed is {MAX_FILE_SIZE_MB}MB."
        )

    # ── 3. Generate a unique filename ────────────────────────────────────
    # WHY? If two users upload "report.pdf", we can't save both as
    # "report.pdf" — one overwrites the other. UUID gives each file
    # a guaranteed unique name like: a3f8c1d2_report.pdf
    original_name = file.filename
    unique_prefix = str(uuid.uuid4())[:8]           # e.g. "a3f8c1d2"
    safe_filename = f"{unique_prefix}_{original_name}"  # e.g. "a3f8c1d2_report.pdf"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # ── 4. Save file to disk asynchronously ─────────────────────────────
    # aiofiles.open() is the async version of Python's built-in open()
    # "wb" = write binary (PDFs are binary, not plain text)
    ensure_upload_dir()
    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(contents)

    # ── 5. Return metadata ───────────────────────────────────────────────
    return JSONResponse(
        status_code=201,  # 201 = Created (more accurate than 200 for new resources)
        content={
            "message": "File uploaded successfully",
            "file_id": unique_prefix,
            "filename": safe_filename,
            "original_name": original_name,
            "size_mb": round(file_size_mb, 3),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
    )


@router.get("/documents", summary="List all uploaded documents")
def list_documents():
    """
    Returns a list of all uploaded PDF files.
    Useful for the frontend to show what's been uploaded.
    """
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


@router.get("/documents/{file_id}/parse", summary="Parse and chunk a PDF")
def parse_document(file_id: str):
    """
    Finds an uploaded PDF by its file_id, extracts all text,
    and splits it into chunks ready for embedding.

    - **file_id**: The 8-character ID returned when the file was uploaded
    """

    # ── 1. Find the file by its ID prefix ───────────────────────────────
    # We don't store the full filename — just the ID. So we search the
    # uploads folder for a file that STARTS WITH that ID.
    ensure_upload_dir()
    matched_file = None

    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(file_id):
            matched_file = filename
            break  # Found it — stop searching

    # ── 2. Handle file not found ─────────────────────────────────────────
    if not matched_file:
        raise HTTPException(
            status_code=404,
            detail=f"No document found with file_id '{file_id}'. Upload it first."
        )

    # ── 3. Parse and chunk ───────────────────────────────────────────────
    file_path = os.path.join(UPLOAD_DIR, matched_file)
    result = parse_and_chunk_pdf(file_path)

    # ── 4. Return result ─────────────────────────────────────────────────
    return {
        "file_id": file_id,
        "filename": matched_file,
        "total_pages": result["total_pages"],
        "total_characters": result["total_characters"],
        "total_chunks": result["total_chunks"],
        # Return first 5 chunks as preview — don't overwhelm the response
        "chunks_preview": result["chunks"][:5],
        "all_chunks": result["chunks"]
    }

@router.post("/documents/{file_id}/embed", summary="Embed a PDF into ChromaDB")
def embed_document(file_id: str):
    """
    Parses the PDF, generates embeddings for each chunk,
    and stores everything in ChromaDB.

    Run this AFTER uploading a PDF.
    Run this BEFORE asking questions about it.
    """

    # Step 1 — Find the file
    ensure_upload_dir()
    matched_file = None
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(file_id):
            matched_file = filename
            break

    if not matched_file:
        raise HTTPException(
            status_code=404,
            detail=f"No document found with file_id '{file_id}'"
        )

    # Step 2 — Parse into chunks
    file_path = os.path.join(UPLOAD_DIR, matched_file)
    parse_result = parse_and_chunk_pdf(file_path)

    # Step 3 — Embed and store in ChromaDB
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


@router.get("/documents/{file_id}/search", summary="Search PDF by meaning")
def search_document(file_id: str, query: str, n_results: int = 3):
    """
    Searches the embedded PDF for chunks relevant to your query.
    Uses semantic search — finds meaning, not just keywords.

    - **file_id**: The document to search
    - **query**: Your question in plain English
    - **n_results**: How many chunks to return (default 3)
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


@router.get("/documents/{file_id}/info", summary="Check embedding status")
def document_info(file_id: str):
    """
    Check if a document has been embedded and how many
    chunks are stored in ChromaDB.
    """
    return get_collection_info(file_id)

@router.get("/documents/embedded", summary="List all embedded documents")
def get_embedded_documents():
    """
    Returns all documents currently stored in ChromaDB.
    Use this to see which file_ids you can search across.
    """
    return list_embedded_documents()


@router.post("/chat/multi", summary="Chat across multiple PDFs")
def multi_document_chat(request: MultiDocQuestionRequest):
    """
    Ask a question that searches across MULTIPLE uploaded PDFs.
    Returns the most relevant information from all documents combined.

    - **file_ids**: List of document IDs to search across
    - **question**: Your question
    - **session_id**: Conversation ID (auto-generated if not provided)
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

@router.get("/documents/{file_id}/compare-chunking",
            summary="Compare basic vs smart chunking")
def compare_chunking(file_id: str):
    """
    Runs both chunking strategies on the same PDF and
    returns a comparison. Shows why smart chunking is better.
    """
    ensure_upload_dir()
    matched_file = None
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(file_id):
            matched_file = filename
            break

    if not matched_file:
        raise HTTPException(
            status_code=404,
            detail=f"No document found with file_id '{file_id}'"
        )

    file_path = os.path.join(UPLOAD_DIR, matched_file)

    # Run both strategies
    basic_result = parse_and_chunk_pdf(file_path)
    smart_result = parse_and_chunk_pdf_smart(file_path)

    return {
        "file_id": file_id,
        "comparison": {
            "basic_chunking": {
                "total_chunks": basic_result["total_chunks"],
                "sample_chunk": basic_result["chunks"][0]["text"][:200] if basic_result["chunks"] else None,
            },
            "smart_chunking": {
                "total_chunks": smart_result["total_chunks"],
                "stats": smart_result["chunking_stats"],
                "sample_chunk": smart_result["chunks"][0]["text"][:200] if smart_result["chunks"] else None,
                "sample_section_type": smart_result["chunks"][0].get("section_type", "N/A") if smart_result["chunks"] else None,
            }
        }
    }