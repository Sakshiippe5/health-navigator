# api/schemas.py
#
# RESPONSIBILITY: All Pydantic models for requests AND responses.
# Centralizing them here means:
#   - One place to find all data shapes
#   - Easy to reuse across routes
#   - Single source of truth for API contract
#
# NAMING CONVENTION:
#   *Request  = incoming data (what client sends)
#   *Response = outgoing data (what server returns)

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ── Document Schemas ──────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Returned after successfully uploading a PDF."""
    message: str
    file_id: str
    filename: str
    original_name: str
    size_mb: float
    uploaded_at: str

    class Config:
        # Allows FastAPI to convert ORM objects too (useful in Phase 4)
        from_attributes = True


class DocumentInfo(BaseModel):
    """Basic info about one document."""
    filename: str
    size_mb: float


class DocumentListResponse(BaseModel):
    """Returned when listing all uploaded documents."""
    total: int
    documents: List[DocumentInfo]


class ParseResponse(BaseModel):
    """Returned after parsing a PDF into chunks."""
    file_id: str
    filename: str
    total_pages: int
    total_characters: int
    total_chunks: int
    chunks_preview: List[Dict[str, Any]]  # first 5 chunks
    all_chunks: List[Dict[str, Any]]


class EmbedResponse(BaseModel):
    """Returned after embedding a document into ChromaDB."""
    file_id: str
    filename: str
    parsing: Dict[str, Any]
    embedding: Dict[str, Any]


class CollectionInfo(BaseModel):
    """Info about a document's ChromaDB collection."""
    file_id: str
    collection_name: str
    total_chunks: int
    is_embedded: bool
    embedding_model: str


class EmbeddedDocumentItem(BaseModel):
    """One item in the embedded documents list."""
    file_id: str
    collection_name: str
    total_chunks: int


class EmbeddedDocumentsResponse(BaseModel):
    """List of all embedded documents."""
    total_documents: int
    documents: List[EmbeddedDocumentItem]


# ── Search Schemas ────────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    """One chunk result from semantic search."""
    text: str
    chunk_index: int
    similarity_score: float
    word_count: int


class SearchResponse(BaseModel):
    """Returned after searching a document."""
    status: str
    query: str
    total_results: int
    results: List[SearchResult]


# ── Chat Schemas ──────────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    """Request body for single-document chat."""
    question: str = Field(
        ...,                              # required
        min_length=1,                     # can't be empty
        max_length=1000,                  # reasonable limit
        description="Your question about the document"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Conversation ID. Auto-generated if not provided."
    )
    n_chunks: int = Field(
        default=3,
        ge=1,          # greater than or equal to 1
        le=10,         # less than or equal to 10
        description="Number of context chunks to retrieve"
    )


class MultiDocQuestionRequest(BaseModel):
    """Request body for multi-document chat."""
    file_ids: List[str] = Field(
        ...,
        min_length=1,    # at least one file
        description="List of document IDs to search across"
    )
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000
    )
    session_id: Optional[str] = None
    n_results: int = Field(default=5, ge=1, le=20)


class SourceChunk(BaseModel):
    """One source chunk included in a chat response."""
    chunk_index: int
    similarity_score: float
    excerpt: str                          # first 150 chars of chunk


class ChatResponse(BaseModel):
    """Returned after asking a question about a document."""
    status: str
    session_id: str
    question: str
    answer: str
    history_length: int
    sources: List[SourceChunk]
    model: str


class MultiDocSourceChunk(BaseModel):
    """Source chunk with document attribution for multi-doc chat."""
    source_file_id: str                   # which document this came from
    chunk_index: int
    similarity_score: float
    excerpt: str


class MultiDocChatResponse(BaseModel):
    """Returned after multi-document chat."""
    status: str
    session_id: str
    question: str
    answer: str
    history_length: int
    documents_searched: List[str]
    sources: List[MultiDocSourceChunk]
    model: str


# ── History Schemas ───────────────────────────────────────────────────────────

class HistoryMessage(BaseModel):
    """One message in conversation history."""
    role: str                             # "user" or "assistant"
    content: str


class SessionHistoryResponse(BaseModel):
    """Full conversation history for a session."""
    session_id: str
    history: List[HistoryMessage]
    total_messages: int
    total_exchanges: int


class ClearSessionResponse(BaseModel):
    """Returned after clearing a session."""
    status: str
    session_id: str


# ── Health Schema ─────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Server health check response."""
    status: str
    timestamp: str
    version: str
    service: str


# ── Error Schema ──────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error response shape."""
    detail: str