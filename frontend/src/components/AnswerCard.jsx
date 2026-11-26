// One answer from the assistant, with the sources it was built from.

// Turns "[1]" or "[1, 2]" inside the answer into small highlighter-yellow badges.
function renderAnswer(text) {
  return text.split(/(\[\d+(?:\s*,\s*\d+)*\])/g).map((part, index) => {
    if (!/^\[\d/.test(part)) return part;
    return part
      .slice(1, -1)
      .split(",")
      .map((number, i) => (
        <sup
          key={`${index}-${i}`}
          className="mx-0.5 rounded bg-mark px-1 text-[0.7rem] font-medium text-mark-ink"
        >
          {number.trim()}
        </sup>
      ));
  });
}

export default function AnswerCard({ message }) {
  const { text, found, sources = [] } = message;

  // Unique page numbers, sorted, for the summary line.
  const pages = [...new Set(sources.map((s) => s.page_number))].sort((a, b) => a - b);
  const label = sources[0]?.location_label ?? "Page";

  // Not-found answers get a calmer, different look.
  if (!found) {
    return (
      <div className="max-w-[90%] rounded-xl border border-line bg-paper px-4 py-3">
        <p className="font-serif leading-relaxed">{text}</p>
        <p className="mt-1 text-xs text-muted">
          Try rewording the question or using words that appear in the document.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-[90%] rounded-xl border border-line bg-white px-4 py-3 shadow-sm">
      <p className="whitespace-pre-wrap break-words font-serif text-[1.02rem] leading-7">
        {renderAnswer(text)}
      </p>

      {sources.length > 0 && (
        <div className="mt-3 border-t border-line pt-3">
          <p className="text-sm">
            <span className="text-muted">Found on {label.toLowerCase()}{pages.length > 1 ? "s" : ""}: </span>
            {pages.map((page) => (
              <span
                key={page}
                className="mr-1.5 rounded bg-mark px-1.5 py-0.5 text-xs font-medium text-mark-ink"
              >
                {label} {page}
              </span>
            ))}
          </p>

          <div className="mt-2 space-y-1.5">
            {sources.map((source) => (
              <details key={source.source_number} className="group rounded-lg border border-line">
                <summary className="flex cursor-pointer items-center gap-2 px-3 py-2 text-sm hover:bg-paper">
                  <sup className="rounded bg-mark px-1 text-[0.7rem] font-medium text-mark-ink">
                    {source.source_number}
                  </sup>
                  <span className="font-medium">
                    {source.location_label} {source.page_number}
                  </span>
                  <span className="ml-auto text-xs text-muted">
                    match {Math.round(source.score * 100)}%
                  </span>
                </summary>
                <blockquote className="whitespace-pre-wrap break-words border-t border-line bg-paper px-3 py-2 font-serif text-sm leading-6 text-ink/90">
                  {source.text}
                </blockquote>
              </details>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
