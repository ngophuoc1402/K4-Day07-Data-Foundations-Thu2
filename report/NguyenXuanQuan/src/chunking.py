from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Split on sentence boundaries: ". ", "! ", "? " or ".\n"
        # Use regex to split but keep the delimiters attached to the preceding sentence
        pattern = r'(?<=[.!?])\s+|(?<=\.)\n'
        raw_sentences = re.split(pattern, text)

        # Filter out empty strings and strip whitespace
        sentences = [s.strip() for s in raw_sentences if s.strip()]

        if not sentences:
            return [text.strip()] if text.strip() else []

        # Group sentences into chunks of max_sentences_per_chunk
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunk = " ".join(group)
            if chunk:
                chunks.append(chunk)

        return chunks if chunks else [text.strip()]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case: text fits in a single chunk
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text.strip() else []

        # No separators left — force-split character by character
        if not remaining_separators:
            result = []
            for i in range(0, len(current_text), self.chunk_size):
                part = current_text[i : i + self.chunk_size]
                if part:
                    result.append(part)
            return result

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # If separator not in text, try next separator
        if separator not in current_text:
            return self._split(current_text, next_separators)

        # Split by separator
        if separator == "":
            parts = list(current_text)
        else:
            parts = current_text.split(separator)

        # Merge parts into chunks no bigger than chunk_size
        chunks: list[str] = []
        current_chunk_parts: list[str] = []
        current_len = 0

        for part in parts:
            # Length of adding this part (+ separator cost)
            sep_len = len(separator) if current_chunk_parts else 0
            if current_len + sep_len + len(part) <= self.chunk_size:
                current_chunk_parts.append(part)
                current_len += sep_len + len(part)
            else:
                # Flush current chunk
                if current_chunk_parts:
                    merged = separator.join(current_chunk_parts)
                    if merged.strip():
                        chunks.append(merged)
                # Start new chunk with current part
                if len(part) > self.chunk_size:
                    # Part itself too large — recurse with next separators
                    sub_chunks = self._split(part, next_separators)
                    chunks.extend(sub_chunks)
                    current_chunk_parts = []
                    current_len = 0
                else:
                    current_chunk_parts = [part]
                    current_len = len(part)

        # Flush remaining parts
        if current_chunk_parts:
            merged = separator.join(current_chunk_parts)
            if merged.strip():
                chunks.append(merged)

        return chunks if chunks else [current_text]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_product = _dot(vec_a, vec_b)
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(x * x for x in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_chunks = FixedSizeChunker(chunk_size=chunk_size, overlap=0).chunk(text)
        sentence_chunks = SentenceChunker(max_sentences_per_chunk=3).chunk(text)
        recursive_chunks = RecursiveChunker(chunk_size=chunk_size).chunk(text)

        def stats(chunks: list[str]) -> dict:
            count = len(chunks)
            avg_length = (sum(len(c) for c in chunks) / count) if count > 0 else 0.0
            return {
                "count": count,
                "avg_length": round(avg_length, 2),
                "chunks": chunks,
            }

        return {
            "fixed_size": stats(fixed_chunks),
            "by_sentences": stats(sentence_chunks),
            "recursive": stats(recursive_chunks),
        }
