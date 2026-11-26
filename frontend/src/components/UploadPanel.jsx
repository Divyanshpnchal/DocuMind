import { useRef, useState } from "react";
import Spinner from "./Spinner.jsx";

const ALLOWED = ["pdf", "docx", "txt"];
const MAX_MB = 20; // keep in sync with MAX_UPLOAD_MB in backend/.env

export default function UploadPanel({ onUpload, uploading, error }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [localError, setLocalError] = useState("");

  // Check the file in the browser first, so obvious mistakes fail instantly.
  function handleFile(file) {
    setLocalError("");
    if (!file) return;
    const extension = file.name.split(".").pop().toLowerCase();
    if (!ALLOWED.includes(extension)) {
      setLocalError("Unsupported file type. Please choose a PDF, DOCX or TXT file.");
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setLocalError(`This file is larger than ${MAX_MB} MB.`);
      return;
    }
    onUpload(file);
  }

  const message = localError || error;

  return (
    <div className="rounded-xl border border-line bg-white p-4">
      <h2 className="font-semibold">Upload a document</h2>
      <p className="mt-1 text-sm text-muted">PDF, DOCX or TXT, up to {MAX_MB} MB.</p>

      <button
        type="button"
        disabled={uploading}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          handleFile(e.dataTransfer.files?.[0]);
        }}
        className={`mt-4 flex w-full flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed px-4 py-10 text-center transition-colors disabled:cursor-wait ${
          dragging ? "border-brand bg-brand-soft" : "border-line hover:border-brand hover:bg-brand-soft/50"
        }`}
      >
        {uploading ? (
          <>
            <Spinner label="Reading and indexing your document..." />
            <span className="mt-1 text-xs text-muted">
              The first upload can take longer while the language model loads.
            </span>
          </>
        ) : (
          <>
            <span className="font-medium text-brand-dark">Choose a file</span>
            <span className="text-sm text-muted">or drag and drop it here</span>
          </>
        )}
      </button>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.txt"
        className="hidden"
        onChange={(e) => {
          handleFile(e.target.files?.[0]);
          e.target.value = ""; // lets the user pick the same file again
        }}
      />

      {message && (
        <p role="alert" className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">
          {message}
        </p>
      )}
    </div>
  );
}
