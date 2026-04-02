from __future__ import annotations

import re
import uuid
from abc import ABC, abstractmethod
from typing import List

from .errors import ProviderError
from .models import AssistantResponse, ConversationMessage, ToolCall, ToolSpec


class BaseProvider(ABC):
    """Provider interface for the runtime."""

    @abstractmethod
    async def respond(
        self,
        messages: List[ConversationMessage],
        tools: List[ToolSpec],
    ) -> AssistantResponse:
        raise NotImplementedError


class RuleBasedProvider(BaseProvider):
    """
    Simple in-process provider for local execution and demos.

    Supported commands:
    - "sum 3 4"
    - "echo hello world"
    - "write-note notes/demo.txt :: hello"
    """

    async def respond(
        self,
        messages: List[ConversationMessage],
        tools: List[ToolSpec],
    ) -> AssistantResponse:
        if not messages:
            raise ProviderError("No messages were provided to the provider.")

        last_message = messages[-1]
        if last_message.role == "user":
            return self._plan_from_user_message(last_message.content)
        if last_message.role == "tool":
            return self._summarize_tool_results(messages)

        return AssistantResponse(content="No action was taken.")

    def _plan_from_user_message(self, content: str) -> AssistantResponse:
        calls = []
        normalized = content.strip()

        sum_match = re.search(r"sum\s+(-?\d+)\s+(-?\d+)", normalized, re.IGNORECASE)
        if sum_match:
            calls.append(
                ToolCall(
                    id=str(uuid.uuid4()),
                    name="sum_numbers",
                    arguments={
                        "left": int(sum_match.group(1)),
                        "right": int(sum_match.group(2)),
                    },
                )
            )

        echo_match = re.search(r"echo\s+(.+)", normalized, re.IGNORECASE)
        if echo_match:
            calls.append(
                ToolCall(
                    id=str(uuid.uuid4()),
                    name="echo_text",
                    arguments={"text": echo_match.group(1).strip()},
                )
            )

        write_match = re.search(
            r"write-note\s+(\S+)\s+::\s*(.+)",
            normalized,
            re.IGNORECASE,
        )
        if write_match:
            calls.append(
                ToolCall(
                    id=str(uuid.uuid4()),
                    name="write_note",
                    arguments={
                        "path": write_match.group(1).strip(),
                        "content": write_match.group(2).strip(),
                    },
                )
            )

        if calls:
            return AssistantResponse(
                content="Planned tool execution.",
                tool_calls=calls,
            )

        return AssistantResponse(
            content=(
                "No supported tool request was detected. "
                "Use one of: 'sum 3 4', 'echo hello', "
                "or 'write-note notes/demo.txt :: some text'."
            )
        )

    def _summarize_tool_results(
        self,
        messages: List[ConversationMessage],
    ) -> AssistantResponse:
        tool_messages = []
        for message in reversed(messages):
            if message.role == "tool":
                tool_messages.append(message)
                continue
            break

        tool_messages.reverse()
        if not tool_messages:
            return AssistantResponse(content="Tool execution finished.")

        lines = []
        for message in tool_messages:
            prefix = message.tool_name or "tool"
            lines.append(f"- {prefix}: {message.content}")

        return AssistantResponse(content="Execution summary:\n" + "\n".join(lines))
