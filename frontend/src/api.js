// api.js - the only file that talks to the backend.
// Components call these small functions instead of using fetch() directly.

const BASE = import.meta.env.VITE_API_URL || "/api";

async function request(path, options) {
  let response;
  try {
    response = await fetch(`${BASE}${path}`, options);
  } catch {
    throw new Error("Cannot reach the server. Make sure the backend is running on port 8000.");
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    // FastAPI sends { detail: "message" } for errors we raised ourselves,
    // and { detail: [ ... ] } for validation errors.
    const detail = data?.detail;
    throw new Error(
      typeof detail === "string" ? detail : `Request failed (status ${response.status}).`
    );
  }
  return data;
}

export function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  return request("/documents", { method: "POST", body: form });
}

export function askQuestion(documentId, question) {
  return request(`/documents/${documentId}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

export function deleteDocument(documentId) {
  return request(`/documents/${documentId}`, { method: "DELETE" });
}
