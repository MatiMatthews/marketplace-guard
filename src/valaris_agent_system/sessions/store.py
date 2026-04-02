from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..runtime.models import (
    ConversationMessage,
    ExecutionEvent,
    JobOutcomeEvent,
    PolicyAction,
    PolicyDecisionEvent,
    ProviderRespondedEvent,
    RiskLevel,
    ToolCompletedEvent,
    ToolFailedEvent,
    ToolReceivedEvent,
    TurnCompletedEvent,
    TurnResult,
    TurnStartedEvent,
)


ModelT = TypeVar("ModelT", bound=BaseModel)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobResultSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    final_output: str
    turns_used: int
    message_count: int
    event_count: int
    status: str = "completed"

    @classmethod
    def from_turn_result(cls, result: TurnResult) -> "JobResultSummary":
        status = "completed"
        for event in reversed(result.events):
            if isinstance(event, JobOutcomeEvent):
                status = event.outcome
                break
        return cls(
            final_output=result.final_output,
            turns_used=result.turns_used,
            message_count=len(result.messages),
            event_count=len(result.events),
            status=status,
        )


class Checkpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str
    session_id: str
    created_at: datetime = Field(default_factory=utc_now)
    messages: List[ConversationMessage] = Field(default_factory=list)
    events: List[ExecutionEvent] = Field(default_factory=list)
    result: JobResultSummary


class SessionState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    session_id: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_checkpoint: Optional[str] = None
    messages: List[ConversationMessage] = Field(default_factory=list)
    events: List[ExecutionEvent] = Field(default_factory=list)
    result: Optional[JobResultSummary] = None

    @classmethod
    def from_turn_result(
        cls,
        result: TurnResult,
        previous: Optional["SessionState"] = None,
    ) -> "SessionState":
        return cls(
            session_id=result.session_id,
            created_at=previous.created_at if previous else utc_now(),
            updated_at=utc_now(),
            last_checkpoint=previous.last_checkpoint if previous else None,
            messages=result.messages,
            events=result.events,
            result=JobResultSummary.from_turn_result(result),
        )


class FileSessionStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def load_history(self, session_id: str) -> List[ConversationMessage]:
        session = self.load_session(session_id)
        if session is None:
            return []
        return session.messages

    def load_session(self, session_id: str) -> Optional[SessionState]:
        path = self._session_path(session_id)
        if not path.exists():
            return None
        return self._read_model(path, SessionState)

    def save_session(self, session: SessionState) -> None:
        self._write_model(self._session_path(session.session_id), session)

    def load_checkpoint(self, session_id: str, checkpoint_id: str) -> Checkpoint:
        return self._read_model(self._checkpoint_path(session_id, checkpoint_id), Checkpoint)

    def save_checkpoint(self, checkpoint: Checkpoint) -> None:
        self._write_model(
            self._checkpoint_path(checkpoint.session_id, checkpoint.checkpoint_id),
            checkpoint,
        )

    def list_checkpoints(self, session_id: str) -> List[Checkpoint]:
        checkpoints_dir = self._checkpoints_dir(session_id)
        if not checkpoints_dir.exists():
            return []

        checkpoints = []
        for path in sorted(checkpoints_dir.glob("*.json")):
            checkpoints.append(self._read_model(path, Checkpoint))
        return checkpoints

    def save_result(self, result: TurnResult) -> SessionState:
        previous = self.load_session(result.session_id)
        session = SessionState.from_turn_result(result, previous=previous)
        prior_events = previous.events if previous else []
        session.events = prior_events + self._renumber_events(
            result.events,
            starting_sequence=len(prior_events),
        )

        checkpoint = Checkpoint(
            checkpoint_id=self._checkpoint_id(result.turns_used),
            session_id=result.session_id,
            messages=result.messages,
            events=session.events,
            result=JobResultSummary.from_turn_result(result),
        )
        session.last_checkpoint = checkpoint.checkpoint_id

        self.save_session(session)
        self.save_checkpoint(checkpoint)
        return session

    def _session_path(self, session_id: str) -> Path:
        return self.root / session_id / "session.json"

    def _checkpoint_path(self, session_id: str, checkpoint_id: str) -> Path:
        return self.root / session_id / "checkpoints" / f"{checkpoint_id}.json"

    def _checkpoints_dir(self, session_id: str) -> Path:
        return self.root / session_id / "checkpoints"

    @staticmethod
    def _checkpoint_id(turns_used: int) -> str:
        return f"cp-{turns_used:06d}"

    @staticmethod
    def _read_model(path: Path, model_class: Type[ModelT]) -> ModelT:
        raw_text = path.read_text(encoding="utf-8")
        try:
            return model_class.model_validate_json(raw_text)
        except ValidationError:
            if model_class not in (SessionState, Checkpoint):
                raise
            raw_payload = json.loads(raw_text)
            migrated_payload = FileSessionStore._migrate_legacy_payload(raw_payload)
            return model_class.model_validate(migrated_payload)

    @staticmethod
    def _write_model(path: Path, model: BaseModel) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        tmp_path.replace(path)

    @staticmethod
    def _renumber_events(
        events: List[ExecutionEvent],
        starting_sequence: int,
    ) -> List[ExecutionEvent]:
        renumbered = []
        for offset, event in enumerate(events, start=1):
            renumbered.append(event.model_copy(update={"sequence": starting_sequence + offset}))
        return renumbered

    @staticmethod
    def _migrate_legacy_payload(payload: dict) -> dict:
        migrated = dict(payload)
        raw_events = migrated.get("events", [])
        migrated["events"] = [
            FileSessionStore._migrate_legacy_event(raw_event)
            if isinstance(raw_event, dict) and "event_name" not in raw_event and "type" in raw_event
            else raw_event
            for raw_event in raw_events
        ]
        return migrated

    @staticmethod
    def _migrate_legacy_event(raw_event: dict) -> ExecutionEvent:
        event_type = raw_event.get("type", "turn.completed")
        payload = raw_event.get("payload", {})
        sequence = raw_event.get("sequence", 0)
        recorded_at = raw_event.get("recorded_at", utc_now())
        turn = payload.get("turn", 1)

        if event_type == "turn.started":
            return TurnStartedEvent(
                sequence=sequence,
                recorded_at=recorded_at,
                turn=turn,
                max_turns=payload.get("max_turns", turn),
            )
        if event_type == "provider.responded":
            return ProviderRespondedEvent(
                sequence=sequence,
                recorded_at=recorded_at,
                turn=turn,
                attempt=payload.get("attempt", 1),
                duration_ms=payload.get("duration_ms", 0.0),
                tool_call_count=payload.get("tool_call_count", 0),
                content_present=bool(payload.get("content")),
            )
        if event_type == "tool.received":
            return ToolReceivedEvent(
                sequence=sequence,
                recorded_at=recorded_at,
                turn=turn,
                tool_name=payload.get("tool_name", "unknown_tool"),
                tool_call_id=payload.get("tool_call_id", "unknown_call"),
            )
        if event_type == "policy.decided":
            action = payload.get("action", PolicyAction.ALLOW.value)
            risk_value = payload.get("risk_level", RiskLevel.LOW.value)
            return PolicyDecisionEvent(
                sequence=sequence,
                recorded_at=recorded_at,
                turn=turn,
                tool_name=payload.get("tool_name", "unknown_tool"),
                tool_call_id=payload.get("tool_call_id", "unknown_call"),
                action=PolicyAction(action),
                risk_level=RiskLevel(risk_value),
                reason=payload.get("reason"),
            )
        if event_type == "tool.completed":
            data = payload.get("data", {})
            return ToolCompletedEvent(
                sequence=sequence,
                recorded_at=recorded_at,
                turn=turn,
                tool_name=payload.get("tool_name", "unknown_tool"),
                tool_call_id=payload.get("tool_call_id", "unknown_call"),
                attempt_count=payload.get("attempt_count", 1),
                duration_ms=payload.get("duration_ms", 0.0),
                output_keys=sorted(data.keys()) if isinstance(data, dict) else [],
            )
        if event_type == "tool.failed":
            return ToolFailedEvent(
                sequence=sequence,
                recorded_at=recorded_at,
                turn=turn,
                tool_name=payload.get("tool_name", "unknown_tool"),
                tool_call_id=payload.get("tool_call_id", "unknown_call"),
                attempt_count=payload.get("attempt_count", 1),
                duration_ms=payload.get("duration_ms", 0.0),
                error_type=payload.get("error_type", "ToolError"),
                error_message=payload.get("error", "Unknown tool failure."),
                retryable=payload.get("retryable", False),
            )
        return TurnCompletedEvent(
            sequence=sequence,
            recorded_at=recorded_at,
            turn=turn,
            final_output_preview=payload.get("final_output", ""),
            message_count=payload.get("message_count", 0),
        )
