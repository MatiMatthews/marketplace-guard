from .errors import (
    AgentRuntimeError,
    ApprovalRequiredError,
    PolicyDeniedError,
    ProviderError,
    ToolExecutionError,
    ToolValidationError,
)
from .models import (
    AssistantResponse,
    ConversationMessage,
    ExecutionContext,
    ExecutionEvent,
    JobOutcomeEvent,
    PolicyAction,
    PolicyContext,
    PolicyDecision,
    RetryPolicy,
    RiskLevel,
    RuntimeEvent,
    ToolCall,
    ToolResultEnvelope,
    ToolSpec,
    TurnRequest,
    TurnResult,
)
from .providers import BaseProvider, RuleBasedProvider

__all__ = [
    "AgentRuntime",
    "AgentRuntimeError",
    "ApprovalRequiredError",
    "AssistantResponse",
    "BaseProvider",
    "ConversationMessage",
    "create_app",
    "ExecutionContext",
    "ExecutionEvent",
    "JobOutcomeEvent",
    "PolicyAction",
    "PolicyContext",
    "PolicyDecision",
    "PolicyDeniedError",
    "ProviderError",
    "RetryPolicy",
    "RiskLevel",
    "RuleBasedProvider",
    "RuntimeEvent",
    "ToolCall",
    "ToolExecutionError",
    "ToolResultEnvelope",
    "ToolSpec",
    "ToolValidationError",
    "TurnRequest",
    "TurnResult",
]


def __getattr__(name: str):
    if name == "AgentRuntime":
        from .agent_runtime import AgentRuntime

        return AgentRuntime
    if name == "create_app":
        from .app import create_app

        return create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
