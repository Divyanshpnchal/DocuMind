"""
chunker.py
----------
STEP 2 of the pipeline: cut each page into small overlapping chunks.

Why chunks?
  - An embedding model works best on short passages (a few sentences).
  - We only want to send the most relevant passages to the LLM, not the whole file.

Important rule: a chunk NEVER crosses a page boundary.
That is how every chunk keeps one exact page number.

Overlap: the end of one chunk is repeated at the start of the next one,
so a sentence on the border is not cut off from its context.
"""

import re
from dataclasses import dataclass

from .document_loader import Page

MIN_CHUNK_CHARS = 20  # ignore tiny leftovers such as page numbers


@dataclass
class Chunk:
    chunk_id: int
    page_number: int
    text: str


def split_into_chunks(pages: list[Page], chunk_size: int, overlap: int) -> list[Chunk]:
    """Turn a list of pages into a flat list of chunks."""
    chunks: list[Chunk] = []

    for page in pages:
        sentences = _split_sentences(_clean_text(page.text), max_len=chunk_size)
        current: list[str] = []
        current_len = 0

        for sentence in sentences:
            # Chunk is full -> save it, then start the next one with some overlap.
            if current and current_len + len(sentence) + 1 > chunk_size:
                chunks.append(_make_chunk(len(chunks), page.number, current))
                current = _overlap_tail(current, overlap)
                current_len = sum(len(s) + 1 for s in current)

            current.append(sentence)
            current_len += len(sentence) + 1

        if current:
            chunks.append(_make_chunk(len(chunks), page.number, current))

    return [chunk for chunk in chunks if len(chunk.text) >= MIN_CHUNK_CHARS]


def _make_chunk(chunk_id: int, page_number: int, sentences: list[str]) -> Chunk:
    return Chunk(chunk_id=chunk_id, page_number=page_number, text=" ".join(sentences).strip())


def _clean_text(text: str) -> str:
    """Fix the messy spacing and line breaks that come out of PDFs."""
    text = text.replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)                 # many spaces -> one space
    text = re.sub(r"\n{2,}", "\n\n", text)              # many blank lines -> one
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)        # single line break -> space
    return text.strip()


def _split_sentences(text: str, max_len: int) -> list[str]:
    """Split on . ! ? and blank lines. Very long 'sentences' are cut by length."""
    parts = re.split(r"(?<=[.!?])\s+|\n\s*\n", text)
    sentences: list[str] = []
    for part in parts:
        part = part.strip()
        while len(part) > max_len:            # safety for text without punctuation
            sentences.append(part[:max_len])
            part = part[max_len:].strip()
        if part:
            sentences.append(part)
    return sentences


def _overlap_tail(sentences: list[str], overlap: int) -> list[str]:
    """Return the last few sentences whose total length is at most `overlap`."""
    tail: list[str] = []
    total = 0
    for sentence in reversed(sentences):
        if total + len(sentence) + 1 > overlap:
            break
        tail.insert(0, sentence)
        total += len(sentence) + 1
    return tail
