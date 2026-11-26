"""
document_loader.py
------------------
STEP 1 of the pipeline: read the uploaded file and get plain text,
while remembering which PAGE each piece of text came from.

Output: a list of Page(number, text).

- PDF  -> real page numbers (PyMuPDF reads page by page).
- DOCX -> real page numbers if the file has page-break markers (Word saves them).
          If not, we split the text into "Sections" instead of inventing pages.
- TXT  -> form-feed characters (\\f) are treated as page breaks, otherwise "Sections".
"""

import io
import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf  # PyMuPDF
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
SECTION_SIZE_CHARS = 3000  # size of one "Section" when a file has no real pages


class DocumentProcessingError(Exception):
    """Raised when a file cannot be read. The message is safe to show to the user."""


@dataclass
class Page:
    number: int   # 1-based page (or section) number
    text: str


@dataclass
class LoadedDocument:
    pages: list[Page]
    location_label: str   # "Page" or "Section"
    file_type: str        # "PDF", "DOCX" or "TXT"


def load_document(filename: str, data: bytes) -> LoadedDocument:
    """Pick the right reader for the file type and return its pages."""
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        document = _load_pdf(data)
    elif extension == ".docx":
        document = _load_docx(data)
    elif extension == ".txt":
        document = _load_txt(data)
    else:
        raise DocumentProcessingError(
            "Unsupported file type. Please upload a PDF, DOCX or TXT file."
        )

    # Remove empty pages but KEEP the original numbers, so page 5 stays page 5.
    document.pages = [page for page in document.pages if page.text.strip()]
    if not document.pages:
        raise DocumentProcessingError(
            "No readable text was found in this file. "
            "If it is a scanned PDF (only images), it needs OCR first."
        )
    return document


# ---------------------------------------------------------------- PDF
def _load_pdf(data: bytes) -> LoadedDocument:
    if b"%PDF" not in data[:1024]:
        raise DocumentProcessingError("This file does not look like a valid PDF.")
    try:
        pdf = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise DocumentProcessingError(
            "Could not open this PDF. The file may be corrupted."
        ) from exc

    with pdf:
        if pdf.needs_pass:
            raise DocumentProcessingError(
                "This PDF is password protected. Please upload an unlocked copy."
            )
        # enumerate(..., start=1): the first PDF page is page 1, not 0
        pages = [
            Page(number=index, text=page.get_text("text"))
            for index, page in enumerate(pdf, start=1)
        ]
    return LoadedDocument(pages=pages, location_label="Page", file_type="PDF")


# --------------------------------------------------------------- DOCX
def _load_docx(data: bytes) -> LoadedDocument:
    if not data.startswith(b"PK"):  # DOCX files are ZIP archives
        raise DocumentProcessingError(
            "This file does not look like a valid DOCX. (Old .doc files are not supported.)"
        )
    try:
        document = Document(io.BytesIO(data))
    except Exception as exc:
        raise DocumentProcessingError(
            "Could not open this Word file. It may be corrupted."
        ) from exc

    body = document.element.body

    # DOCX has no fixed "pages" - Word decides them when it renders the file.
    # But Word leaves markers when it saves:
    #   <w:lastRenderedPageBreak/>  = "a new page started here" (most accurate)
    #   <w:br w:type="page"/>       = a manual page break
    # We use the first kind if it exists, otherwise the second kind.
    if body.xpath(".//w:lastRenderedPageBreak"):
        break_marker = ".//w:lastRenderedPageBreak"
    else:
        break_marker = './/w:br[@w:type="page"]'

    page_texts: list[list[str]] = [[]]   # page_texts[0] = lines of page 1, ...

    # Go through the body in order so paragraphs and tables stay in reading order.
    for element in body.iterchildren():
        tag = element.tag.split("}")[-1]  # strip the XML namespace

        if tag == "p":
            if element.xpath(break_marker):
                page_texts.append([])     # a new page starts at this paragraph
            text = Paragraph(element, document).text.strip()
            if text:
                page_texts[-1].append(text)

        elif tag == "tbl":
            for row in Table(element, document).rows:
                cells: list[str] = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    # merged cells repeat the same text, so skip duplicates
                    if cell_text and (not cells or cells[-1] != cell_text):
                        cells.append(cell_text)
                if cells:
                    page_texts[-1].append(" | ".join(cells))

    if len(page_texts) > 1:
        pages = [
            Page(number=index, text="\n".join(lines))
            for index, lines in enumerate(page_texts, start=1)
        ]
        return LoadedDocument(pages=pages, location_label="Page", file_type="DOCX")

    # No page markers at all -> be honest and call the parts "Sections".
    full_text = "\n\n".join(page_texts[0])
    return LoadedDocument(
        pages=_split_into_sections(full_text), location_label="Section", file_type="DOCX"
    )


# ---------------------------------------------------------------- TXT
def _load_txt(data: bytes) -> LoadedDocument:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("latin-1")  # never fails, good enough for old text files

    if "\x00" in text:
        raise DocumentProcessingError("This file looks like a binary file, not plain text.")

    if "\f" in text:  # form feed = page break in plain text
        pages = [Page(number=i, text=part) for i, part in enumerate(text.split("\f"), start=1)]
        return LoadedDocument(pages=pages, location_label="Page", file_type="TXT")

    return LoadedDocument(
        pages=_split_into_sections(text), location_label="Section", file_type="TXT"
    )


# ------------------------------------------------------------- helpers
def _split_into_sections(text: str) -> list[Page]:
    """Group paragraphs into sections of roughly SECTION_SIZE_CHARS characters."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    sections: list[str] = []
    current: list[str] = []
    size = 0

    for paragraph in paragraphs:
        if current and size + len(paragraph) > SECTION_SIZE_CHARS:
            sections.append("\n\n".join(current))
            current, size = [], 0
        current.append(paragraph)
        size += len(paragraph)

    if current:
        sections.append("\n\n".join(current))
    return [Page(number=i, text=t) for i, t in enumerate(sections, start=1)]
