import { useState } from "react";

export default function ChatInput({ onSend, disabled, hasDocument }) {
  const [value, setValue] = useState("");

  function submit() {
    const question = value.trim();
    if (!question || disabled) return;
    onSend(question);
    setValue("");
  }

  return (
    <form
      className="flex items-end gap-2 border-t border-line p-3"
      onSubmit={(e) => { e.preventDefault(); submit(); }}
    >
      <textarea
        value={value}
        rows={1}
        maxLength={1000}
        disabled={!hasDocument}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          // Enter sends, Shift+Enter makes a new line
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        placeholder={hasDocument ? "Ask a question about your document" : "Upload a document to start"}
        aria-label="Your question"
        className="max-h-32 min-h-[2.75rem] flex-1 resize-none rounded-lg border border-line px-3 py-2.5 text-sm disabled:bg-paper"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="h-11 rounded-lg bg-brand px-4 text-sm font-medium text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-40"
      >
        Ask
      </button>
    </form>
  );
}
