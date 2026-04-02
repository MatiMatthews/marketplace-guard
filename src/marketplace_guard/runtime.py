from __future__ import annotations

import uuid
from pathlib import Path
from typing import List

from valaris_agent_system import (
    AgentRuntime,
    AssistantResponse,
    BaseProvider,
    ConversationMessage,
    ExplicitToolRule,
    FileSessionStore,
    PolicyEngine,
    RiskLevel,
    RiskPolicyRule,
    ToolCall,
    ToolRegistry,
    ToolResultEnvelope,
    ToolSpec,
    TurnRequest,
    TurnResult,
)

from .db import MarketplaceRepository
from .domain import DetectionEngine
from .schemas import RuntimeJob, RuntimeJobResult
from .tools import (
    CalculateMarginTool,
    CreateAlertTool,
    DetectAnomaliesTool,
    GetProductsTool,
    SimulateBlockSkuTool,
)


class MarketplaceWorkflowProvider(BaseProvider):
    async def respond(
        self,
        messages: List[ConversationMessage],
        tools: List[ToolSpec],
    ) -> AssistantResponse:
        if not messages:
            raise ValueError("No messages were provided to the marketplace workflow.")

        last_message = messages[-1]
        if last_message.role == "user":
            return self._start_workflow(last_message.content)
        if last_message.role == "tool":
            return self._continue_workflow(messages)
        return AssistantResponse(content="No workflow action was taken.")

    def _start_workflow(self, payload: str) -> AssistantResponse:
        job = RuntimeJob.model_validate_json(payload)
        if job.kind == "simulate_run":
            return AssistantResponse(
                content="Running anomaly detection.",
                tool_calls=[
                    ToolCall(
                        id=str(uuid.uuid4()),
                        name="detect_anomalies",
                        arguments={"max_alerts": 20},
                    )
                ],
            )

        return AssistantResponse(
            content="Executing block action.",
            tool_calls=[
                ToolCall(
                    id=str(uuid.uuid4()),
                    name="simulate_block_sku",
                    arguments={
                        "alert_id": job.alert_id,
                        "requested_by": job.requested_by,
                    },
                )
            ],
        )

    def _continue_workflow(
        self,
        messages: List[ConversationMessage],
    ) -> AssistantResponse:
        tool_result = ToolResultEnvelope.model_validate_json(messages[-1].content)
        if not tool_result.ok:
            return AssistantResponse(
                content=f"Workflow stopped at '{messages[-1].tool_name}' with error: {tool_result.error}"
            )

        if messages[-1].tool_name == "detect_anomalies":
            anomalies = (tool_result.data or {}).get("anomalies", [])
            if not anomalies:
                return AssistantResponse(content="Detection finished without anomalies.")
            return AssistantResponse(
                content=f"Creating {len(anomalies)} alerts.",
                tool_calls=[
                    ToolCall(
                        id=str(uuid.uuid4()),
                        name="create_alert",
                        arguments=anomaly,
                    )
                    for anomaly in anomalies
                ],
            )

        if messages[-1].tool_name == "create_alert":
            recent_tool_messages = self._recent_tool_messages(messages)
            created_alert_ids = []
            for message in recent_tool_messages:
                if message.tool_name != "create_alert":
                    return AssistantResponse(content="Alert creation finished.")
                result = ToolResultEnvelope.model_validate_json(message.content)
                if result.ok and result.data is not None:
                    created_alert_ids.append(result.data["alert_id"])
            return AssistantResponse(
                content=f"Created or refreshed {len(created_alert_ids)} alerts: {created_alert_ids}"
            )

        if messages[-1].tool_name == "simulate_block_sku":
            data = tool_result.data or {}
            return AssistantResponse(
                content=(
                    f"Listing {data.get('listing_id')} blocked in simulation. "
                    f"Action run {data.get('action_run_id')} completed."
                )
            )

        return AssistantResponse(content="Workflow finished.")

    @staticmethod
    def _recent_tool_messages(messages: List[ConversationMessage]) -> List[ConversationMessage]:
        recent: List[ConversationMessage] = []
        for message in reversed(messages):
            if message.role != "tool":
                break
            recent.append(message)
        recent.reverse()
        return recent


