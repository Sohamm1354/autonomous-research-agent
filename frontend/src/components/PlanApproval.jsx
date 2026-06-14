import { useState } from "react";

export default function PlanApproval({ subQueries, onApprove, onReject, loading }) {
  const [queries, setQueries] = useState(subQueries);

  function updateQuery(i, val) {
    const updated = [...queries];
    updated[i] = val;
    setQueries(updated);
  }

  return (
    <div className="card">
      <p className="section-label">Review search plan</p>
      <p className="meta" style={{ marginBottom: "1rem" }}>
        The agent will run these queries. Edit any before approving.
      </p>
      <div className="query-list">
        {queries.map((q, i) => (
          <div key={i} className="query-item">
            <span className="query-num">{i + 1}</span>
            <input
              className="query-input"
              value={q}
              onChange={(e) => updateQuery(i, e.target.value)}
            />
          </div>
        ))}
      </div>
      <div className="divider" />
      <div className="action-row">
        <button className="btn" onClick={onReject} disabled={loading}>
          ← Start over
        </button>
        <button
          className="btn primary"
          onClick={() => onApprove(queries)}
          disabled={loading}
        >
          {loading ? "Researching… (2–4 min)" : "✓ Approve and research"}
        </button>
      </div>
    </div>
  );
}