"""
config.py
---------
One place for every setting in the backend.
Values are read from environment variables (or from the .env file),
so API keys are never written inside the code.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env (if the file exists)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ---- LLM (Gemini) ----
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ---- Embeddings ----
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# ---- Chunking ----
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))        # max characters per chunk
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))  # characters shared by neighbours

# ---- Retrieval ----
# The assignment asks for 3-5 chunks, so we clamp the value into that range.
TOP_K: int = max(3, min(5, int(os.getenv("TOP_K", "4"))))
# Chunks less similar than this are treated as "not related to the question".
MIN_SIMILARITY: float = float(os.getenv("MIN_SIMILARITY", "0.20"))

# ---- Upload / server ----
MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "20"))
MAX_DOCUMENTS_IN_MEMORY: int = 10
ALLOWED_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# The exact sentence the assignment wants when the answer is not in the document.
NOT_FOUND_MESSAGE = "I couldn't find this information in the uploaded document."

GEMINI_FALLBACK_MODELS: list[str] = [
    m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.5-flash-lite").split(",") if m.strip()
]