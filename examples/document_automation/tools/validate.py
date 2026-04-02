from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field

from valaris_agent_system.runtime.models import ExecutionContext, RiskLevel, ToolSpec
from valaris_agent_system.tools.base import BaseTool


class ValidateDocumentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_uri: str
    local_path: str
    bytes_downloaded: int
    sha256: str
    text_content: str
    char_count: int
    min_char_count: int = 1
    required_terms: List[str] = Field(default_factory=list)


class ValidateDocumentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_uri: str
    local_path: str
    bytes_downloaded: int
    sha256: str
    char_count: int
    is_valid: bool
    issues: List[str] = Field(default_factory=list)


class ValidateDocumentTool(BaseTool):
    spec = ToolSpec(
        name="validate_document",
        description="Validate extracted document content against business rules.",
        risk_level=RiskLevel.LOW,
    )
    input_model = ValidateDocumentInput
    output_model = ValidateDocumentOutput

    async def execute(
        self,
        payload: ValidateDocumentInput,
        context: ExecutionContext,
    ) -> ValidateDocumentOutput:
        issues = []
        if payload.char_count < payload.min_char_count:
            issues.append(
                f"Document contains {payload.char_count} chars, below required minimum {payload.min_char_count}."
            )

        lowered_content = payload.text_content.lower()
        for term in payload.required_terms:
            if term.lower() not in lowered_content:
                issues.append(f"Missing required term: {term}")

        return ValidateDocumentOutput(
            source_uri=payload.source_uri,
            local_path=payload.local_path,
            bytes_downloaded=payload.bytes_downloaded,
            sha256=payload.sha256,
            char_count=payload.char_count,
            is_valid=not issues,
            issues=issues,
        )
