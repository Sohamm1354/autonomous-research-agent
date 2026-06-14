from langchain_core.callbacks import BaseCallbackHandler
from app.core.cost_tracker import RunCost
from app.core.logger import logger


class CostTrackingCallback(BaseCallbackHandler):
    def __init__(self, run_cost: RunCost):
        self.run_cost = run_cost

    def on_llm_end(self, response, **kwargs) -> None:
        try:
            llm_out = response.llm_output or {}

            # Try standard location first
            usage = llm_out.get("token_usage") or llm_out.get("usage") or {}

            # Fallback: LangChain >=0.2 usage_metadata on generation
            if not usage:
                try:
                    gen  = response.generations[0][0]
                    meta = getattr(gen, "usage_metadata", {}) or {}
                    usage = {
                        "prompt_tokens":     meta.get("input_tokens", 0),
                        "completion_tokens": meta.get("output_tokens", 0),
                    }
                except Exception:
                    pass

            model = llm_out.get("model_name", "llama-3.1-8b-instant")
            self.run_cost.add(
                model=model,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
            )
            logger.debug(
                "llm_call_tracked",
                model=model,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_so_far=self.run_cost.total_tokens,
            )
        except Exception:
            pass  # never let tracking crash the agent