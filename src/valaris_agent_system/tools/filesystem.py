from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ..runtime.errors import ToolExecutionError
from ..runtime.models import ExecutionContext, RetryPolicy, RiskLevel, ToolSpec
from .base import BaseTool


def resolve_path_within_cwd(cwd: str | None, relative_path: str) -> Path:
    if not cwd:
        raise ToolExecutionError("Execution context is missing a working directory.")

    base_dir = Path(cwd).resolve()
    target_path = (base_dir / relative_path).resolve()
    if base_dir not in target_path.parents and target_path != base_dir:
        raise ToolExecutionError("Target path escapes the configured working directory.")
    return target_path


class WriteNoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    content: str


class WriteNoteOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    written_path: str
    bytes_written: int


class WriteNoteTool(BaseTool):
    spec = ToolSpec(
        name="write_note",
        description="Write a text file inside the current working directory.",
        risk_level=RiskLevel.MEDIUM,
        retry_policy=RetryPolicy(max_attempts=1),
    )
    input_model = WriteNoteInput
    output_model = WriteNoteOutput

    async def execute(
        self,
        payload: WriteNoteInput,
        context: ExecutionContext,
    ) -> WriteNoteOutput:
        target_path = resolve_path_within_cwd(context.cwd, payload.path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        data = payload.content.encode("utf-8")
        target_path.write_bytes(data)
        return WriteNoteOutput(
            written_path=str(target_path),
            bytes_written=len(data),
        )
