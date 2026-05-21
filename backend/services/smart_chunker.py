# services/smart_chunker.py
#
# RESPONSIBILITY: Medical-aware document chunking.
# Goes beyond simple character splitting to understand
# the structure of medical documents.
#
# Three strategies:
#   1. Sentence-aware chunking (default, always use)
#   2. Section-aware chunking (for structured medical docs)
#   3. Hybrid chunking (combines both)

import re
import nltk
from typing import List, Dict, Any

# ── Constants ─────────────────────────────────────────────────────────────────
# Medical section headers we look for
# These patterns cover most standard medical document formats
MEDICAL_SECTION_PATTERNS = [
    r"DIAGNOSIS[:\s]",
    r"MEDICATIONS?[:\s]",
    r"PRESCRIPTIONS?[:\s]",
    r"LAB\s+RESULTS?[:\s]",
    r"VITAL\s+SIGNS?[:\s]",
    r"SYMPTOMS?[:\s]",
    r"TREATMENT[:\s]",
    r"FOLLOW[\s-]?UP[:\s]",
    r"ALLERGIES[:\s]",
    r"MEDICAL\s+HISTORY[:\s]",
    r"CHIEF\s+COMPLAINT[:\s]",
    r"ASSESSMENT[:\s]",
    r"PLAN[:\s]",
    r"DISCHARGE\s+SUMMARY[:\s]",
    r"SURGICAL\s+HISTORY[:\s]",
]

# Compile patterns once for efficiency
# re.IGNORECASE = matches "diagnosis" and "DIAGNOSIS" and "Diagnosis"
COMPILED_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in MEDICAL_SECTION_PATTERNS
]

# Chunk size constants
SENTENCE_CHUNK_SIZE = 400       # chars per sentence-aware chunk
SENTENCE_CHUNK_OVERLAP = 80     # overlap between sentence chunks
MIN_CHUNK_SIZE = 50             # ignore chunks smaller than this


# ── Strategy 1: Sentence-Aware Chunking ──────────────────────────────────────

def sentence_aware_chunk(text: str) -> List[Dict[str, Any]]:
    """
    Splits text into chunks that always respect sentence boundaries.

    HOW IT WORKS:
    1. Split text into individual sentences using NLTK
    2. Group sentences together until we approach the size limit
    3. When adding next sentence would exceed limit → start new chunk
    4. Each chunk overlaps slightly with previous (shared sentences)

    WHY BETTER THAN CHARACTER SPLITTING:
    Character splitting: "The patient has diab" | "etes mellitus"
    Sentence splitting:  "The patient has diabetes mellitus." | next sentence

    Args:
        text: Full document text

    Returns:
        List of chunk dicts with text and metadata
    """

    # NLTK's sent_tokenize is smarter than .split(".")
    # It handles: "Dr. Smith prescribed 500mg." correctly
    # It knows "Dr." is an abbreviation, not a sentence end
    try:
        sentences = nltk.sent_tokenize(text)
    except Exception:
        # Fallback if NLTK fails — simple split on periods
        sentences = [s.strip() for s in text.split('.') if s.strip()]

    chunks = []
    current_chunk_sentences = []
    current_length = 0
    chunk_index = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence_length = len(sentence)

        # If adding this sentence would exceed our limit
        # AND we already have some content → save current chunk
        if current_length + sentence_length > SENTENCE_CHUNK_SIZE and current_chunk_sentences:

            chunk_text = " ".join(current_chunk_sentences)

            if len(chunk_text) >= MIN_CHUNK_SIZE:
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                    "word_count": len(chunk_text.split()),
                    "strategy": "sentence_aware",
                    "sentence_count": len(current_chunk_sentences)
                })
                chunk_index += 1

            # OVERLAP: Keep last sentence(s) for next chunk
            # This preserves context at chunk boundaries
            overlap_text = current_length
            overlap_sentences = []
            for s in reversed(current_chunk_sentences):
                if overlap_text - len(s) < SENTENCE_CHUNK_OVERLAP:
                    overlap_sentences.insert(0, s)
                else:
                    break
                overlap_text -= len(s)

            current_chunk_sentences = overlap_sentences
            current_length = sum(len(s) for s in current_chunk_sentences)

        current_chunk_sentences.append(sentence)
        current_length += sentence_length

    # Don't forget the last chunk
    if current_chunk_sentences:
        chunk_text = " ".join(current_chunk_sentences)
        if len(chunk_text) >= MIN_CHUNK_SIZE:
            chunks.append({
                "chunk_index": chunk_index,
                "text": chunk_text,
                "char_count": len(chunk_text),
                "word_count": len(chunk_text.split()),
                "strategy": "sentence_aware",
                "sentence_count": len(current_chunk_sentences)
            })

    return chunks


