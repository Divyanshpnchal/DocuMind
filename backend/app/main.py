"""
main.py
-------
The FastAPI application: defines the HTTP endpoints the React frontend calls.

    POST   /api/documents                     upload + index a file
    POST   /api/documents/{id}/ask            ask a question
    DELETE /api/documents/{id}                forget a document
    GET    /api/health                        quick "is the server alive?" check

Endpoints are plain `def` (not `async def`) on purpose: embedding and PDF reading are
slow CPU work, and FastAPI runs plain `def` endpoints in a worker thread so the server
stays responsive.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .schemas import AskRequest, AskResponse, DocumentInfo
from .services import embedder, rag_pipeline, session_store
from .services.document_loader import SUPPORTED_EXTENSIONS, DocumentProcessingError
from .services.llm import LLMError

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s: %(message)s")
logger = logging.getLogger("document-qa")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once at startup: load the embedding model so the first upload is fast."""
    try:
        embedder.preload()
    except Exception:
        logger.exception("Could not preload the embedding model (will retry on first upload)")
    yield


app = FastAPI(title="Document-Based Question Answering (RAG)", lifespan=lifespan)

# CORS lets the React app (running on another port) call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _to_info(session: session_store.DocumentSession) -> DocumentInfo:
    return DocumentInfo(
        document_id=session.document_id,
        filename=session.filename,
        file_type=session.file_type,
        location_label=session.location_label,
        num_pages=session.num_pages,
        num_chunks=session.num_chunks,
        num_characters=session.num_characters,
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "llm_configured": bool(config.GEMINI_API_KEY)}


@app.post("/api/documents", response_model=DocumentInfo)
def upload_document(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name      # drop any folder path for safety
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(400, "Unsupported file type. Please upload a PDF, DOCX or TXT file.")

    max_bytes = config.MAX_UPLOAD_MB * 1024 * 1024
    data = file.file.read(max_bytes + 1)            # read one extra byte to detect "too big"
    if not data:
        raise HTTPException(400, "The uploaded file is empty.")
    if len(data) > max_bytes:
        raise HTTPException(413, f"File is too large. The limit is {config.MAX_UPLOAD_MB} MB.")

    try:
        session = rag_pipeline.index_document(filename, data)
    except DocumentProcessingError as exc:
        raise HTTPException(422, str(exc))
    except Exception:
        logger.exception("Unexpected error while indexing '%s'", filename)
        raise HTTPException(
            500, "Something went wrong while processing the document. Check the server logs."
        )

    session_store.save(session)
    return _to_info(session)


@app.post("/api/documents/{document_id}/ask", response_model=AskResponse)
def ask_question(document_id: str, body: AskRequest):
    session = session_store.get(document_id)
    if session is None:
        raise HTTPException(404, "Document not found. Please upload it again.")

    question = body.question.strip()
    if not question:
        raise HTTPException(400, "Please type a question.")

    try:
        return rag_pipeline.answer_question(session, question)
    except LLMError as exc:
        raise HTTPException(502, str(exc))
    except Exception:
        logger.exception("Unexpected error while answering")
        raise HTTPException(500, "Something went wrong while answering. Check the server logs.")


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str):
    session_store.remove(document_id)
    return {"status": "deleted"}
