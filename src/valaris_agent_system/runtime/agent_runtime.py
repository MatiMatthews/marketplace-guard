from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import List, Optional, Type

from pydantic import BaseModel, ValidationError

from ..tools.base import BaseTool
from ..tools.registry import ToolRegistry
from ..policy.engine import PolicyEngine
from .errors import (
    AgentRuntimeError,
    ApprovalRequiredError,
    PolicyDeniedError,
    ProviderError,
    ToolExecutionError,
    ToolValidationError,
)
from .models import (
    ConversationMessage,
    ExecutionContext,
    ExecutionEvent,
    ExecutionEventBase,
    JobOutcomeEvent,
    PolicyAction,
    PolicyContext,
    PolicyDecisionEvent,
    ProviderFailedEvent,
    ProviderRequestedEvent,
    ProviderRespondedEvent,
    ProviderRetryEvent,
    ToolCall,
    ToolCompletedEvent,
    ToolFailedEvent,
    ToolReceivedEvent,
    ToolResultEnvelope,
    ToolRetryEvent,
    TurnCompletedEvent,
    TurnFailedEvent,
    TurnRequest,
    TurnResult,
    TurnStartedEvent,
)
from .providers import BaseProvider


logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionOutcome:
    output: Optional[BaseModel]
    attempt_count: int
    duration_ms: float
    error: Optional[AgentRuntimeError] = None


