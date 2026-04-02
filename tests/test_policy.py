from __future__ import annotations

import unittest

from valaris_agent_system import (
    ExplicitToolRule,
    PolicyAction,
    PolicyContext,
    PolicyEngine,
    RiskLevel,
    RiskPolicyRule,
    ToolSpec,
)


class PolicyEngineTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.context = PolicyContext(session_id="policy-session")
        self.low_risk_tool = ToolSpec(
            name="echo_text",
            description="Echo text",
            risk_level=RiskLevel.LOW,
        )
        self.medium_risk_tool = ToolSpec(
            name="write_note",
            description="Write note",
            risk_level=RiskLevel.MEDIUM,
        )

    async def test_allow(self) -> None:
        engine = PolicyEngine([RiskPolicyRule(auto_allow_until=RiskLevel.LOW)])

        decision = await engine.authorize(self.low_risk_tool, payload={}, context=self.context)

        self.assertEqual(decision.action, PolicyAction.ALLOW)

    async def test_deny(self) -> None:
        engine = PolicyEngine([ExplicitToolRule(denied_tools={"write_note"}), RiskPolicyRule()])

        decision = await engine.authorize(self.medium_risk_tool, payload={}, context=self.context)

        self.assertEqual(decision.action, PolicyAction.DENY)

    async def test_require_approval(self) -> None:
        engine = PolicyEngine([RiskPolicyRule(auto_allow_until=RiskLevel.LOW)])

        decision = await engine.authorize(self.medium_risk_tool, payload={}, context=self.context)

        self.assertEqual(decision.action, PolicyAction.REQUIRE_APPROVAL)
