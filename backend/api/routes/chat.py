# api/routes/chat.py
#
# UPDATED: Session-based chat with memory.
# Three endpoints:
#   POST   /chat/{file_id}          → ask a question
#   GET    /chat/{session_id}/history → view history
#   DELETE /chat/{session_id}       → clear history

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.rag_service import (
    ask_question_with_memory,
    clear_session,
    get_session_history
)
import uuid

router = APIRouter()


# ── Request Schema ────────────────────────────────────────────────────────────
class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = None  # auto-generated if not provided
    n_chunks: int = 3


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/chat/{file_id}", summary="Chat with a PDF (with memory)")
def chat_with_document(file_id: str, request: QuestionRequest):
    """
    Ask a question about an uploaded PDF.
    Remembers previous questions in the same session.

    First message → don't send session_id → one gets created for you
    Follow-up     → send the session_id from the previous response
    """

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # Auto-generate session_id if this is a new conversation
    session_id = request.session_id or str(uuid.uuid4())[:8]

    result = ask_question_with_memory(
        file_id=file_id,
        question=request.question,
        session_id=session_id,
        n_chunks=request.n_chunks
    )

    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])

    return result


@router.get("/chat/{session_id}/history", summary="View conversation history")
def get_history(session_id: str):
    """
    Returns all previous messages in a conversation.
    Frontend uses this to display the chat timeline.
    """
    return get_session_history(session_id)


@router.delete("/chat/{session_id}", summary="Clear conversation")
def clear_conversation(session_id: str):
    """
    Deletes all history for a session.
    Called when user clicks 'New Chat'.
    """
    return clear_session(session_id)