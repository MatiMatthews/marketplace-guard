from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Set, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class RetryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_attempts: int = 1
    backoff_seconds: float = 0.25
    retry_on_timeout: bool = True
    retry_on_transient: bool = True


class ToolSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    risk_level: RiskLevel
    timeout_seconds: float = 30.0
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)


class ExecutionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    trace_id: str
    cwd: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PolicyContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    user_id: Optional[str] = None
    cwd: Optional[str] = None
    is_background: bool = False
    approved_tools: Set[str] = Field(default_factory=set)
    approved_risk_levels: Set[RiskLevel] = Field(default_factory=set)


class PolicyDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: PolicyAction
    reason: Optional[str] = None


class ConversationMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    content: str
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class AssistantResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_payload(self) -> "AssistantResponse":
        if not self.content and not self.tool_calls:
            raise ValueError("AssistantResponse must contain content or tool calls.")
        return self


class ToolResultEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    tool_name: str
    tool_call_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionEventBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int
    event_name: str
    recorded_at: datetime = Field(default_factory=utc_now)
    turn: int


class TurnStartedEvent(ExecutionEventBase):
    event_name: Literal["turn.started"] = "turn.started"
    max_turns: int


class ProviderRequestedEvent(ExecutionEventBase):
    event_name: Literal["provider.requested"] = "provider.requested"
    attempt: int
    message_count: int


class ProviderRetryEvent(ExecutionEventBase):
    event_name: Literal["provider.retry"] = "provider.retry"
    attempt: int
    max_attempts: int
    duration_ms: float
    error_type: str
    error_message: str
    backoff_seconds: float


class ProviderFailedEvent(ExecutionEventBase):
    event_name: Literal["provider.failed"] = "provider.failed"
    attempt: int
    max_attempts: int
    duration_ms: float
    error_type: str
    error_message: str
    retryable: bool = False


class ProviderRespondedEvent(ExecutionEventBase):
    event_name: Literal["provider.responded"] = "provider.responded"
    attempt: int
    duration_ms: float
    tool_call_count: int
    content_present: bool


class ToolReceivedEvent(ExecutionEventBase):
    event_name: Literal["tool.received"] = "tool.received"
    tool_name: str
    tool_call_id: str


class PolicyDecisionEvent(ExecutionEventBase):
    event_name: Literal["policy.decided"] = "policy.decided"
    tool_name: str
    tool_call_id: str
    action: PolicyAction
    risk_level: RiskLevel
    reason: Optional[str] = None


class ToolRetryEvent(ExecutionEventBase):
    event_name: Literal["tool.retry"] = "tool.retry"
    tool_name: str
    tool_call_id: str
    attempt: int
    max_attempts: int
    duration_ms: float
    error_type: str
    error_message: str
    retryable: bool = False
    backoff_seconds: float


class ToolCompletedEvent(ExecutionEventBase):
    event_name: Literal["tool.completed"] = "tool.completed"
    tool_name: str
    tool_call_id: str
    attempt_count: int
    duration_ms: float
    output_keys: List[str] = Field(default_factory=list)


class ToolFailedEvent(ExecutionEventBase):
    event_name: Literal["tool.failed"] = "tool.failed"
    tool_name: str
    tool_call_id: str
    attempt_count: int
    duration_ms: float
    error_type: str
    error_message: str
    retryable: bool = False


class TurnCompletedEvent(ExecutionEventBase):
    event_name: Literal["turn.completed"] = "turn.completed"
    final_output_preview: str
    message_count: int


class TurnFailedEvent(ExecutionEventBase):
    event_name: Literal["turn.failed"] = "turn.failed"
    error_type: str
    error_message: str


class JobOutcomeEvent(ExecutionEventBase):
    event_name: Literal["job.outcome"] = "job.outcome"
    outcome: Literal["completed", "completed_with_errors", "failed"]
    turns_used: int
    final_output_preview: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None


ExecutionEvent = Annotated[
    Union[
        TurnStartedEvent,
        ProviderRequestedEvent,
        ProviderRetryEvent,
        ProviderFailedEvent,
        ProviderRespondedEvent,
        ToolReceivedEvent,
        PolicyDecisionEvent,
        ToolRetryEvent,
        ToolCompletedEvent,
        ToolFailedEvent,
        TurnCompletedEvent,
        TurnFailedEvent,
        JobOutcomeEvent,
    ],
    Field(discriminator="event_name"),
]


RuntimeEvent = ExecutionEvent


class TurnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    message: str
    history: List[ConversationMessage] = Field(default_factory=list)
    user_id: Optional[str] = None
    cwd: Optional[str] = None
    max_turns: int = 8
    approved_tools: Set[str] = Field(default_factory=set)
    approved_risk_levels: Set[RiskLevel] = Field(default_factory=set)
    is_background: bool = False


class TurnResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    final_output: str
    messages: List[ConversationMessage]
    events: List[ExecutionEvent]
    turns_used: int
