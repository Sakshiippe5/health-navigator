# api/routes/chat.py
from fastapi import APIRouter, HTTPException
from api.schemas import (
    QuestionRequest,
    MultiDocQuestionRequest,
    ChatResponse,
    MultiDocChatResponse,
    SessionHistoryResponse,
    ClearSessionResponse
)
from services.rag_service import (
    ask_question_with_memory,
    ask_across_documents,
    clear_session,
    get_session_history
)
import uuid

router = APIRouter()


@router.post(
    "/chat/{file_id}",
    response_model=ChatResponse,          # ← enforces response shape
    summary="Chat with a PDF (with memory)"
)
def chat_with_document(file_id: str, request: QuestionRequest):
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


@router.get(
    "/chat/{session_id}/history",
    response_model=SessionHistoryResponse,
    summary="View conversation history"
)
def get_history(session_id: str):
    return get_session_history(session_id)


@router.delete(
    "/chat/{session_id}",
    response_model=ClearSessionResponse,
    summary="Clear conversation"
)
def clear_conversation(session_id: str):
    return clear_session(session_id)