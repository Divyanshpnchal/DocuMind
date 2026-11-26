"""
vector_store.py
---------------
STEP 4: store the chunk embeddings and search them with FAISS.

FAISS is a library made by Facebook/Meta for fast similarity search.
We use IndexFlatIP ("inner product"). Because our vectors are normalised,
inner product = cosine similarity, so a higher score means a closer meaning.

Each uploaded document gets its OWN VectorStore, so answers never mix documents.
"""

from dataclasses import dataclass

import faiss
import numpy as np

from .chunker import Chunk


@dataclass
class SearchHit:
    chunk: Chunk
    score: float   # cosine similarity (higher = more relevant)


class VectorStore:
    def __init__(self, dimension: int):
        self.index = faiss.IndexFlatIP(dimension)
        self.chunks: list[Chunk] = []   # position i here = vector i inside FAISS

    def add(self, embeddings: np.ndarray, chunks: list[Chunk]) -> None:
        self.index.add(embeddings)
        self.chunks.extend(chunks)

    def search(self, query_embedding: np.ndarray, top_k: int) -> list[SearchHit]:
        """Return the top_k chunks most similar to the question, best first."""
        if not self.chunks:
            return []
        k = min(top_k, len(self.chunks))
        scores, ids = self.index.search(query_embedding, k)

        hits: list[SearchHit] = []
        for score, chunk_index in zip(scores[0], ids[0]):
            if chunk_index == -1:   # FAISS uses -1 when it has no result
                continue
            hits.append(SearchHit(chunk=self.chunks[chunk_index], score=float(score)))
        return hits
