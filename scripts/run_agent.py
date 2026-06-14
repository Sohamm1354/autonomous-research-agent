import sys
import time

sys.path.insert(0, ".")

from app.core.logger import setup_logging
from app.agent.graph import agent_graph


def make_initial_state(question: str) -> dict:
    return {
        "question":        question,
        "sub_queries":     [],
        "plan_approved":   False,
        "search_results":  [],
        "failed_urls":     [],
        "final_report":    "",
        "reflection":      "",
        "run_id":          "cli-test-001",
        "total_tokens":    0,
        "total_cost_usd":  0.0,
        "elapsed_seconds": 0.0,
        "messages":        [],
    }


def run(question: str):
    setup_logging()
    thread_id = "cli-test-001"
    config    = {"configurable": {"thread_id": thread_id}}

    print("\n" + "=" * 65)
    print("  RESEARCH AGENT")
    print("=" * 65)
    print(f"  Question: {question}")
    print("=" * 65 + "\n")

    # ── Step 1: run planner (graph pauses before tools) ──────────────
    print("⏳  Running planner...")

    for _ in agent_graph.stream(
        make_initial_state(question),
        config,
        stream_mode="values",
    ):
        pass  # consume stream until interrupt

    # Read sub_queries from checkpoint
    snapshot    = agent_graph.get_state(config)
    sub_queries = snapshot.values.get("sub_queries", [])

    print("\n📋  Sub-queries the agent plans to search:\n")
    for i, q in enumerate(sub_queries, 1):
        print(f"    {i}. {q}")

    # ── Step 2: human approval ────────────────────────────────────────
    print("\n" + "-" * 65)
    approval = input("  Approve this plan? (y/n): ").strip().lower()
    if approval != "y":
        print("\n  Plan rejected. Exiting.\n")
        return

    # ── Step 3: resume from checkpoint ───────────────────────────────
    print("\n⏳  Researching... (takes 60–120 seconds)\n")
    t0 = time.time()

    # Write approval into the saved state
    agent_graph.update_state(config, {"plan_approved": True})

    # Resume — pass None so it continues from checkpoint
    final_state = None
    for event in agent_graph.stream(
        None,
        config,
        stream_mode="values",
    ):
        final_state = event

    elapsed = round(time.time() - t0, 1)

    # Fallback: read directly from checkpoint if stream gave nothing
    if not final_state:
        final_state = agent_graph.get_state(config).values

    # ── Output ────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  FINAL REPORT")
    print("=" * 65)
    print(final_state.get("final_report", "No report generated."))

    print("\n" + "-" * 65)
    print(f"  💡 Reflection : {final_state.get('reflection', 'N/A')}")
    print(f"  ❌ Failed URLs: {final_state.get('failed_urls', [])}")
    # Token count lives in the node logs, not state — show source count instead
    sources = final_state.get("search_results", [])
    print(f"  📊 Sources used : {len(sources)}")
    print(f"  📝 Report length: {len(final_state.get('final_report', ''))} chars")
    print(f"  ⏱  Time taken : {elapsed}s")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    q = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "What is the current state of AI in healthcare in India?"
    )
    run(q)