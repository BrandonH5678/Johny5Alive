#!/usr/bin/env python3
"""
Sherlock Text Chunking - Split and score text for LLM processing
Creates semantic chunks with relevance scoring for context injection
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def chunk(txt_path: str, chunk_size: int = 1500, overlap: int = 200) -> str:
    """
    Split text into overlapping chunks and score for relevance

    Args:
        txt_path: Path to normalized .txt file
        chunk_size: Target characters per chunk (default 1500 ~= 375 tokens)
        overlap: Character overlap between chunks (default 200)

    Returns:
        Path to chunks.json file with scored excerpts

    Output format (excerpts.json schema):
    {
        "source": "original_file.txt",
        "total_chunks": N,
        "chunks": [
            {
                "id": 0,
                "start": 0,
                "end": 1500,
                "text": "chunk text...",
                "score": 0.95,
                "tokens_estimate": 375
            },
            ...
        ]
    }
    """
    path = Path(txt_path)

    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {txt_path}")

    # Read text
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    logger.info(f"Chunking {path} ({len(text)} chars)")

    # Split into chunks
    chunks = _split_text(text, chunk_size, overlap)

    # Score chunks (simple scoring for now, can be enhanced with embeddings)
    scored_chunks = _score_chunks(chunks, text)

    # Build output
    output = {
        "source": path.name,
        "source_path": str(path.absolute()),
        "total_chunks": len(scored_chunks),
        "chunk_size": chunk_size,
        "overlap": overlap,
        "chunks": scored_chunks
    }

    # Write chunks.json
    output_dir = "/home/johnny5/Johny5Alive/j5a-nightshift/ops/processed"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{path.stem}_chunks.json")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"Created {len(scored_chunks)} chunks → {output_path}")
    return output_path


def _split_text(text: str, chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    chunk_id = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings in last 100 chars
            search_start = max(start, end - 100)
            last_period = text.rfind('.', search_start, end)
            last_newline = text.rfind('\n\n', search_start, end)

            # Use the closer boundary
            boundary = max(last_period, last_newline)
            if boundary > start:
                end = boundary + 1

        chunk_text = text[start:end].strip()

        if chunk_text:  # Skip empty chunks
            chunks.append({
                "id": chunk_id,
                "start": start,
                "end": end,
                "text": chunk_text,
                "length": len(chunk_text)
            })
            chunk_id += 1

        # Move to next chunk with overlap
        start = end - overlap

        # Ensure we make progress
        if start <= chunks[-1]["start"] if chunks else 0:
            start = end

    return chunks


def _score_chunks(chunks: List[Dict[str, Any]], full_text: str) -> List[Dict[str, Any]]:
    """
    Score chunks for relevance (simple heuristic-based scoring)

    Can be enhanced with:
    - Embeddings-based similarity
    - TF-IDF scoring
    - Query-specific relevance

    For now: simple heuristics based on position and content
    """
    total_length = len(full_text)

    for chunk in chunks:
        score = 1.0

        # Position scoring (beginning and end slightly higher)
        position_ratio = chunk["start"] / total_length
        if position_ratio < 0.1:  # First 10%
            score *= 1.1
        elif position_ratio > 0.9:  # Last 10%
            score *= 1.05

        # Content scoring
        text = chunk["text"]

        # Penalize very short chunks
        if len(text) < 100:
            score *= 0.5

        # Boost chunks with questions (may be important)
        if '?' in text:
            score *= 1.05

        # Boost chunks with numbers/data (may be important facts)
        digit_ratio = sum(c.isdigit() for c in text) / len(text)
        if digit_ratio > 0.05:  # >5% digits
            score *= 1.1

        # Estimate tokens (rough: ~4 chars per token)
        tokens_estimate = len(text) // 4

        # Normalize score to 0-1 range
        chunk["score"] = min(score, 1.0)
        chunk["tokens_estimate"] = tokens_estimate

    # Sort by score (highest first)
    chunks.sort(key=lambda x: x["score"], reverse=True)

    return chunks


def select_excerpts(chunks_json_path: str, max_excerpts: int = 10, max_tokens: int = 3000) -> List[Dict[str, Any]]:
    """
    Select top N chunks for LLM context injection

    Args:
        chunks_json_path: Path to chunks.json file
        max_excerpts: Maximum number of excerpts to select
        max_tokens: Maximum total tokens across all excerpts

    Returns:
        List of selected excerpt dicts (compatible with llm_gateway)
    """
    with open(chunks_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunks = data["chunks"]
    source = data["source"]

    selected = []
    total_tokens = 0

    for chunk in chunks[:max_excerpts]:
        if total_tokens + chunk["tokens_estimate"] > max_tokens:
            break

        # Format for llm_gateway
        excerpt = {
            "text": chunk["text"],
            "source": source,
            "score": chunk["score"],
            "start": chunk["start"],
            "end": chunk["end"]
        }

        selected.append(excerpt)
        total_tokens += chunk["tokens_estimate"]

    logger.info(f"Selected {len(selected)} excerpts (~{total_tokens} tokens)")
    return selected


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test with sample text
    test_dir = "/home/johnny5/Johny5Alive/j5a-nightshift/ops/processed"
    os.makedirs(test_dir, exist_ok=True)

    # Create test text file
    test_file = os.path.join(test_dir, "test_document.txt")
    with open(test_file, 'w') as f:
        f.write("""
# Introduction to Python

Python is a high-level, interpreted programming language. It was created by Guido van Rossum
and first released in 1991. Python emphasizes code readability with significant whitespace.

# Key Features

Python supports multiple programming paradigms, including procedural, object-oriented, and
functional programming. It has a comprehensive standard library, often described as having
"batteries included" philosophy.

# Use Cases

Python is widely used in:
- Web development (Django, Flask)
- Data science (NumPy, Pandas)
- Machine learning (TensorFlow, PyTorch)
- Automation and scripting
- Scientific computing

# Conclusion

Python's simple syntax and extensive ecosystem make it an excellent choice for beginners
and experienced developers alike. Its versatility continues to drive adoption across industries.
        """.strip())

    # Test chunking
    chunks_path = chunk(test_file, chunk_size=300, overlap=50)
    print(f"\nChunks created: {chunks_path}")

    # Display chunks
    with open(chunks_path, 'r') as f:
        data = json.load(f)

    print(f"\nTotal chunks: {data['total_chunks']}")
    for i, chunk in enumerate(data['chunks'][:3]):  # Show top 3
        print(f"\nChunk {i} (score: {chunk['score']:.2f}, ~{chunk['tokens_estimate']} tokens):")
        print(chunk['text'][:150] + "..." if len(chunk['text']) > 150 else chunk['text'])

    # Test excerpt selection
    excerpts = select_excerpts(chunks_path, max_excerpts=5, max_tokens=1000)
    print(f"\n\nSelected {len(excerpts)} excerpts for LLM context")
