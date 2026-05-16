# services/pdf_parser.py
#
# RESPONSIBILITY: Everything related to reading and chunking PDF files.
# This is a "service" — pure business logic, no HTTP, no FastAPI.
# Routes call this service. The service doesn't know or care about HTTP.
#
# WHY separate from routes?
# Tomorrow if you switch from PDF to Word docs, you only change this file.
# The routes don't need to change at all. That's good architecture.

import fitz  # PyMuPDF — 'fitz' is its legacy import name, don't let it confuse you
import os
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ── Constants ────────────────────────────────────────────────────────────────
# These numbers are tuned for medical documents — we'll explain each below
CHUNK_SIZE = 500        # Max characters per chunk
CHUNK_OVERLAP = 100     # Characters shared between consecutive chunks


# ── Core Functions ────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> Dict[str, Any]:
    """
    Opens a PDF file and extracts all text, page by page.

    Args:
        file_path: Absolute path to the PDF file on disk

    Returns:
        A dict containing:
        - full_text: entire document as one string
        - pages: list of {page_number, text, char_count} per page
        - total_pages: number of pages
        - total_characters: total character count
    """

    # Verify the file actually exists before trying to open it
    # This gives a clear error instead of a cryptic PyMuPDF crash
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found at path: {file_path}")

    # fitz.open() loads the PDF into memory
    # 'doc' is now a PyMuPDF Document object — iterable, one item per page
    doc = fitz.open(file_path)

    pages_data = []
    full_text_parts = []

    # Iterate through every page in the document
    # enumerate gives us (index, page) — we add 1 so pages start at 1 not 0
    for page_num, page in enumerate(doc, start=1):

        # .get_text() extracts all readable text from this page
        # "text" mode = plain text, strips formatting, keeps words
        page_text = page.get_text("text")

        # Skip completely empty pages (common in scanned PDFs)
        if not page_text.strip():
            continue

        pages_data.append({
            "page_number": page_num,
            "text": page_text,
            "char_count": len(page_text)
        })

        full_text_parts.append(page_text)

    # Close the document to free memory — like closing a file after reading
    doc.close()

    # Join all pages into one big string with clear page separators
    full_text = "\n\n--- PAGE BREAK ---\n\n".join(full_text_parts)

    return {
        "full_text": full_text,
        "pages": pages_data,
        "total_pages": len(pages_data),
        "total_characters": len(full_text)
    }


def chunk_text(full_text: str) -> List[Dict[str, Any]]:
    """
    Splits a large text string into overlapping chunks using LangChain's
    RecursiveCharacterTextSplitter.

    WHY RecursiveCharacterTextSplitter?
    It tries to split on natural boundaries in this order:
      1. Paragraphs (\n\n)  — preferred, keeps ideas together
      2. Sentences (\n)     — fallback
      3. Words (space)      — last resort
      4. Characters         — absolute last resort
    This means chunks respect meaning as much as possible.

    Args:
        full_text: The entire document as a single string

    Returns:
        List of chunk dicts with text and metadata
    """

    # Initialize the splitter with our constants
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,        # Each chunk max 500 chars
        chunk_overlap=CHUNK_OVERLAP,  # 100 chars shared with next chunk
        length_function=len,          # Use character count (not token count)
        separators=["\n\n", "\n", " ", ""]  # Priority order for splitting
    )

    # split_text returns a plain list of strings
    raw_chunks = splitter.split_text(full_text)

    # Enrich each chunk with metadata — this becomes very useful in RAG
    # When we retrieve a chunk, we'll know exactly where it came from
    chunks = []
    for index, chunk_text_content in enumerate(raw_chunks):
        chunks.append({
            "chunk_index": index,           # Position in document
            "text": chunk_text_content,     # The actual content
            "char_count": len(chunk_text_content),  # Size of this chunk
            "word_count": len(chunk_text_content.split()),  # Rough word count
        })

    return chunks


def parse_and_chunk_pdf(file_path: str) -> Dict[str, Any]:
    """
    Master function — combines extraction + chunking into one call.
    This is what the route will call. Clean single entry point.

    Args:
        file_path: Path to the PDF on disk

    Returns:
        Complete parsing result with text, pages, and chunks
    """

    # Step 1: Extract text from PDF
    extraction_result = extract_text_from_pdf(file_path)

    # Step 2: Chunk the full text
    chunks = chunk_text(extraction_result["full_text"])

    # Step 3: Combine and return everything
    return {
        "total_pages": extraction_result["total_pages"],
        "total_characters": extraction_result["total_characters"],
        "total_chunks": len(chunks),
        "pages": extraction_result["pages"],
        "chunks": chunks
    }