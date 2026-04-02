from __future__ import annotations

import uuid
from pathlib import Path
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from valaris_agent_system.policy.engine import ExplicitToolRule, PolicyEngine, RiskPolicyRule
from valaris_agent_system.runtime.agent_runtime import AgentRuntime
from valaris_agent_system.runtime.models import (
    AssistantResponse,
    ConversationMessage,
    RiskLevel,
    ToolCall,
    ToolResultEnvelope,
    ToolSpec,
    TurnRequest,
    TurnResult,
)
from valaris_agent_system.runtime.providers import BaseProvider
from valaris_agent_system.sessions.store import Checkpoint, FileSessionStore, SessionState
from valaris_agent_system.tools.registry import ToolRegistry

from .tools import (
    DownloadDocumentTool,
    ExtractDocumentTextTool,
    StoreDocumentReportTool,
    ValidateDocumentTool,
)


class DocumentJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    source_uri: str = Field(min_length=1)
    download_path: str = "artifacts/downloads/document.txt"
    report_path: str = "artifacts/reports/document_report.json"
    min_char_count: int = 50
    required_terms: List[str] = Field(default_factory=list)


class DocumentWorkflowProvider(BaseProvider):
    async def respond(
        self,
        messages: List[ConversationMessage],
        tools: List[ToolSpec],
    ) -> AssistantResponse:
        if not messages:
            raise ValueError("No messages were provided to the workflow provider.")

        last_message = messages[-1]
        if last_message.role == "user":
            return self._start_workflow(last_message.content)
        if last_message.role == "tool":
            return self._continue_workflow(messages)

        return AssistantResponse(content="No workflow action was taken.")

    def _start_workflow(self, job_payload: str) -> AssistantResponse:
        job = DocumentJob.model_validate_json(job_payload)
        return AssistantResponse(
            content="Downloading document.",
            tool_calls=[
                ToolCall(
                    id=str(uuid.uuid4()),
                    name="download_document",
                    arguments={
                        "source_uri": job.source_uri,
                        "target_path": job.download_path,
                    },
                )
            ],
        )

    def _continue_workflow(
        self,
        messages: List[ConversationMessage],
    ) -> AssistantResponse:
        job = self._current_job(messages)
        last_tool_message = messages[-1]
        tool_result = ToolResultEnvelope.model_validate_json(last_tool_message.content)

        if not tool_result.ok:
            return AssistantResponse(
                content=(
                    f"Document workflow stopped at '{last_tool_message.tool_name}' "
                    f"with error: {tool_result.error}"
                )
            )

        if last_tool_message.tool_name == "download_document":
            return AssistantResponse(
                content="Extracting document text.",
                tool_calls=[
                    ToolCall(
                        id=str(uuid.uuid4()),
                        name="extract_document_text",
                        arguments=tool_result.data or {},
                    )
                ],
            )

        if last_tool_message.tool_name == "extract_document_text":
            arguments = dict(tool_result.data or {})
            arguments["min_char_count"] = job.min_char_count
            arguments["required_terms"] = job.required_terms
            return AssistantResponse(
                content="Validating document.",
                tool_calls=[
                    ToolCall(
                        id=str(uuid.uuid4()),
                        name="validate_document",
                        arguments=arguments,
                    )
                ],
            )

        if last_tool_message.tool_name == "validate_document":
            arguments = dict(tool_result.data or {})
            arguments["report_path"] = job.report_path
            return AssistantResponse(
                content="Storing document report.",
                tool_calls=[
                    ToolCall(
                        id=str(uuid.uuid4()),
                        name="store_document_report",
                        arguments=arguments,
                    )
                ],
            )

        if last_tool_message.tool_name == "store_document_report":
            return AssistantResponse(
                content=(
                    "Document workflow completed successfully. "
                    f"Report available at {(tool_result.data or {}).get('report_path', '')}"
                )
            )

        return AssistantResponse(content="Document workflow finished.")

    @staticmethod
    def _current_job(messages: List[ConversationMessage]) -> DocumentJob:
        for message in reversed(messages):
            if message.role == "user":
                return DocumentJob.model_validate_json(message.content)
        raise ValueError("Missing document job definition in conversation history.")


class DocumentAutomationService:
    def __init__(
        self,
        runtime: AgentRuntime,
        session_store: FileSessionStore,
        workspace: Path,
    ) -> None:
        self.runtime = runtime
        self.session_store = session_store
        self.workspace = workspace

    async def run_job(self, job: DocumentJob) -> TurnResult:
        history = self.session_store.load_history(job.session_id)
        request = TurnRequest(
            session_id=job.session_id,
            message=job.model_dump_json(),
            history=history,
            cwd=str(self.workspace),
            approved_risk_levels={RiskLevel.MEDIUM},
        )
        result = await self.runtime.run(request)
        self.session_store.save_result(result)
        return result

    async def submit_job(self, job: DocumentJob) -> SessionState:
        await self.run_job(job)
        session = self.get_job(job.session_id)
        if session is None:
            raise RuntimeError(f"Session '{job.session_id}' was not persisted.")
        return session

    def get_job(self, session_id: str) -> SessionState | None:
        return self.session_store.load_session(session_id)

    def list_checkpoints(self, session_id: str) -> List[Checkpoint]:
        return self.session_store.list_checkpoints(session_id)


def build_document_runtime() -> AgentRuntime:
    registry = ToolRegistry()
    registry.register(DownloadDocumentTool())
    registry.register(ExtractDocumentTextTool())
    registry.register(ValidateDocumentTool())
    registry.register(StoreDocumentReportTool())

    policy_engine = PolicyEngine(
        rules=[
            ExplicitToolRule(),
            RiskPolicyRule(auto_allow_until=RiskLevel.LOW),
        ]
    )

    return AgentRuntime(
        provider=DocumentWorkflowProvider(),
        registry=registry,
        policy_engine=policy_engine,
    )
