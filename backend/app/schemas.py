"""
schemas.py
----------
Pydantic models = the "shape" of the JSON that goes in and out of the API.
FastAPI uses them to validate requests and to build the API docs automatically.
"""

from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    """Details shown in the 'Uploaded document' panel."""
    document_id: str
    filename: str
    file_type: str            # "PDF", "DOCX" or "TXT"
    location_label: str       # "Page" (real pages) or "Section" (TXT/DOCX without page breaks)
    num_pages: int            # number of pages (or sections)
    num_chunks: int
    num_characters: int


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)


class SourceChunk(BaseModel):
    """One piece of the document that was used to build the answer."""
    source_number: int        # matches the [1], [2] markers inside the answer
    page_number: int
    location_label: str
    text: str                 # exact excerpt taken from the document
    score: float              # similarity score between 0 and 1


class AskResponse(BaseModel):
    answer: str
    found: bool               # False when the document has no answer
    sources: list[SourceChunk]
