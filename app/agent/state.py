from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # ── Input ──────────────────────────────
    question:        str

    # ── Planner output ─────────────────────
    sub_queries:     List[str]
    plan_approved:   bool

    # ── Tools output ───────────────────────
    search_results:  List[dict]
    failed_urls:     List[str]

    # ── Writer output ──────────────────────
    final_report:    str
    reflection:      str

    # ── Run metadata ───────────────────────
    run_id:          str
    total_tokens:    int
    total_cost_usd:  float
    elapsed_seconds: float

    # ── Conversation memory ─────────────────
    messages: Annotated[list, add_messages]