// A small loading circle. Pass a label to show text next to it.
export default function Spinner({ label }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-muted" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-line border-t-brand" />
      {label}
    </span>
  );
}
