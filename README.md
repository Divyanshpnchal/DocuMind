# Document-Based Question Answering System (RAG)

Upload a PDF, DOCX or TXT file, ask questions in plain English, and get answers that come
**only from your document**, with the page numbers and exact excerpts used.

## 1. What is RAG? 

**RAG = Retrieval-Augmented Generation.** A plain LLM answers from what it memorised during
training, so it can be wrong or make things up about *your* file. RAG fixes this in two steps:

1. **Retrieve** - find the few passages of your document that are most related to the question.
2. **Generate** - give only those passages to the LLM and tell it to answer from them.

```
 UPLOAD (once per file)
 file -> extract text per page -> split into chunks -> embeddings -> FAISS index

 ASK (every question)
 question -> embedding -> FAISS finds top-4 similar chunks -> LLM writes answer -> answer + page numbers + excerpts
```

## 2. Folder structure

```
document-qa-rag/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── .env.example              <- copy to .env and add your key
│   └── app/
│       ├── main.py               <- FastAPI endpoints (upload, ask, delete, health)
│       ├── config.py             <- all settings, read from .env
│       ├── schemas.py            <- shape of request/response JSON
│       └── services/
│           ├── document_loader.py  <- PDF/DOCX/TXT -> pages (keeps page numbers)
│           ├── chunker.py          <- pages -> small overlapping chunks
│           ├── embedder.py         <- text -> vectors (Sentence Transformers)
│           ├── vector_store.py     <- FAISS index + similarity search
│           ├── llm.py              <- prompt + Gemini call
│           ├── rag_pipeline.py     <- connects all steps
│           └── session_store.py    <- keeps uploaded documents in memory
└── frontend/
    ├── package.json, vite.config.js, index.html
    └── src/
        ├── main.jsx, index.css
        ├── App.jsx               <- all shared state
        ├── api.js                <- calls to the backend
        └── components/
            ├── UploadPanel.jsx   ├── DocumentInfo.jsx
            ├── ChatWindow.jsx    ├── ChatInput.jsx
            ├── AnswerCard.jsx    └── Spinner.jsx
```

## 3. Setup

You need **Python 3.10+** and **Node.js 18+**.

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # downloads PyTorch, so the first install is big
cp .env.example .env               # Windows: copy .env.example .env
```
Open `backend/.env` and paste your Gemini key (free at https://aistudio.google.com/apikey).
Then start the server:
```bash
uvicorn app.main:app --reload --port 8000
```
The first start downloads the embedding model (about 90 MB). API docs: http://localhost:8000/docs

### Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

## 4. How each part works

| Part | What it does | Key idea |
|---|---|---|
| `document_loader.py` | Reads the file page by page | PDF pages come from PyMuPDF. DOCX uses the page-break markers Word saves. If a DOCX/TXT has no page info, we call the parts **Sections** instead of inventing pages. |
| `chunker.py` | Splits each page into ~800-character chunks with 150 characters of overlap | Chunks never cross a page, so each chunk has one exact page number. Overlap stops sentences on the border losing context. |
| `embedder.py` | `all-MiniLM-L6-v2` turns text into a 384-number vector | Similar meaning = similar vector. Vectors are normalised so dot product = cosine similarity. |
| `vector_store.py` | FAISS `IndexFlatIP` stores vectors and finds the closest ones | One index per document, so documents never mix. |
| `rag_pipeline.py` | Runs retrieval, the safety check, the LLM call, and builds sources | Sources are built from the **real retrieved chunks**, never from LLM text, so they cannot be fake. |
| `llm.py` | Sends excerpts + question to Gemini with strict rules | Low temperature (0.1), "use only the excerpts", exact fallback sentence. |

### How hallucination is controlled (three layers)
1. **Similarity threshold** (`MIN_SIMILARITY`): if no chunk is related enough, the LLM is never called and the fallback message is returned.
2. **Strict prompt**: the LLM must answer only from the numbered excerpts, or reply with the exact sentence *"I couldn't find this information in the uploaded document."*
3. **Real sources only**: page numbers and excerpts come from FAISS results. The LLM only adds `[1]`, `[2]` markers, and the backend ignores any number that does not exist.

### Error handling
Wrong file type, empty file, fake/corrupted PDF or DOCX, password-protected PDF, scanned PDF
(no text), file too large, missing API key, Gemini failures, and a server that is down all show a
clear message in the UI.

## 5. Settings you can change (`backend/.env`)

| Setting | Default | Meaning |
|---|---|---|
| `CHUNK_SIZE` | 800 | Max characters per chunk |
| `CHUNK_OVERLAP` | 150 | Characters repeated between neighbouring chunks |
| `TOP_K` | 4 | Chunks sent to the LLM (kept between 3 and 5) |
| `MIN_SIMILARITY` | 0.20 | Raise it if answers use unrelated text; lower it if good questions get "not found" |
| `GEMINI_MODEL` | gemini-2.5-flash | If Google retires this name, pick a current one in AI Studio |

## 6. Known limits (good to mention in a viva)
- Scanned PDFs need OCR (not included).
- Broad questions like "summarise the whole document" work poorly, because RAG only sees the top few chunks.
- Each question is answered on its own; the chat history is shown but not used for follow-ups like "and what about the second one?".
- Documents live in memory and are forgotten when the server restarts.
- For DOCX, page numbers match what Word saved; a file that was never opened in Word may show Sections.

## 7. Possible viva questions
- **Why chunks, not the whole document?** Embedding models and LLM prompts work best on short passages, and we only want the relevant ones.
- **Why overlap?** So a fact split across a chunk border is still found.
- **What is cosine similarity?** The angle between two vectors. 1 means the same direction (same meaning).
- **Why FAISS?** It searches thousands of vectors very fast. ChromaDB would also work and adds saving to disk.
- **Why not just ask the LLM directly?** It does not know your file and may invent answers. RAG grounds it in your text.
- **How do you show correct page numbers?** The page number is stored with each chunk when the file is read, and travels with it through search to the answer card.

## 8. Ideas to improve it
Save indexes to disk with ChromaDB, add OCR (pytesseract), use chat history for follow-up questions, add a re-ranking model, stream answers token by token.
