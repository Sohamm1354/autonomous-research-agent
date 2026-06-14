"""
eval_agent.py — Benchmark the research agent against 10 test questions.

Measures:
  - Success rate (did the agent produce a report?)
  - Report quality (does it contain expected keywords?)
  - Source count (how many sources were used?)
  - Speed (how long did each run take?)
  - Token usage (are we staying inside Groq rate limits?)

Usage:
  python scripts/eval_agent.py
  python scripts/eval_agent.py --questions 3   # run only first 3 questions
"""

import asyncio
import sys
import time
import argparse

sys.path.insert(0, ".")

from app.core.logger import setup_logging
from app.agent.graph import agent_graph
from app.agent.state import AgentState


# ── Test suite ─────────────────────────────────────────────────────────────
# Each entry has:
#   question     : the research question
#   must_contain : keywords that a good report on this topic MUST mention
#                  (used to check report quality automatically)

TEST_QUESTIONS = [
    {
        "question": "What is the current state of AI in healthcare in India?",
        "must_contain": ["AI", "healthcare", "India"],
    },
    {
        "question": "What are the latest breakthroughs in large language models in 2024 and 2025?",
        "must_contain": ["model", "language", "training"],
    },
    {
        "question": "How are electric vehicles impacting the Indian automobile market?",
        "must_contain": ["electric", "vehicle", "India"],
    },
    {
        "question": "What is the current funding landscape for AI startups globally?",
        "must_contain": ["funding", "startup", "AI"],
    },
    {
        "question": "How is generative AI being used in software development today?",
        "must_contain": ["generative", "code", "developer"],
    },
    {
        "question": "What are the main challenges in deploying AI models in production?",
        "must_contain": ["deployment", "model", "production"],
    },
    {
        "question": "What is the current state of quantum computing research?",
        "must_contain": ["quantum", "computing", "qubit"],
    },
    {
        "question": "How are companies using RAG systems in enterprise applications?",
        "must_contain": ["RAG", "retrieval", "enterprise"],
    },
    {
        "question": "What are the most popular open source LLMs available in 2025?",
        "must_contain": ["open source", "model", "LLM"],
    },
    {
        "question": "How is AI regulation developing across the US, EU, and India?",
        "must_contain": ["regulation", "AI", "policy"],
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────

def make_initial_state(question: str, run_id: str) -> AgentState:
    return AgentState(
        question=question,
        sub_queries=[],
        plan_approved=False,
        search_results=[],
        failed_urls=[],
        final_report="",
        reflection="",
        run_id=run_id,
        total_tokens=0,
        total_cost_usd=0.0,
        elapsed_seconds=0.0,
        messages=[],
    )


def check_quality(report: str, must_contain: list[str]) -> tuple[int, list[str]]:
    """
    Returns (score, missing_keywords).
    Score = number of must_contain keywords found in the report (case-insensitive).
    """
    report_lower = report.lower()
    found   = [kw for kw in must_contain if kw.lower() in report_lower]
    missing = [kw for kw in must_contain if kw.lower() not in report_lower]
    return len(found), missing


def print_separator(char="─", width=65):
    print(char * width)


# ── Core eval runner ───────────────────────────────────────────────────────

async def run_single_eval(
    idx: int,
    test: dict,
    auto_approve: bool = True,
) -> dict:
    """
    Run one question through the full agent pipeline.
    Returns a result dict with all metrics.
    """
    question    = test["question"]
    thread_id   = f"eval-{idx:03d}"
    config      = {"configurable": {"thread_id": thread_id}}

    print(f"\n[{idx}] {question}")
    print_separator()

    result = {
        "idx":            idx,
        "question":       question,
        "success":        False,
        "report_length":  0,
        "source_count":   0,
        "failed_urls":    0,
        "quality_score":  0,
        "max_score":      len(test["must_contain"]),
        "missing_kw":     [],
        "elapsed_sec":    0.0,
        "total_tokens":   0,
        "sub_queries":    [],
        "error":          None,
    }

    try:
        t0 = time.time()

        # Step 1 — planner
        print("  ⏳ Planner running...")
        state_result = agent_graph.invoke(
            make_initial_state(question, thread_id),
            config,
        )

        sub_queries = state_result.get("sub_queries", [])
        result["sub_queries"] = sub_queries
        print(f"  📋 Sub-queries: {len(sub_queries)}")
        for q in sub_queries:
            print(f"       • {q}")

        # Step 2 — approve (always auto-approve in eval mode)
        print("  ⏳ Running tools + writer + reflection...")
        final = agent_graph.invoke({"plan_approved": True}, config)

        elapsed = round(time.time() - t0, 1)

        report        = final.get("final_report", "")
        source_count  = len(final.get("search_results", []))
        failed_count  = len(final.get("failed_urls", []))
        total_tokens  = final.get("total_tokens", 0)

        quality_score, missing_kw = check_quality(report, test["must_contain"])

        result.update({
            "success":       bool(report),
            "report_length": len(report),
            "source_count":  source_count,
            "failed_urls":   failed_count,
            "quality_score": quality_score,
            "missing_kw":    missing_kw,
            "elapsed_sec":   elapsed,
            "total_tokens":  total_tokens,
        })

        status = "✅" if result["success"] else "❌"
        print(f"  {status} Done in {elapsed}s")
        print(f"  📄 Report length : {len(report)} chars")
        print(f"  🔗 Sources used  : {source_count} (failed: {failed_count})")
        print(f"  🎯 Quality score : {quality_score}/{len(test['must_contain'])}")
        if missing_kw:
            print(f"  ⚠️  Missing kw    : {missing_kw}")
        print(f"  📊 Tokens used   : {total_tokens}")

    except Exception as e:
        elapsed = round(time.time() - t0, 1)
        result["error"]       = str(e)
        result["elapsed_sec"] = elapsed
        print(f"  ❌ FAILED in {elapsed}s: {e}")

    # Pause between runs to respect Groq rate limits
    print("  ⏸  Waiting 5s before next question (rate limit buffer)...")
    await asyncio.sleep(5)

    return result


# ── Main eval loop ─────────────────────────────────────────────────────────

async def run_eval(num_questions: int):
    setup_logging()

    questions = TEST_QUESTIONS[:num_questions]

    print("\n" + "=" * 65)
    print("  AUTONOMOUS RESEARCH AGENT — EVALUATION SUITE")
    print("=" * 65)
    print(f"  Running {len(questions)} test questions")
    print(f"  Model : llama-3.1-8b-instant (Groq)")
    print(f"  Mode  : auto-approve all plans")
    print("=" * 65)

    all_results = []
    for i, test in enumerate(questions, 1):
        res = await run_single_eval(i, test)
        all_results.append(res)

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  EVALUATION SUMMARY")
    print("=" * 65)

    total          = len(all_results)
    successful     = [r for r in all_results if r["success"]]
    failed         = [r for r in all_results if not r["success"]]
    success_rate   = round(len(successful) / total * 100, 1)

    avg_elapsed    = round(
        sum(r["elapsed_sec"] for r in successful) / max(len(successful), 1), 1
    )
    avg_sources    = round(
        sum(r["source_count"] for r in successful) / max(len(successful), 1), 1
    )
    avg_tokens     = round(
        sum(r["total_tokens"] for r in all_results) / total, 0
    )

    total_quality  = sum(r["quality_score"] for r in successful)
    total_max      = sum(r["max_score"]     for r in successful)
    quality_pct    = round(total_quality / max(total_max, 1) * 100, 1)

    print(f"  Success rate   : {len(successful)}/{total} ({success_rate}%)")
    print(f"  Quality score  : {total_quality}/{total_max} ({quality_pct}%)")
    print(f"  Avg time/run   : {avg_elapsed}s")
    print(f"  Avg sources    : {avg_sources} per report")
    print(f"  Avg tokens     : {int(avg_tokens)} per run")

    if failed:
        print(f"\n  ❌ Failed questions ({len(failed)}):")
        for r in failed:
            print(f"     [{r['idx']}] {r['question'][:60]}...")
            print(f"          Error: {r['error']}")

    # ── Per-question table ─────────────────────────────────────────────────
    print("\n" + "─" * 65)
    print(f"  {'#':<4} {'Q (truncated)':<34} {'Score':<8} {'Time':<8} {'Src'}")
    print("─" * 65)
    for r in all_results:
        q_short = r["question"][:33] + "…" if len(r["question"]) > 33 else r["question"]
        score   = f"{r['quality_score']}/{r['max_score']}"
        elapsed = f"{r['elapsed_sec']}s"
        srcs    = str(r["source_count"]) if r["success"] else "FAIL"
        status  = "✅" if r["success"] else "❌"
        print(f"  {status} {r['idx']:<3} {q_short:<34} {score:<8} {elapsed:<8} {srcs}")

    print("─" * 65)

    # ── README-ready benchmark line ────────────────────────────────────────
    print(f"""
  📋 README benchmark line (copy this into your README.md):
  ─────────────────────────────────────────────────────────
  Evaluated on {total} research questions:
  - Success rate  : {success_rate}%
  - Quality score : {quality_pct}% keyword recall
  - Avg speed     : {avg_elapsed}s per report
  - Avg sources   : {avg_sources} sources per report
  - Model         : llama-3.1-8b-instant (Groq, free tier)
""")

    print("=" * 65 + "\n")


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate the Autonomous Research Agent"
    )
    parser.add_argument(
        "--questions",
        type=int,
        default=10,
        help="Number of test questions to run (default: 10, max: 10)",
    )
    args = parser.parse_args()

    num = min(max(args.questions, 1), len(TEST_QUESTIONS))
    asyncio.run(run_eval(num))