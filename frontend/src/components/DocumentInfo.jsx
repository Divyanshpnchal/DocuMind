// Shows details about the uploaded document and a button to replace it.
export default function DocumentInfo({ doc, onRemove }) {
  const unit = doc.location_label.toLowerCase(); // "page" or "section"

  const rows = [
    ["Type", doc.file_type],
    [`${doc.location_label}s`, doc.num_pages],
    ["Text chunks", doc.num_chunks],
    ["Characters", doc.num_characters.toLocaleString()],
  ];

  return (
    <div className="rounded-xl border border-line bg-white p-4">
      <h2 className="text-sm text-muted">Uploaded document</h2>
      <p className="mt-1 break-words font-semibold" title={doc.filename}>
        {doc.filename}
      </p>

      <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt className="text-muted">{label}</dt>
            <dd className="font-medium">{value}</dd>
          </div>
        ))}
      </dl>

      {doc.location_label === "Section" && (
        <p className="mt-4 rounded-md bg-brand-soft px-3 py-2 text-xs text-brand-dark">
          This file has no fixed pages, so answers point to numbered {unit}s instead.
        </p>
      )}

      <button
        type="button"
        onClick={onRemove}
        className="mt-4 w-full rounded-lg border border-line px-3 py-2 text-sm font-medium hover:border-brand hover:text-brand-dark"
      >
        Upload a different document
      </button>
    </div>
  );
}