# ── Strategy 2: Section-Aware Chunking ───────────────────────────────────────

def detect_section_type(text: str) -> str:
    """
    Detects what type of medical section this text belongs to.
    Returns the section name or 'general' if no match found.
    """
    for pattern in COMPILED_PATTERNS:
        match = pattern.search(text)
        if match:
            # Clean up the matched section name
            section = match.group().strip().rstrip(":").strip()
            return section.upper()
    return "GENERAL"


def section_aware_chunk(text: str) -> List[Dict[str, Any]]:
    """
    Splits text by detecting medical section headers first,
    then applies sentence-aware chunking within each section.

    HOW IT WORKS:
    1. Scan text line by line for section headers
    2. When header found → save previous section, start new one
    3. Each section gets chunked with sentence_aware_chunk()
    4. Each chunk tagged with its section type

    EXAMPLE:
    Input:
      "DIAGNOSIS: Type 2 Diabetes
       MEDICATIONS: Metformin 500mg"

    Output:
      chunk_0: "Type 2 Diabetes"    section_type: "DIAGNOSIS"
      chunk_1: "Metformin 500mg"    section_type: "MEDICATIONS"

    Args:
        text: Full document text

    Returns:
        List of chunks with section_type metadata
    """

    lines = text.split('\n')
    sections = []
    current_section_lines = []
    current_section_type = "GENERAL"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if this line is a section header
        detected_type = detect_section_type(line)

        if detected_type != "GENERAL":
            # Save previous section if it has content
            if current_section_lines:
                sections.append({
                    "type": current_section_type,
                    "text": " ".join(current_section_lines)
                })

            # Start new section
            current_section_type = detected_type
            current_section_lines = [line]
        else:
            current_section_lines.append(line)

    # Save the last section
    if current_section_lines:
        sections.append({
            "type": current_section_type,
            "text": " ".join(current_section_lines)
        })

    # Now chunk each section with sentence awareness
    all_chunks = []
    global_index = 0

    for section in sections:
        section_chunks = sentence_aware_chunk(section["text"])

        for chunk in section_chunks:
            chunk["chunk_index"] = global_index
            chunk["section_type"] = section["type"]  # ← key metadata
            chunk["strategy"] = "section_aware"
            all_chunks.append(chunk)
            global_index += 1

    return all_chunks if all_chunks else sentence_aware_chunk(text)


# ── Strategy 3: Hybrid Chunking (Recommended) ────────────────────────────────

def hybrid_chunk(text: str) -> List[Dict[str, Any]]:
    """
    Tries section-aware chunking first.
    Falls back to sentence-aware if no sections detected.

    This is the recommended strategy for medical documents:
    - Structured reports → section-aware
    - Unstructured notes → sentence-aware
    - Always better than raw character splitting

    Args:
        text: Full document text

    Returns:
        Best chunks for this document type
    """

    # Try section-aware first
    section_chunks = section_aware_chunk(text)

    # Check if we found any real sections
    # (not everything tagged as GENERAL)
    has_real_sections = any(
        chunk.get("section_type", "GENERAL") != "GENERAL"
        for chunk in section_chunks
    )

    if has_real_sections:
        # Structured document — use section chunks
        return section_chunks
    else:
        # Unstructured document — use sentence chunks
        chunks = sentence_aware_chunk(text)
        # Mark strategy clearly
        for chunk in chunks:
            chunk["strategy"] = "sentence_aware_fallback"
        return chunks


# ── Stats Helper ──────────────────────────────────────────────────────────────

def get_chunking_stats(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Returns statistics about the chunking result.
    Useful for debugging and comparing strategies.
    """
    if not chunks:
        return {"error": "No chunks produced"}

    char_counts = [c["char_count"] for c in chunks]
    word_counts = [c["word_count"] for c in chunks]

    # Count chunks per section type
    section_distribution = {}
    for chunk in chunks:
        section = chunk.get("section_type", "N/A")
        section_distribution[section] = section_distribution.get(section, 0) + 1

    return {
        "total_chunks": len(chunks),
        "strategy_used": chunks[0].get("strategy", "unknown"),
        "avg_chunk_size": round(sum(char_counts) / len(char_counts)),
        "min_chunk_size": min(char_counts),
        "max_chunk_size": max(char_counts),
        "avg_word_count": round(sum(word_counts) / len(word_counts)),
        "section_distribution": section_distribution
    }