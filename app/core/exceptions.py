class ResearchAgentError(Exception):
    """Base — all agent errors inherit from this."""


class PlannerError(ResearchAgentError):
    """Planner failed to parse sub-queries from LLM response."""


class ToolError(ResearchAgentError):
    """A tool (search / scrape / summarise) failed."""
    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(f"[{tool_name}] {message}")


class WriterError(ResearchAgentError):
    """Writer node failed to produce a report."""


class CheckpointNotFoundError(ResearchAgentError):
    """Thread ID not found in checkpoint store."""