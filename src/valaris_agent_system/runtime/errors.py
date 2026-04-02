class AgentRuntimeError(Exception):
    """Base error for runtime failures."""


class ProviderError(AgentRuntimeError):
    """Error produced by the model provider."""

    def __init__(self, message: str, transient: bool = False) -> None:
        super().__init__(message)
        self.transient = transient


class ToolValidationError(AgentRuntimeError):
    """Tool input or output did not match the declared schema."""


class ToolExecutionError(AgentRuntimeError):
    """Tool execution failed."""

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class PolicyDeniedError(AgentRuntimeError):
    """Policy engine denied the tool call."""


class ApprovalRequiredError(AgentRuntimeError):
    """Tool call requires approval before execution."""
