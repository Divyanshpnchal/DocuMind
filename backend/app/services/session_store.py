"""
session_store.py
----------------
Keeps each uploaded document (and its vector store) in memory while the server runs.

This is deliberately simple for a lab project: no database, no login.
If you restart the server, uploaded documents are forgotten.
"""

import threading
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field

from .. import config
from .vector_store import VectorStore


@dataclass
class DocumentSession:
    filename: str
    file_type: str
    location_label: str
    num_pages: int
    num_characters: int
    vector_store: VectorStore
    document_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    @property
    def num_chunks(self) -> int:
        return len(self.vector_store.chunks)


_sessions: "OrderedDict[str, DocumentSession]" = OrderedDict()
_lock = threading.Lock()


def save(session: DocumentSession) -> None:
    with _lock:
        _sessions[session.document_id] = session
        while len(_sessions) > config.MAX_DOCUMENTS_IN_MEMORY:
            _sessions.popitem(last=False)   # forget the oldest document


def get(document_id: str) -> DocumentSession | None:
    with _lock:
        return _sessions.get(document_id)


def remove(document_id: str) -> None:
    with _lock:
        _sessions.pop(document_id, None)
