# api/routes/chat.py
#
# RESPONSIBILITY: Handle Q&A requests from the user.
# This is the endpoint your frontend will call when
# a user types a question about their medical PDF.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.rag_service import ask_question

router = APIRouter()


# ── Request Schema ────────────────────────────────────────────────────────────
# Pydantic BaseModel defines the shape of the request body.
# FastAPI automatically validates incoming JSON against this model.
# If the request is missing 'question', FastAPI returns 422 automatically.
class QuestionRequest(BaseModel):
    question: str           # Required — the user's question
    n_chunks: int = 3       # Optional — how many chunks to use (default 3)


# ── Endpoint ──────────────────────────────────────────────────────────────────
@router.post("/chat/{file_id}", summary="Ask a question about a PDF")
def chat_with_document(file_id: str, request: QuestionRequest):
    """
    Ask any question about an uploaded and embedded PDF.
    The AI will answer based only on the document content.

    - **file_id**: The document to query
    - **question**: Your question in plain English
    - **n_chunks**: Number of context chunks to use (default 3)
    """

    # Validate question isn't empty
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # Run the full RAG pipeline
    result = ask_question(
        file_id=file_id,
        question=request.question,
        n_chunks=request.n_chunks
    )

    # Handle errors from the RAG service
    if result["status"] == "error":
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result