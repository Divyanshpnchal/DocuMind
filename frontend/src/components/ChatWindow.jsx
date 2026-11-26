import { useEffect, useRef } from "react";
import AnswerCard from "./AnswerCard.jsx";
import Spinner from "./Spinner.jsx";

export default function ChatWindow({ messages, asking, hasDocument }) {
  const bottomRef = useRef(null);

  // Scroll to the newest message whenever the chat changes.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, asking]);

  return (
    <div className="flex-1 space-y-4 overflow-y-auto p-4" aria-live="polite">
      {messages.length === 0 && (
        <div className="mx-auto mt-10 max-w-sm text-center">
          <p className="font-medium">
            {hasDocument ? "Your document is ready." : "No document yet."}
          </p>
          <p className="mt-1 text-sm text-muted">
            {hasDocument
              ? 'Ask something specific, like "What is the refund period?" Answers come only from your file.'
              : "Upload a PDF, DOCX or TXT file on the left, then ask questions here."}
          </p>
        </div>
      )}

      {messages.map((message) => {
        if (message.role === "user") {
          return (
            <div key={message.id} className="flex justify-end">
              <p className="max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-br-sm bg-brand px-4 py-2.5 text-sm text-white">
                {message.text}
              </p>
            </div>
          );
        }
        if (message.role === "error") {
          return (
            <p key={message.id} role="alert" className="max-w-[85%] rounded-lg bg-red-50 px-4 py-2.5 text-sm text-red-800">
              {message.text}
            </p>
          );
        }
        return <AnswerCard key={message.id} message={message} />;
      })}

      {asking && (
        <div className="px-1">
          <Spinner label="Searching the document and writing an answer..." />
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
