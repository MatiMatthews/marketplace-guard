from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..runtime.models import ExecutionContext, RiskLevel, ToolSpec
from .base import BaseTool


class EchoTextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)


class EchoTextOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    echoed_text: str


class EchoTextTool(BaseTool):
    spec = ToolSpec(
        name="echo_text",
        description="Return the same text provided in the input payload.",
        risk_level=RiskLevel.LOW,
    )
    input_model = EchoTextInput
    output_model = EchoTextOutput

    async def execute(
        self,
        payload: EchoTextInput,
        context: ExecutionContext,
    ) -> EchoTextOutput:
        return EchoTextOutput(echoed_text=payload.text)


class SumNumbersInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    left: int
    right: int


class SumNumbersOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int


class SumNumbersTool(BaseTool):
    spec = ToolSpec(
        name="sum_numbers",
        description="Sum two integers and return the result.",
        risk_level=RiskLevel.LOW,
    )
    input_model = SumNumbersInput
    output_model = SumNumbersOutput

    async def execute(
        self,
        payload: SumNumbersInput,
        context: ExecutionContext,
    ) -> SumNumbersOutput:
        return SumNumbersOutput(total=payload.left + payload.right)
