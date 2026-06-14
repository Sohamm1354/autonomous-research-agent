import { useEffect, useState } from "react";
import {
  getHistory,
  getHistoryEntry,
  deleteHistoryEntry,
  deleteAllHistory,
} from "../api";

function timeAgo(isoString) {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins  < 1)   return "Just now";
  if (mins  < 60)  return `${mins}m ago`;
  if (hours < 24)  return `${hours}h ago`;
  return `${days}d ago`;
}

export default function HistorySidebar({ onSelectEntry, currentHistoryId }) {
  const [entries,   setEntries]   = useState([]);
  const [loading,   setLoading]   = useState(false);
  const [deleting,  setDeleting]  = useState(null);

  async function load() {
    setLoading(true);
    try {
      const data = await getHistory();
      setEntries(data.entries);
    } catch (e) {
      console.error("Failed to load history:", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [currentHistoryId]);

  async function handleDelete(e, id) {
    e.stopPropagation();
    setDeleting(id);
    try {
      await deleteHistoryEntry(id);
      setEntries((prev) => prev.filter((en) => en.id !== id));
      if (currentHistoryId === id) onSelectEntry(null);
    } catch (err) {
      console.error("Delete failed:", err);
    } finally {
      setDeleting(null);
    }
  }

  async function handleDeleteAll() {
    if (!window.confirm("Delete all history? This cannot be undone.")) return;
    try {
      await deleteAllHistory();
      setEntries([]);
      onSelectEntry(null);
    } catch (err) {
      console.error("Delete all failed:", err);
    }
  }

  async function handleSelect(id) {
    try {
      const entry = await getHistoryEntry(id);
      onSelectEntry(entry);
    } catch (err) {
      console.error("Failed to load entry:", err);
    }
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-title">History</span>
        {entries.length > 0 && (
          <button
            className="sidebar-clear-btn"
            onClick={handleDeleteAll}
            title="Clear all history"
          >
            Clear all
          </button>
        )}
      </div>

      {loading && (
        <div className="sidebar-empty">Loading…</div>
      )}

      {!loading && entries.length === 0 && (
        <div className="sidebar-empty">
          No research history yet.<br />
          Start a research run to see it here.
        </div>
      )}

      <div className="sidebar-list">
        {entries.map((en) => (
          <div
            key={en.id}
            className={`sidebar-item ${currentHistoryId === en.id ? "active" : ""}`}
            onClick={() => handleSelect(en.id)}
          >
            <div className="sidebar-item-top">
              <span className="sidebar-item-time">{timeAgo(en.created_at)}</span>
              <button
                className="sidebar-delete-btn"
                onClick={(e) => handleDelete(e, en.id)}
                disabled={deleting === en.id}
                title="Delete this entry"
              >
                {deleting === en.id ? "…" : "✕"}
              </button>
            </div>
            <p className="sidebar-item-q">{en.question}</p>
            <div className="sidebar-item-meta">
              <span>{en.source_count} sources</span>
              <span>{Math.round(en.elapsed_sec)}s</span>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}