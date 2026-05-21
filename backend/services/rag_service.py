# services/rag_service.py
# Using Groq (free, fast, generous limits)

from groq import Groq
from core.config import GROQ_API_KEY
from services.vector_store import search_similar_chunks
from typing import Dict, Any, List

# ── Initialize Groq ───────────────────────────────────────────────────────────
client = Groq(api_key=GROQ_API_KEY)
GROQ_MODEL = "llama-3.3-70b-versatile"

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a helpful medical document assistant.
Answer questions based ONLY on the provided document context.

Rules:
- Answer only from the context provided
- If answer not in context, say "I couldn't find that in the document"
- Be precise and concise
- Never make up information
"""

# ── In-Memory Session Store ───────────────────────────────────────────────────
chat_sessions: Dict[str, List[Dict[str, str]]] = {}


def get_or_create_session(session_id: str) -> List[Dict[str, str]]:
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    return chat_sessions[session_id]


def build_prompt(
    context_chunks: List[Dict],
    question: str,
    history: List[Dict]
) -> str:
    # Format context
    context_text = ""
    for i, chunk in enumerate(context_chunks, start=1):
        context_text += f"\n[Context {i}]:\n{chunk['text']}\n"

    # Format history
    history_text = ""
    if history:
        history_text = "\n---CONVERSATION HISTORY---\n"
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
        history_text += "---END OF HISTORY---\n"

    return f"""---DOCUMENT CONTEXT---
{context_text}
---END OF CONTEXT---
{history_text}
Current Question: {question}

Answer:"""


def ask_question_with_memory(
    file_id: str,
    question: str,
    session_id: str,
    n_chunks: int = 3
) -> Dict[str, Any]:

    # Step 1 — load history
    history = get_or_create_session(session_id)

    # Step 2 — retrieve chunks
    search_result = search_similar_chunks(
        file_id=file_id,
        query=question,
        n_results=n_chunks
    )

    if search_result["status"] == "not_embedded":
        return {
            "status": "error",
            "message": "Document not embedded yet. POST to /embed first.",
            "answer": None
        }

    chunks = search_result["results"]

    # Step 3 — build prompt
    prompt = build_prompt(chunks, question, history)

    # Step 4 — call Groq
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    answer = response.choices[0].message.content

    # Step 5 — save to history
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})

    # Step 6 — return
    return {
        "status": "success",
        "session_id": session_id,
        "question": question,
        "answer": answer,
        "history_length": len(history) // 2,
        "sources": [
            {
                "chunk_index": chunk["chunk_index"],
                "similarity_score": chunk["similarity_score"],
                "excerpt": chunk["text"][:150] + "..."
            }
            for chunk in chunks
        ],
        "model": GROQ_MODEL
    }


def clear_session(session_id: str) -> Dict[str, Any]:
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return {"status": "cleared", "session_id": session_id}
    return {"status": "not_found", "session_id": session_id}


def get_session_history(session_id: str) -> Dict[str, Any]:
    history = chat_sessions.get(session_id, [])
    return {
        "session_id": session_id,
        "history": history,
        "total_messages": len(history),
        "total_exchanges": len(history) // 2
    }

def ask_across_documents(
    file_ids: List[str],
    question: str,
    session_id: str,
    n_results: int = 5
) -> Dict[str, Any]:
    """
    RAG pipeline that searches across MULTIPLE documents.

    Same flow as ask_question_with_memory() but:
    - Searches multiple ChromaDB collections
    - Tags each chunk with its source document
    - Tells the LLM which document each piece of info came from
    """
    from services.vector_store import search_across_documents

    # Step 1 — load session history
    history = get_or_create_session(session_id)

    # Step 2 — search across all documents
    search_result = search_across_documents(
        file_ids=file_ids,
        query=question,
        n_results_per_doc=2,
        total_results=n_results
    )

    if search_result["status"] == "no_results":
        return {
            "status": "error",
            "message": search_result["message"],
            "answer": None
        }

    chunks = search_result["results"]

    # Step 3 — build prompt
    # Note: we include source_file_id in context so LLM
    # can attribute information to specific documents
    context_text = ""
    for i, chunk in enumerate(chunks, start=1):
        context_text += f"\n[Context {i} - from document '{chunk['source_file_id']}']:\n"
        context_text += f"{chunk['text']}\n"

    # Format history
    history_text = ""
    if history:
        history_text = "\n---CONVERSATION HISTORY---\n"
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
        history_text += "---END OF HISTORY---\n"

    prompt = f"""---DOCUMENT CONTEXT (from {len(search_result['searched_docs'])} documents)---
{context_text}
---END OF CONTEXT---
{history_text}
Current Question: {question}

Answer based on the provided context. When referencing information,
mention which document it came from if relevant.

Answer:"""

    # Step 4 — call Groq
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    answer = response.choices[0].message.content

    # Step 5 — save to history
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})

    # Step 6 — return
    return {
        "status": "success",
        "session_id": session_id,
        "question": question,
        "answer": answer,
        "history_length": len(history) // 2,
        "documents_searched": search_result["searched_docs"],
        "sources": [
            {
                "source_file_id": chunk["source_file_id"],
                "chunk_index": chunk["chunk_index"],
                "similarity_score": chunk["similarity_score"],
                "excerpt": chunk["text"][:150] + "..."
            }
            for chunk in chunks
        ],
        "model": GROQ_MODEL
    }