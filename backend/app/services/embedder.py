"""
embedder.py
-----------
STEP 3: turn text into embeddings (lists of numbers) with Sentence Transformers.

An embedding is a vector that captures the MEANING of a sentence.
Sentences with similar meaning get vectors that point in similar directions,
even if they use different words ("car" vs "automobile").

We normalise every vector to length 1. Then the dot product of two vectors
equals their cosine similarity (1 = same meaning, 0 = unrelated).
"""

import logging
import threading

import numpy as np

from .. import config

logger = logging.getLogger(__name__)

_model = None
_model_lock = threading.Lock()


def _get_model():
    """Load the model once and reuse it (loading takes a few seconds)."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                # Imported here so the server starts fast and other modules stay light.
                from sentence_transformers import SentenceTransformer

                logger.info("Loading embedding model '%s' ...", config.EMBEDDING_MODEL)
                _model = SentenceTransformer(config.EMBEDDING_MODEL)
    return _model


def preload() -> None:
    """Called when the server starts, so the first upload is not slow."""
    _get_model()


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed many texts. Returns an array of shape (number_of_texts, 384)."""
    vectors = _get_model().encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return np.ascontiguousarray(vectors, dtype="float32")  # FAISS needs float32


def embed_query(question: str) -> np.ndarray:
    """Embed one question. Returns an array of shape (1, 384)."""
    return embed_texts([question])
