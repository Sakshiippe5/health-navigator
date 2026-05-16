# services/rag_service.py
#
# RESPONSIBILITY: The complete RAG pipeline.
# This service connects ChromaDB (retrieval) with Gemini (generation).
#
# Flow:
#   1. Take user question
#   2. Search ChromaDB for relevant chunks
#   3. Build a prompt with those chunks as context
#   4. Send to Gemini
#   5. Return the answer

import google.generativeai as genai
from core.config import GEMINI_API_KEY
from services.vector_store import search_similar_chunks
from typing import Dict, Any

# ── Initialize Gemini ─────────────────────────────────────────────────────────
# Configure the SDK with our API key — done once at module load
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model we want to use
# gemini-1.5-flash = fast, free tier, great for Q&A
model = genai.GenerativeModel("gemini-2.0-flash")

# ── Prompt Template ───────────────────────────────────────────────────────────
# This is the system instruction we give Gemini before every question.
# It tells the model HOW to behave — stay grounded in the document,
# don't make things up, be precise.
SYSTEM_PROMPT = """You are a helpful medical document assistant.
Your job is to answer questions based ONLY on the provided document context.

Rules:
- Answer only from the context provided below
- If the answer is not in the context, say "I couldn't find that information in the document"
- Be precise and cite relevant details from the context
- Keep answers clear and concise
- Do not make up information that isn't in the context
"""


def build_prompt(context_chunks: list, question: str) -> str:
    """
    Builds the full prompt by combining:
    - System instructions
    - Retrieved context chunks
    - User's question

    This is called "prompt engineering" — designing the
    input to get the best possible output from the LLM.

    Args:
        context_chunks: List of relevant chunk dicts from ChromaDB
        question: The user's question

    Returns:
        Complete prompt string ready to send to Gemini
    """

    # Format each chunk with its index for clarity
    context_text = ""
    for i, chunk in enumerate(context_chunks, start=1):
        context_text += f"\n[Context {i}]:\n{chunk['text']}\n"
        context_text += f"(Relevance score: {chunk['similarity_score']})\n"

    # Combine everything into one prompt
    full_prompt = f"""{SYSTEM_PROMPT}

---DOCUMENT CONTEXT---
{context_text}
---END OF CONTEXT---

User Question: {question}

Answer:"""

    return full_prompt


def ask_question(file_id: str, question: str, n_chunks: int = 3) -> Dict[str, Any]:
    """
    The main RAG function — the complete pipeline in one call.

    Step 1: Retrieve relevant chunks from ChromaDB
    Step 2: Build a grounded prompt
    Step 3: Send to Gemini
    Step 4: Return structured response

    Args:
        file_id: Which document to search
        question: User's question in plain English
        n_chunks: How many context chunks to retrieve

    Returns:
        Dict with answer, sources, and metadata
    """

    # ── Step 1: Retrieve ──────────────────────────────────────────────────
    search_result = search_similar_chunks(
        file_id=file_id,
        query=question,
        n_results=n_chunks
    )

    # Handle case where document isn't embedded yet
    if search_result["status"] == "not_embedded":
        return {
            "status": "error",
            "message": "Document not embedded. POST to /embed first.",
            "answer": None
        }

    chunks = search_result["results"]

    # Handle case where no relevant chunks found
    if not chunks:
        return {
            "status": "error",
            "message": "No relevant content found in document.",
            "answer": None
        }

    # ── Step 2: Build Prompt ──────────────────────────────────────────────
    prompt = build_prompt(chunks, question)

    # ── Step 3: Generate Answer ───────────────────────────────────────────
    # generate_content() sends the prompt to Gemini and returns a response
    # .text extracts just the string answer from the response object
    response = model.generate_content(prompt)
    answer = response.text

    # ── Step 4: Return structured result ─────────────────────────────────
    return {
        "status": "success",
        "question": question,
        "answer": answer,
        # Include sources so user knows WHERE the answer came from
        "sources": [
            {
                "chunk_index": chunk["chunk_index"],
                "similarity_score": chunk["similarity_score"],
                "excerpt": chunk["text"][:150] + "..."  # First 150 chars as preview
            }
            for chunk in chunks
        ],
        "chunks_used": len(chunks),
        "model": "gemini-1.5-flash"
    }