class AgentRuntime:
    def __init__(
        self,
        provider: BaseProvider,
        registry: ToolRegistry,
        policy_engine: PolicyEngine,
        default_max_turns: int = 8,
        provider_retry_attempts: int = 2,
        provider_retry_backoff: float = 0.5,
    ) -> None:
        self.provider = provider
        self.registry = registry
        self.policy_engine = policy_engine
        self.default_max_turns = default_max_turns
        self.provider_retry_attempts = provider_retry_attempts
        self.provider_retry_backoff = provider_retry_backoff
        self._event_sequence = 0

    async def run(self, request: TurnRequest) -> TurnResult:
        self._event_sequence = 0
        events: List[ExecutionEvent] = []
        messages = list(request.history)
        messages.append(ConversationMessage(role="user", content=request.message))
        max_turns = request.max_turns or self.default_max_turns
        current_turn = 0

        try:
            for turn in range(1, max_turns + 1):
                current_turn = turn
                self._append_event(
                    events,
                    TurnStartedEvent,
                    turn=turn,
                    max_turns=max_turns,
                )

                response = await self._call_provider_with_retry(messages, events, turn)
                if response.content:
                    messages.append(
                        ConversationMessage(role="assistant", content=response.content)
                    )

                if not response.tool_calls:
                    final_output = response.content or ""
                    outcome = (
                        "completed_with_errors"
                        if any(isinstance(event, ToolFailedEvent) for event in events)
                        else "completed"
                    )
                    self._append_event(
                        events,
                        TurnCompletedEvent,
                        turn=turn,
                        final_output_preview=self._preview_text(final_output),
                        message_count=len(messages),
                    )
                    self._append_event(
                        events,
                        JobOutcomeEvent,
                        turn=turn,
                        outcome=outcome,
                        turns_used=turn,
                        final_output_preview=self._preview_text(final_output),
                    )
                    return TurnResult(
                        session_id=request.session_id,
                        final_output=final_output,
                        messages=messages,
                        events=events,
                        turns_used=turn,
                    )

                for tool_call in response.tool_calls:
                    tool_result = await self._handle_tool_call(
                        request=request,
                        tool_call=tool_call,
                        events=events,
                        turn=turn,
                    )
                    messages.append(
                        ConversationMessage(
                            role="tool",
                            content=tool_result.model_dump_json(),
                            tool_call_id=tool_call.id,
                            tool_name=tool_call.name,
                        )
                    )
        except Exception as exc:
            failure_turn = current_turn or 1
            self._append_event(
                events,
                TurnFailedEvent,
                turn=failure_turn,
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )
            self._append_event(
                events,
                JobOutcomeEvent,
                turn=failure_turn,
                outcome="failed",
                turns_used=failure_turn,
                error_type=exc.__class__.__name__,
                error_message=str(exc),
            )
            raise

        failure = AgentRuntimeError("Maximum turn count exceeded.")
        self._append_event(
            events,
            TurnFailedEvent,
            turn=max_turns,
            error_type=failure.__class__.__name__,
            error_message=str(failure),
        )
        self._append_event(
            events,
            JobOutcomeEvent,
            turn=max_turns,
            outcome="failed",
            turns_used=max_turns,
            error_type=failure.__class__.__name__,
            error_message=str(failure),
        )
        raise failure

    async def _call_provider_with_retry(
        self,
        messages: List[ConversationMessage],
        events: List[ExecutionEvent],
        turn: int,
    ):
        last_error = None
        for attempt in range(1, self.provider_retry_attempts + 1):
            self._append_event(
                events,
                ProviderRequestedEvent,
                turn=turn,
                attempt=attempt,
                message_count=len(messages),
            )
            started_at = time.perf_counter()
            try:
                response = await self.provider.respond(messages, self.registry.tool_specs())
                self._append_event(
                    events,
                    ProviderRespondedEvent,
                    turn=turn,
                    attempt=attempt,
                    duration_ms=self._duration_ms(started_at),
                    tool_call_count=len(response.tool_calls),
                    content_present=bool(response.content),
                )
                return response
            except ProviderError as exc:
                last_error = exc
                logger.warning(
                    "provider_attempt_failed",
                    extra={"attempt": attempt, "transient": exc.transient},
                )
                duration_ms = self._duration_ms(started_at)
                if not exc.transient or attempt == self.provider_retry_attempts:
                    self._append_event(
                        events,
                        ProviderFailedEvent,
                        turn=turn,
                        attempt=attempt,
                        max_attempts=self.provider_retry_attempts,
                        duration_ms=duration_ms,
                        error_type=exc.__class__.__name__,
                        error_message=str(exc),
                        retryable=exc.transient,
                    )
                    raise

                backoff_seconds = self.provider_retry_backoff * attempt
                self._append_event(
                    events,
                    ProviderRetryEvent,
                    turn=turn,
                    attempt=attempt,
                    max_attempts=self.provider_retry_attempts,
                    duration_ms=duration_ms,
                    error_type=exc.__class__.__name__,
                    error_message=str(exc),
                    backoff_seconds=backoff_seconds,
                )
                await asyncio.sleep(backoff_seconds)

        raise last_error or ProviderError("Provider failed without an explicit error.")

    async def _handle_tool_call(
        self,
        request: TurnRequest,
        tool_call: ToolCall,
        events: List[ExecutionEvent],
        turn: int,
    ) -> ToolResultEnvelope:
        self._append_event(
            events,
            ToolReceivedEvent,
            turn=turn,
            tool_name=tool_call.name,
            tool_call_id=tool_call.id,
        )

        if not self.registry.has(tool_call.name):
            return self._error_result(
                tool_call=tool_call,
                error=f"Unknown tool '{tool_call.name}'.",
                events=events,
                turn=turn,
            )

        tool = self.registry.get(tool_call.name)

        try:
            payload = tool.input_model.model_validate(tool_call.arguments)
        except ValidationError as exc:
            return self._error_result(
                tool_call=tool_call,
                error=f"Input validation failed: {exc}",
                events=events,
                turn=turn,
                exception=ToolValidationError(str(exc)),
            )

        policy_context = PolicyContext(
            session_id=request.session_id,
            user_id=request.user_id,
            cwd=request.cwd,
            is_background=request.is_background,
            approved_tools=request.approved_tools,
            approved_risk_levels=request.approved_risk_levels,
        )
        decision = await self.policy_engine.authorize(tool.spec, payload, policy_context)
        self._append_event(
            events,
            PolicyDecisionEvent,
            turn=turn,
            tool_name=tool_call.name,
            tool_call_id=tool_call.id,
            action=decision.action,
            risk_level=tool.spec.risk_level,
            reason=decision.reason,
        )

        if decision.action == PolicyAction.DENY:
            return self._error_result(
                tool_call=tool_call,
                error=decision.reason or "Tool denied by policy.",
                events=events,
                turn=turn,
                exception=PolicyDeniedError(decision.reason or "Tool denied."),
            )
        if decision.action == PolicyAction.REQUIRE_APPROVAL:
            return self._error_result(
                tool_call=tool_call,
                error=decision.reason or "Tool requires approval.",
                events=events,
                turn=turn,
                exception=ApprovalRequiredError(decision.reason or "Approval required."),
            )

        execution_context = ExecutionContext(
            session_id=request.session_id,
            cwd=request.cwd,
            trace_id=str(uuid.uuid4()),
        )

        outcome = await self._execute_tool_with_retry(
            tool=tool,
            payload=payload,
            context=execution_context,
            events=events,
            turn=turn,
            tool_call=tool_call,
        )
        if outcome.error is not None:
            return self._error_result(
                tool_call=tool_call,
                error=str(outcome.error),
                events=events,
                turn=turn,
                exception=outcome.error,
                attempt_count=outcome.attempt_count,
                duration_ms=outcome.duration_ms,
            )

        try:
            validated_output = tool.output_model.model_validate(outcome.output)
        except ValidationError as exc:
            return self._error_result(
                tool_call=tool_call,
                error=str(exc),
                events=events,
                turn=turn,
                exception=ToolValidationError(str(exc)),
                attempt_count=outcome.attempt_count,
                duration_ms=outcome.duration_ms,
            )

        envelope = ToolResultEnvelope(
            ok=True,
            tool_name=tool_call.name,
            tool_call_id=tool_call.id,
            data=validated_output.model_dump(),
        )
        self._append_event(
            events,
            ToolCompletedEvent,
            turn=turn,
            tool_name=tool_call.name,
            tool_call_id=tool_call.id,
            attempt_count=outcome.attempt_count,
            duration_ms=outcome.duration_ms,
            output_keys=sorted(validated_output.model_dump().keys()),
        )
        return envelope

    async def _execute_tool_with_retry(
        self,
        tool: BaseTool,
        payload: BaseModel,
        context: ExecutionContext,
        events: List[ExecutionEvent],
        turn: int,
        tool_call: ToolCall,
    ) -> ToolExecutionOutcome:
        last_error = None
        policy = tool.spec.retry_policy
        started_at = time.perf_counter()

        for attempt in range(1, policy.max_attempts + 1):
            should_retry = False
            try:
                output = await asyncio.wait_for(
                    tool.execute(payload, context),
                    timeout=tool.spec.timeout_seconds,
                )
                return ToolExecutionOutcome(
                    output=output,
                    attempt_count=attempt,
                    duration_ms=self._duration_ms(started_at),
                )
            except asyncio.TimeoutError as exc:
                last_error = ToolExecutionError(
                    f"Tool '{tool.spec.name}' timed out after {tool.spec.timeout_seconds:.2f}s.",
                    retryable=True,
                )
                should_retry = policy.retry_on_timeout and attempt < policy.max_attempts
            except ToolExecutionError as exc:
                last_error = exc
                should_retry = (
                    exc.retryable
                    and policy.retry_on_transient
                    and attempt < policy.max_attempts
                )
            except ValidationError as exc:
                last_error = ToolValidationError(str(exc))

            if not should_retry:
                return ToolExecutionOutcome(
                    output=None,
                    attempt_count=attempt,
                    duration_ms=self._duration_ms(started_at),
                    error=last_error,
                )

            backoff_seconds = policy.backoff_seconds * attempt
            self._append_event(
                events,
                ToolRetryEvent,
                turn=turn,
                tool_name=tool.spec.name,
                tool_call_id=tool_call.id,
                attempt=attempt,
                max_attempts=policy.max_attempts,
                duration_ms=self._duration_ms(started_at),
                error_type=last_error.__class__.__name__,
                error_message=str(last_error),
                retryable=bool(getattr(last_error, "retryable", False)),
                backoff_seconds=backoff_seconds,
            )
            await asyncio.sleep(backoff_seconds)

        return ToolExecutionOutcome(
            output=None,
            attempt_count=policy.max_attempts,
            duration_ms=self._duration_ms(started_at),
            error=last_error or ToolExecutionError(
                f"Tool '{tool.spec.name}' failed without an explicit error."
            ),
        )

    def _append_event(
        self,
        events: List[ExecutionEvent],
        event_class: Type[ExecutionEventBase],
        **kwargs,
    ) -> None:
        self._event_sequence += 1
        events.append(event_class(sequence=self._event_sequence, **kwargs))

    def _error_result(
        self,
        tool_call: ToolCall,
        error: str,
        events: List[ExecutionEvent],
        turn: int,
        exception: Optional[AgentRuntimeError] = None,
        attempt_count: int = 1,
        duration_ms: float = 0.0,
    ) -> ToolResultEnvelope:
        if exception:
            logger.warning(
                "tool_failed",
                extra={
                    "tool_name": tool_call.name,
                    "tool_call_id": tool_call.id,
                    "error_type": exception.__class__.__name__,
                },
            )

        envelope = ToolResultEnvelope(
            ok=False,
            tool_name=tool_call.name,
            tool_call_id=tool_call.id,
            error=error,
        )
        self._append_event(
            events,
            ToolFailedEvent,
            turn=turn,
            tool_name=tool_call.name,
            tool_call_id=tool_call.id,
            attempt_count=attempt_count,
            duration_ms=duration_ms,
            error_type=exception.__class__.__name__ if exception else "ToolError",
            error_message=error,
            retryable=bool(getattr(exception, "retryable", False)),
        )
        return envelope

    @staticmethod
    def _duration_ms(started_at: float) -> float:
        return round((time.perf_counter() - started_at) * 1000, 3)

    @staticmethod
    def _preview_text(text: str, limit: int = 240) -> str:
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."
