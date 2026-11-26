import { useState } from "react";
import { askQuestion, deleteDocument, uploadDocument } from "./api.js";
import UploadPanel from "./components/UploadPanel.jsx";
import DocumentInfo from "./components/DocumentInfo.jsx";
import ChatWindow from "./components/ChatWindow.jsx";
import ChatInput from "./components/ChatInput.jsx";

// App.jsx holds ALL the shared state. The child components only show things
// and call the functions we pass down as props.
export default function App() {
  const [doc, setDoc] = useState(null);          // info about the uploaded document
  const [messages, setMessages] = useState([]);  // the chat history of this session
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const addMessage = (message) =>
    setMessages((previous) => [...previous, { id: crypto.randomUUID(), ...message }]);

  async function handleUpload(file) {
    setUploading(true);
    setUploadError("");
    try {
      const info = await uploadDocument(file);
      setDoc(info);
      setMessages([]); // new document = fresh chat
    } catch (error) {
      setUploadError(error.message);
    } finally {
      setUploading(false);
    }
  }

  async function handleAsk(question) {
    addMessage({ role: "user", text: question });
    setAsking(true);
    try {
      const result = await askQuestion(doc.document_id, question);
      addMessage({
        role: "assistant",
        text: result.answer,
        found: result.found,
        sources: result.sources,
      });
    } catch (error) {
      addMessage({ role: "error", text: error.message });
    } finally {
      setAsking(false);
    }
  }

  function handleRemove() {
    if (doc) deleteDocument(doc.document_id).catch(() => {}); // best effort
    setDoc(null);
    setMessages([]);
    setUploadError("");
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-line bg-white">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-baseline gap-3">
          <h1 className="text-lg font-semibold tracking-tight">Ask your document</h1>
          <p className="text-sm text-muted hidden sm:block">
            Upload a file, ask in plain English, check the page it came from.
          </p>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 grid gap-4 p-4 lg:grid-cols-[320px_1fr] lg:items-start">
        {/* Left column: upload + document details */}
        <aside className="flex flex-col gap-4">
          {doc ? (
            <DocumentInfo doc={doc} onRemove={handleRemove} />
          ) : (
            <UploadPanel onUpload={handleUpload} uploading={uploading} error={uploadError} />
          )}
        </aside>

        {/* Right column: chat */}
        <section className="flex flex-col rounded-xl border border-line bg-white h-[75vh] lg:h-[calc(100vh-6.5rem)] lg:sticky lg:top-4">
          <ChatWindow messages={messages} asking={asking} hasDocument={Boolean(doc)} />
          <ChatInput onSend={handleAsk} disabled={!doc || asking} hasDocument={Boolean(doc)} />
        </section>
      </main>
    </div>
  );
}
