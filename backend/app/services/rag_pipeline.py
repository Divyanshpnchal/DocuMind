"""
rag_pipeline.py
---------------
Connects all the steps. This is the "brain" of the project.

INDEXING (runs once, when a file is uploaded):
    file -> pages -> chunks -> embeddings -> FAISS index

QUESTION ANSWERING (runs for every question):
    question -> embedding -> top-k similar chunks -> LLM -> answer + sources
"""

import re

from .. import config
from ..schemas import AskResponse, SourceChunk
from . import embedder, llm
from .chunker import split_into_chunks
from .document_loader import DocumentProcessingError, load_document
from .session_store import DocumentSession
from .vector_store import VectorStore


# ------------------------------------------------------------- indexing
def index_document(filename: str, data: bytes) -> DocumentSession:
    loaded = load_document(filename, data)

    chunks = split_into_chunks(loaded.pages, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
    if not chunks:
        raise DocumentProcessingError("The document has too little text to search.")

    embeddings = embedder.embed_texts([chunk.text for chunk in chunks])

    store = VectorStore(dimension=embeddings.shape[1])
    store.add(embeddings, chunks)

    return DocumentSession(
        filename=filename,
        file_type=loaded.file_type,
        location_label=loaded.location_label,
        num_pages=len(loaded.pages),
        num_characters=sum(len(page.text) for page in loaded.pages),
        vector_store=store,
    )


# ------------------------------------------------------------ answering
def answer_question(session: DocumentSession, question: str) -> AskResponse:
    # 1. Embed the question and find the most similar chunks.
    query_vector = embedder.embed_query(question)
    hits = session.vector_store.search(query_vector, config.TOP_K)

    # 2. Guard against hallucination: drop chunks that are not really related.
    #    If nothing is related, we do not even call the LLM.
    hits = [hit for hit in hits if hit.score >= config.MIN_SIMILARITY]
    if not hits:
        return _not_found()

    # 3. Ask the LLM to answer using only those chunks.
    answer = llm.generate_answer(question, hits)
    if _is_not_found(answer):
        return _not_found()

    # 4. Build the sources from the REAL chunks (never from LLM text),
    #    so page numbers and excerpts cannot be made up.
    cited = _cited_numbers(answer, max_number=len(hits))
    sources = [
        SourceChunk(
            source_number=number,
            page_number=hit.chunk.page_number,
            location_label=session.location_label,
            text=hit.chunk.text,
            score=round(max(0.0, min(1.0, hit.score)), 3),
        )
        for number, hit in enumerate(hits, start=1)
        if not cited or number in cited   # if the LLM cited nothing, show all retrieved chunks
    ]
    return AskResponse(answer=answer, found=True, sources=sources)


# -------------------------------------------------------------- helpers
def _not_found() -> AskResponse:
    return AskResponse(answer=config.NOT_FOUND_MESSAGE, found=False, sources=[])


def _is_not_found(answer: str) -> bool:
    """True if the LLM said the answer is missing (ignores curly vs straight apostrophes)."""
    normalised = answer.replace("\u2019", "'").lower()
    return "couldn't find this information in the uploaded document" in normalised


def _cited_numbers(answer: str, max_number: int) -> set[int]:
    """Find markers like [1] or [2][3] in the answer and return {1, 2, 3}."""
    numbers: set[int] = set()
    for group in re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", answer):
        for part in group.split(","):
            number = int(part)
            if 1 <= number <= max_number:   # ignore numbers that do not exist
                numbers.add(number)
    return numbers
