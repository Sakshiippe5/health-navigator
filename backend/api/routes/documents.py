# api/routes/documents.py

import os
import uuid
import aiofiles
from datetime import datetime, timezone
from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy.orm import Session

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
from services.document_service import (
    create_document,
    get_user_documents,
    get_document_by_file_id,
    mark_document_embedded
)
from database.connection import get_db
from database.models import User
from core.dependencies import get_current_user

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
MAX_FILE_SIZE_MB = 10
ALLOWED_TYPES = ["application/pdf"]


class MultiDocQuestionRequest(BaseModel):
    file_ids: List[str]
    question: str
    session_id: Optional[str] = None
    n_results: int = 5


def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def find_file_by_id(file_id: str) -> str:
    ensure_upload_dir()
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(file_id):
            return filename
    raise HTTPException(
        status_code=404,
        detail=f"No document found with file_id '{file_id}'"
    )


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("/upload", status_code=201, summary="Upload a medical PDF")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files allowed.")

    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max {MAX_FILE_SIZE_MB}MB."
        )

    original_name = file.filename
    unique_prefix = str(uuid.uuid4())[:8]
    safe_filename = f"{unique_prefix}_{original_name}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    ensure_upload_dir()
    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(contents)

    create_document(
        db=db,
        user_id=current_user.id,
        file_id=unique_prefix,
        filename=safe_filename,
        original_name=original_name,
        size_mb=round(file_size_mb, 3)
    )

    return {
        "message": "File uploaded successfully",
        "file_id": unique_prefix,
        "filename": safe_filename,
        "original_name": original_name,
        "size_mb": round(file_size_mb, 3),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }


# ── List Documents ────────────────────────────────────────────────────────────

@router.get("/documents", summary="List current user's documents")
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_docs = get_user_documents(db, current_user.id)
    return {
        "total": len(user_docs),
        "documents": [
            {
                "filename": doc.filename,
                "original_name": doc.original_name,
                "file_id": doc.file_id,
                "size_mb": doc.size_mb,
                "is_embedded": doc.is_embedded,
                "total_chunks": doc.total_chunks,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None
            }
            for doc in user_docs
        ]
    }


# ── List Embedded Documents ───────────────────────────────────────────────────

@router.get("/documents/embedded", summary="List embedded documents")
def get_embedded_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_docs = get_user_documents(db, current_user.id)
    embedded = [doc for doc in user_docs if doc.is_embedded]
    return {
        "total_documents": len(embedded),
        "documents": [
            {
                "file_id": doc.file_id,
                "collection_name": f"doc_{doc.file_id}",
                "total_chunks": doc.total_chunks,
                "original_name": doc.original_name
            }
            for doc in embedded
        ]
    }


# ── Parse Document ────────────────────────────────────────────────────────────

@router.get("/documents/{file_id}/parse", summary="Parse and chunk a PDF")
def parse_document(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = get_document_by_file_id(db, file_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

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

@router.post("/documents/{file_id}/embed", summary="Embed a PDF into ChromaDB")
def embed_document(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = get_document_by_file_id(db, file_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    matched_file = find_file_by_id(file_id)
    file_path = os.path.join(UPLOAD_DIR, matched_file)

    parse_result = parse_and_chunk_pdf(file_path)
    embed_result = embed_and_store_chunks(
        file_id=file_id,
        chunks=parse_result["chunks"]
    )

    mark_document_embedded(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        total_chunks=parse_result["total_chunks"]
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

@router.get("/documents/{file_id}/info", summary="Check embedding status")
def document_info(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = get_document_by_file_id(db, file_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return get_collection_info(file_id)


# ── Semantic Search ───────────────────────────────────────────────────────────

@router.get("/documents/{file_id}/search", summary="Search PDF by meaning")
def search_document(
    file_id: str,
    query: str,
    n_results: int = 3,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = get_document_by_file_id(db, file_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    result = search_similar_chunks(
        file_id=file_id,
        query=query,
        n_results=n_results
    )

    if result["status"] == "not_embedded":
        raise HTTPException(
            status_code=400,
            detail="Document not embedded yet."
        )
    return result


# ── Compare Chunking ──────────────────────────────────────────────────────────

@router.get("/documents/{file_id}/compare-chunking",
            summary="Compare chunking strategies")
def compare_chunking(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = get_document_by_file_id(db, file_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

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
            }
        }
    }


# ── Multi-Document Chat ───────────────────────────────────────────────────────

@router.post("/chat/multi", summary="Chat across multiple PDFs")
def multi_document_chat(
    request: MultiDocQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    for file_id in request.file_ids:
        doc = get_document_by_file_id(db, file_id, current_user.id)
        if not doc:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{file_id}' not found or access denied."
            )

    session_id = request.session_id or str(uuid.uuid4())[:8]
    result = ask_across_documents(
        file_ids=request.file_ids,
        question=request.question,
        session_id=session_id,
        n_results=request.n_results
    )

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result