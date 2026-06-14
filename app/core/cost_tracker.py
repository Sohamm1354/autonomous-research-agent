from dataclasses import dataclass, field
from typing import Dict, Any
import copy

GROQ_RATE_LIMIT_TPM = 14_400


@dataclass
class RunCost:
    model_usage: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def add(
        self,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        if model not in self.model_usage:
            self.model_usage[model] = {
                "input": 0,
                "output": 0,
            }

        self.model_usage[model]["input"] += input_tokens
        self.model_usage[model]["output"] += output_tokens

    @property
    def total_tokens(self) -> int:
        return sum(
            usage["input"] + usage["output"]
            for usage in self.model_usage.values()
        )

    @property
    def total_cost_usd(self) -> float:
        return 0.0  # Groq free tier

    @property
    def rate_limit_warning(self) -> bool:
        return self.total_tokens >= (GROQ_RATE_LIMIT_TPM * 0.5)

    def summary(self) -> Dict[str, Any]:
        return {
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "rate_limit_warning": self.rate_limit_warning,
            "breakdown": copy.deepcopy(self.model_usage),
        }