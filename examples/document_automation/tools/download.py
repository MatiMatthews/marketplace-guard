from __future__ import annotations

import hashlib
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field

from valaris_agent_system.runtime.models import ExecutionContext, RetryPolicy, RiskLevel, ToolSpec
from valaris_agent_system.tools.base import BaseTool
from valaris_agent_system.tools.filesystem import resolve_path_within_cwd


class DownloadDocumentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_uri: str = Field(min_length=1)
    target_path: str = Field(min_length=1)


class DownloadDocumentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_uri: str
    local_path: str
    bytes_downloaded: int
    sha256: str


class DownloadDocumentTool(BaseTool):
    spec = ToolSpec(
        name="download_document",
        description="Download a document to the local workspace.",
        risk_level=RiskLevel.MEDIUM,
        retry_policy=RetryPolicy(max_attempts=2, backoff_seconds=0.5),
    )
    input_model = DownloadDocumentInput
    output_model = DownloadDocumentOutput

    async def execute(
        self,
        payload: DownloadDocumentInput,
        context: ExecutionContext,
    ) -> DownloadDocumentOutput:
        request = Request(payload.source_uri, headers={"User-Agent": "valaris-agent-system/0.1"})
        with urlopen(request, timeout=20) as response:
            data = response.read()

        target_path = resolve_path_within_cwd(context.cwd, payload.target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(data)

        return DownloadDocumentOutput(
            source_uri=payload.source_uri,
            local_path=str(target_path),
            bytes_downloaded=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
        )
