from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from valaris_agent_system.runtime.models import ExecutionContext, RetryPolicy, RiskLevel, ToolSpec
from valaris_agent_system.tools.base import BaseTool
from valaris_agent_system.tools.filesystem import resolve_path_within_cwd


class StoreDocumentReportInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_uri: str
    local_path: str
    bytes_downloaded: int
    sha256: str
    char_count: int
    is_valid: bool
    issues: list[str] = Field(default_factory=list)
    report_path: str = Field(min_length=1)


class StoreDocumentReportOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_path: str


class StoreDocumentReportTool(BaseTool):
    spec = ToolSpec(
        name="store_document_report",
        description="Persist a document validation report to disk.",
        risk_level=RiskLevel.MEDIUM,
        retry_policy=RetryPolicy(max_attempts=1),
    )
    input_model = StoreDocumentReportInput
    output_model = StoreDocumentReportOutput

    async def execute(
        self,
        payload: StoreDocumentReportInput,
        context: ExecutionContext,
    ) -> StoreDocumentReportOutput:
        report_path = resolve_path_within_cwd(context.cwd, payload.report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
        return StoreDocumentReportOutput(report_path=str(report_path))