class MarketplaceRuntimeService:
    def __init__(
        self,
        runtime: AgentRuntime,
        session_store: FileSessionStore,
        repository: MarketplaceRepository,
        workspace: Path,
    ) -> None:
        self.runtime = runtime
        self.session_store = session_store
        self.repository = repository
        self.workspace = workspace

    async def run_detection(
        self,
        session_id: str,
        requested_by: str,
    ) -> RuntimeJobResult:
        request = TurnRequest(
            session_id=session_id,
            message=RuntimeJob(
                kind="simulate_run",
                session_id=session_id,
                requested_by=requested_by,
            ).model_dump_json(),
            cwd=str(self.workspace),
            approved_risk_levels={RiskLevel.MEDIUM},
        )
        result = await self.runtime.run(request)
        self.session_store.save_result(result)
        return self._build_runtime_result(result)

    async def execute_block_action(
        self,
        alert_id: int,
        requested_by: str,
        approved: bool,
    ) -> RuntimeJobResult:
        session_id = f"action-{alert_id}-{uuid.uuid4().hex[:8]}"
        request = TurnRequest(
            session_id=session_id,
            message=RuntimeJob(
                kind="execute_block_action",
                session_id=session_id,
                requested_by=requested_by,
                alert_id=alert_id,
            ).model_dump_json(),
            cwd=str(self.workspace),
            approved_tools={"simulate_block_sku"} if approved else set(),
        )
        result = await self.runtime.run(request)
        self.session_store.save_result(result)
        runtime_result = self._build_runtime_result(result)
        if runtime_result.requires_approval:
            pending_run = self.repository.record_approval_required(
                alert_id=alert_id,
                requested_by=requested_by,
            )
            runtime_result.action_run_id = pending_run.id
        return runtime_result

    @staticmethod
    def _build_runtime_result(result: TurnResult) -> RuntimeJobResult:
        alert_ids: List[int] = []
        action_run_id = None
        requires_approval = False
        for message in result.messages:
            if message.role != "tool":
                continue
            envelope = ToolResultEnvelope.model_validate_json(message.content)
            if envelope.ok and envelope.tool_name == "create_alert" and envelope.data:
                alert_ids.append(int(envelope.data["alert_id"]))
            if envelope.ok and envelope.tool_name == "simulate_block_sku" and envelope.data:
                action_run_id = int(envelope.data["action_run_id"])
            if not envelope.ok and envelope.tool_name == "simulate_block_sku":
                requires_approval = "approval" in (envelope.error or "").lower()

        return RuntimeJobResult(
            session_id=result.session_id,
            final_output=result.final_output,
            alerts_created=len(alert_ids),
            alert_ids=alert_ids,
            requires_approval=requires_approval,
            action_run_id=action_run_id,
            events=[event.model_dump(mode="json") for event in result.events],
        )


def build_runtime_components(workspace: Path):
    data_dir = workspace / ".marketplace_guard"
    repository = MarketplaceRepository(data_dir / "marketplace_guard.db")
    repository.init_db()
    repository.seed_mock_data()

    registry = ToolRegistry()
    engine = DetectionEngine()
    registry.register(GetProductsTool(repository))
    registry.register(CalculateMarginTool(repository))
    registry.register(DetectAnomaliesTool(repository, engine))
    registry.register(CreateAlertTool(repository))
    registry.register(SimulateBlockSkuTool(repository))

    policy_engine = PolicyEngine(
        rules=[
            ExplicitToolRule(),
            RiskPolicyRule(auto_allow_until=RiskLevel.LOW),
        ]
    )

    runtime = AgentRuntime(
        provider=MarketplaceWorkflowProvider(),
        registry=registry,
        policy_engine=policy_engine,
    )
    session_store = FileSessionStore(data_dir / "sessions")
    service = MarketplaceRuntimeService(
        runtime=runtime,
        session_store=session_store,
        repository=repository,
        workspace=workspace,
    )
    return repository, runtime, session_store, service
