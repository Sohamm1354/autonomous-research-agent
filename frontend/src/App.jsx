import { useState } from "react";
import QuestionForm     from "./components/QuestionForm";
import PlanApproval     from "./components/PlanApproval";
import ResearchProgress from "./components/ResearchProgress";
import ReportViewer     from "./components/ReportViewer";
import HistorySidebar   from "./components/HistorySidebar";
import { startResearch, approveResearch } from "./api";
import "./App.css";

const STAGES = {
  INPUT:    "input",
  PLAN:     "plan",
  PROGRESS: "progress",
  REPORT:   "report",
};

const STAGE_ORDER = [STAGES.INPUT, STAGES.PLAN, STAGES.PROGRESS, STAGES.REPORT];
const STEP_LABELS = ["Question", "Plan", "Research", "Report"];

export default function App() {
  const [stage,         setStage]         = useState(STAGES.INPUT);
  const [threadId,      setThreadId]      = useState(null);
  const [subQueries,    setSubQueries]    = useState([]);
  const [result,        setResult]        = useState(null);
  const [error,         setError]         = useState(null);
  const [loading,       setLoading]       = useState(false);
  const [currentHistId, setCurrentHistId] = useState(null);

  // ── Step 1: start research (runs planner) ──────────────────
  async function handleStart(question) {
    if (!question || question.trim().length < 10) {
      setError("Please enter a question with at least 10 characters.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const data = await startResearch(question);
      setThreadId(data.thread_id);
      setSubQueries(data.sub_queries);
      setStage(STAGES.PLAN);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // ── Step 2: approve plan → run full agent ──────────────────
  async function handleApprove(queries) {
    setError(null);
    setLoading(true);
    setStage(STAGES.PROGRESS);   // show progress screen immediately

    try {
      const data = await approveResearch(threadId, queries);
      setResult(data);
      setCurrentHistId(data.history_id);
      setStage(STAGES.REPORT);
    } catch (e) {
      if (
        e.message.includes("429") ||
        e.message.toLowerCase().includes("rate")
      ) {
        setError(
          "Groq rate limit hit. Wait 60 seconds then click Approve again."
        );
      } else {
        setError(e.message);
      }
      setStage(STAGES.PLAN);
    } finally {
      setLoading(false);
    }
  }

  // ── Reset to fresh state ───────────────────────────────────
  function handleReset() {
    setStage(STAGES.INPUT);
    setThreadId(null);
    setSubQueries([]);
    setResult(null);
    setError(null);
    setLoading(false);
    setCurrentHistId(null);
  }

  // ── Load a history entry into the report view ──────────────
  function handleSelectHistory(entry) {
    if (!entry) return;
    setResult({
      question:       entry.question,
      final_report:   entry.final_report,
      reflection:     entry.reflection,
      failed_urls:    entry.failed_urls,
      elapsed_sec:    entry.elapsed_sec,
      search_results: Array(entry.source_count).fill({}),
    });
    setCurrentHistId(entry.id);
    setStage(STAGES.REPORT);
    setError(null);
  }

  const currentIdx = STAGE_ORDER.indexOf(stage);

  return (
    <div className="layout">

      {/* ── History sidebar ── */}
      <HistorySidebar
        onSelectEntry={handleSelectHistory}
        currentHistoryId={currentHistId}
      />

      {/* ── Main content ── */}
      <main className="main">

        {/* Header */}
        <header className="header">
          <div className="logo">⚡</div>
          <div>
            <h1 className="app-title">Research Agent</h1>
            <p className="app-sub">
              Autonomous AI research · Groq llama-3.1-8b · Tavily search
            </p>
          </div>
          <button
            className="btn new-btn"
            onClick={handleReset}
            style={{ marginLeft: "auto" }}
          >
            + New research
          </button>
        </header>

        {/* Stepper */}
        <div className="stepper">
          {STEP_LABELS.map((label, i) => (
            <div key={label} className="stepper-item">
              <div
                className={`step-dot ${
                  i < currentIdx ? "done" : i === currentIdx ? "active" : ""
                }`}
              >
                {i < currentIdx ? "✓" : i + 1}
              </div>
              <span
                className={`step-label ${i === currentIdx ? "active" : ""}`}
              >
                {label}
              </span>
              {i < STEP_LABELS.length - 1 && <div className="step-line" />}
            </div>
          ))}
        </div>

        {/* Error banner */}
        {error && (
          <div className="error-box">
            <span>⚠ {error}</span>
            <button className="btn" onClick={() => setError(null)}>
              Dismiss
            </button>
          </div>
        )}

        {/* Stage views */}
        {stage === STAGES.INPUT && (
          <QuestionForm
            onSubmit={handleStart}
            loading={loading}
          />
        )}

        {stage === STAGES.PLAN && (
          <PlanApproval
            subQueries={subQueries}
            onApprove={handleApprove}
            onReject={handleReset}
            loading={loading}
          />
        )}

        {stage === STAGES.PROGRESS && (
          <ResearchProgress
            threadId={threadId}
            onComplete={(reportData) => {
              // Called by ResearchProgress when SSE signals done
              // The approve endpoint already returned the data
              // so this is just a fallback trigger
              if (reportData) {
                setResult(reportData);
                setStage(STAGES.REPORT);
              }
            }}
          />
        )}

        {stage === STAGES.REPORT && (
          <ReportViewer
            result={result}
            onReset={handleReset}
          />
        )}

      </main>
    </div>
  );
}