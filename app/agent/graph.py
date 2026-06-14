from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.agent.state import AgentState
from app.agent.nodes import (
    planner_node,
    tools_node,
    writer_node,
    reflection_node,
)
from app.core.logger import logger


def _route_after_planner(state: AgentState) -> str:
    return "tools" if state.get("plan_approved", False) else END


def build_graph():
    g = StateGraph(AgentState)

    # Node names must NOT match any key in AgentState
    # AgentState has "reflection" as a key, so we name the node "reflect"
    g.add_node("planner", planner_node)
    g.add_node("tools",   tools_node)
    g.add_node("writer",  writer_node)
    g.add_node("reflect", reflection_node)   # ← "reflect" not "reflection"

    g.set_entry_point("planner")

    g.add_conditional_edges(
        "planner",
        _route_after_planner,
        {"tools": "tools", END: END},
    )

    g.add_edge("tools",   "writer")
    g.add_edge("writer",  "reflect")         # ← updated
    g.add_edge("reflect", END)               # ← updated

    memory   = MemorySaver()
    compiled = g.compile(
        checkpointer=memory,
        interrupt_before=["tools"],
    )

    logger.info("graph_compiled")
    return compiled


agent_graph = build_graph()