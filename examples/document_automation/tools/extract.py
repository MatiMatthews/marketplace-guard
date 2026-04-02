from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from valaris_agent_system.runtime.models import ExecutionContext, RiskLevel, ToolSpec
from valaris_agent_system.tools.base import BaseTool


class ExtractDocumentTextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_uri: str
    local_path: str
    bytes_downloaded: int
    sha256: str


class ExtractDocumentTextOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_uri: str
    local_path: str
    bytes_downloaded: int
    sha256: str
    text_content: str
    char_count: int


class ExtractDocumentTextTool(BaseTool):
    spec = ToolSpec(
        name="extract_document_text",
        description="Extract text content from a downloaded document.",
        risk_level=RiskLevel.LOW,
    )
    input_model = ExtractDocumentTextInput
    output_model = ExtractDocumentTextOutput

    async def execute(
        self,
        payload: ExtractDocumentTextInput,
        context: ExecutionContext,
    ) -> ExtractDocumentTextOutput:
        text_content = Path(payload.local_path).read_text(encoding="utf-8", errors="ignore")
        return ExtractDocumentTextOutput(
            source_uri=payload.source_uri,
            local_path=payload.local_path,
            bytes_downloaded=payload.bytes_downloaded,
            sha256=payload.sha256,
            text_content=text_content,
            char_count=len(text_content),
        )
