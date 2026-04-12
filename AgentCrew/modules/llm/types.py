from pydantic import BaseModel
from typing import List, Literal, Optional


class SampleParam(BaseModel):
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    min_p: Optional[float] = None
    top_k: Optional[int] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    repetition_penalty: Optional[float] = None


class Model(BaseModel):
    """Model metadata class."""

    id: str
    provider: str
    name: str
    description: str
    capabilities: List[
        Literal[
            "tool_use",
            "stream",
            "thinking",
            "vision",
            "structured_output",
        ]
    ]
    default: bool = False
    default_reasoning: Optional[Literal["none", "minimal", "low", "medium", "high"]] = (
        None
    )
    force_sample_params: Optional[SampleParam] = None
    max_context_token: int = 128_000
    input_token_price_1m: float = 0.0
    output_token_price_1m: float = 0.0
    endpoint: Literal["completions", "response"] = "completions"
