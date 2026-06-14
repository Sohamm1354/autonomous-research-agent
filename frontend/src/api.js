const BASE = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const startResearch = (question) =>
  request("/research/start", {
    method: "POST",
    body: JSON.stringify({ question }),
  });

export const approveResearch = (threadId, revisedQueries = null) =>
  request("/research/approve", {
    method: "POST",
    body: JSON.stringify({
      thread_id: threadId,
      approved: true,
      ...(revisedQueries && { revised_queries: revisedQueries }),
    }),
  });

export const getHistory = () =>
  request("/research/history");

export const getHistoryEntry = (id) =>
  request(`/research/history/${id}`);

export const deleteHistoryEntry = (id) =>
  request(`/research/history/${id}`, { method: "DELETE" });

export const deleteAllHistory = () =>
  request("/research/history", { method: "DELETE" });