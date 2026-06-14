import { useEffect, useState } from "react";

export default function ResearchProgress({ threadId, onComplete }) {
  const [steps, setSteps] = useState([
    { label: "Plan approved",                     status: "done"    },
    { label: "Searching and scraping sources...", status: "running" },
    { label: "Writing report...",                 status: "pending" },
    { label: "Identifying research gaps...",      status: "pending" },
  ]);
  const [statusMsg, setStatusMsg] = useState("Connecting to agent...");

  useEffect(() => {
    if (!threadId) return;

    const es = new EventSource(
      `http://127.0.0.1:8000/research/stream/${threadId}`
    );

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);

        if (data.type === "start") {
          setStatusMsg("Agent is running...");
        }

        if (data.type === "tools_done") {
          setStatusMsg(data.message);
          setSteps((prev) => {
            const updated = [...prev];
            updated[1] = { ...updated[1], status: "done",    label: `Scraped ${data.count} sources ✓` };
            updated[2] = { ...updated[2], status: "running", label: "Writing report..." };
            return updated;
          });
        }

        if (data.type === "writer_done") {
          setStatusMsg("Report complete, identifying gaps...");
          setSteps((prev) => {
            const updated = [...prev];
            updated[2] = { ...updated[2], status: "done",    label: "Report written ✓" };
            updated[3] = { ...updated[3], status: "running", label: "Identifying research gaps..." };
            return updated;
          });
        }

        if (data.type === "reflection_done") {
          setSteps((prev) => {
            const updated = [...prev];
            updated[3] = { ...updated[3], status: "done", label: "Gaps identified ✓" };
            return updated;
          });
        }

        if (data.type === "done") {
          es.close();
          onComplete && onComplete();
        }

        if (data.type === "error") {
          setStatusMsg(`Error: ${data.message}`);
          es.close();
        }

      } catch (err) {
        console.error("SSE parse error:", err);
      }
    };

    es.onerror = () => {
      setStatusMsg("Connection lost. Check if backend is running.");
      es.close();
    };

    return () => es.close();
  }, [threadId]);

  return (
    <div className="card">
      <p className="section-label">Researching</p>
      <div className="progress-list">
        {steps.map((s, i) => (
          <div
            key={i}
            className={`progress-item ${s.status}`}
          >
            {s.status === "done"    && <span className="check">✓</span>}
            {s.status === "running" && <span className="spinner" />}
            {s.status === "pending" && <span className="pending-dot" />}
            {s.label}
          </div>
        ))}
      </div>
      <p className="meta" style={{ marginTop: "0.75rem" }}>
        {statusMsg}
      </p>
      <p className="meta" style={{ marginTop: "0.25rem" }}>
        This takes 2–4 minutes on Groq free tier. Please wait…
      </p>
    </div>
  );
}