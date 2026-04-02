from __future__ import annotations

import unittest
from typing import List

from valaris_agent_system import (
    AgentRuntime,
    AgentRuntimeError,
    AssistantResponse,
    BaseProvider,
    ConversationMessage,
    ExplicitToolRule,
    PolicyEngine,
    RiskPolicyRule,
    ToolCall,
    ToolSpec,
    ToolRegistry,
    TurnRequest,
)
from valaris_agent_system.tools import SumNumbersTool


class FinalOnlyProvider(BaseProvider):
    async def respond(
        self,
        messages: List[ConversationMessage],
        tools: List[ToolSpec],
    ) -> AssistantResponse:
        return AssistantResponse(content="done")


class SumThenFinishProvider(BaseProvider):
    async def respond(
        self,
        messages: List[ConversationMessage],
        tools: List[ToolSpec],
    ) -> AssistantResponse:
        last_message = messages[-1]
        if last_message.role == "user":
            return AssistantResponse(
                content="running sum",
                tool_calls=[
                    ToolCall(
                        id="sum-call-1",
                        name="sum_numbers",
                        arguments={"left": 2, "right": 3},
                    )
                ],
            )
        return AssistantResponse(content="completed")


class LoopingProvider(BaseProvider):
    async def respond(
        self,
        messages: List[ConversationMessage],
        tools: List[ToolSpec],
    ) -> AssistantResponse:
        return AssistantResponse(
            content="keep going",
            tool_calls=[
                ToolCall(
                    id=f"sum-call-{len(messages)}",
                    name="sum_numbers",
                    arguments={"left": 1, "right": 1},
                )
            ],
        )


class AgentRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def build_runtime(self, provider: BaseProvider) -> AgentRuntime:
        registry = ToolRegistry()
        registry.register(SumNumbersTool())
        policy = PolicyEngine([ExplicitToolRule(), RiskPolicyRule()])
        return AgentRuntime(provider=provider, registry=registry, policy_engine=policy)

    async def test_execution_simple_without_tools(self) -> None:
        runtime = self.build_runtime(FinalOnlyProvider())

        result = await runtime.run(TurnRequest(session_id="runtime-no-tools", message="hello"))

        self.assertEqual(result.final_output, "done")
        self.assertEqual(result.turns_used, 1)
        self.assertEqual(result.messages[-1].role, "assistant")

    async def test_execution_with_tool(self) -> None:
        runtime = self.build_runtime(SumThenFinishProvider())

        result = await runtime.run(TurnRequest(session_id="runtime-with-tool", message="sum please"))

        self.assertEqual(result.final_output, "completed")
        self.assertTrue(any(message.role == "tool" for message in result.messages))
        self.assertTrue(any(event.event_name == "tool.completed" for event in result.events))

    async def test_error_for_max_turns(self) -> None:
        runtime = self.build_runtime(LoopingProvider())

        with self.assertRaises(AgentRuntimeError):
            await runtime.run(
                TurnRequest(
                    session_id="runtime-max-turns",
                    message="loop",
                    max_turns=2,
                )
            )
