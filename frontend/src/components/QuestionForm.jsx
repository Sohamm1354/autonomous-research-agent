import { useState } from "react";

export default function QuestionForm({ onSubmit, loading }) {
  const [question, setQuestion] = useState("");

  const examples = [
    "What is the current state of AI in India?",
    "Latest breakthroughs in large language models 2025",
    "How are companies using RAG in enterprise applications?",
  ];

  return (
    <div className="card">
      <p className="section-label">Research question</p>
      <textarea
        className="question-input"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="What do you want to research? Be specific for better results."
        rows={3}
      />
      <div className="example-row">
        <span className="meta">Try: </span>
        {examples.map((ex) => (
          <button
            key={ex}
            className="example-btn"
            onClick={() => setQuestion(ex)}
          >
            {ex.length > 45 ? ex.slice(0, 45) + "…" : ex}
          </button>
        ))}
      </div>
      <div className="divider" />
      <div className="action-row">
        <span className="meta">
          Agent searches the web, scrapes sources, and produces a cited report
        </span>
        <button
          className="btn primary"
          onClick={() => onSubmit(question)}
          disabled={loading || question.trim().length < 10}
        >
          {loading ? "Planning…" : "Start research →"}
        </button>
      </div>
    </div>
  );
}