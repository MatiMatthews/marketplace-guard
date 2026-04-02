from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional, Set

from ..runtime.models import (
    PolicyAction,
    PolicyContext,
    PolicyDecision,
    RiskLevel,
    ToolSpec,
)


RISK_ORDER = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


class PolicyRule(ABC):
    @abstractmethod
    async def evaluate(
        self,
        tool_spec: ToolSpec,
        payload: object,
        context: PolicyContext,
    ) -> Optional[PolicyDecision]:
        raise NotImplementedError


class ExplicitToolRule(PolicyRule):
    def __init__(
        self,
        allowed_tools: Optional[Iterable[str]] = None,
        denied_tools: Optional[Iterable[str]] = None,
    ) -> None:
        self.allowed_tools: Set[str] = set(allowed_tools or [])
        self.denied_tools: Set[str] = set(denied_tools or [])

    async def evaluate(
        self,
        tool_spec: ToolSpec,
        payload: object,
        context: PolicyContext,
    ) -> Optional[PolicyDecision]:
        if tool_spec.name in self.denied_tools:
            return PolicyDecision(
                action=PolicyAction.DENY,
                reason="Tool denied by explicit policy rule.",
            )
        if self.allowed_tools and tool_spec.name in self.allowed_tools:
            return PolicyDecision(action=PolicyAction.ALLOW)
        return None


class RiskPolicyRule(PolicyRule):
    def __init__(
        self,
        auto_allow_until: RiskLevel = RiskLevel.LOW,
        deny_background_from: RiskLevel = RiskLevel.HIGH,
    ) -> None:
        self.auto_allow_until = auto_allow_until
        self.deny_background_from = deny_background_from

    async def evaluate(
        self,
        tool_spec: ToolSpec,
        payload: object,
        context: PolicyContext,
    ) -> Optional[PolicyDecision]:
        if context.is_background and self._gte(
            tool_spec.risk_level,
            self.deny_background_from,
        ):
            return PolicyDecision(
                action=PolicyAction.DENY,
                reason="Risk level not allowed in background execution.",
            )

        if tool_spec.name in context.approved_tools:
            return PolicyDecision(action=PolicyAction.ALLOW)

        if tool_spec.risk_level in context.approved_risk_levels:
            return PolicyDecision(action=PolicyAction.ALLOW)

        if self._lte(tool_spec.risk_level, self.auto_allow_until):
            return PolicyDecision(action=PolicyAction.ALLOW)

        return PolicyDecision(
            action=PolicyAction.REQUIRE_APPROVAL,
            reason=f"Tool risk level '{tool_spec.risk_level.value}' requires approval.",
        )

    @staticmethod
    def _lte(left: RiskLevel, right: RiskLevel) -> bool:
        return RISK_ORDER[left] <= RISK_ORDER[right]

    @staticmethod
    def _gte(left: RiskLevel, right: RiskLevel) -> bool:
        return RISK_ORDER[left] >= RISK_ORDER[right]


class PolicyEngine:
    def __init__(self, rules: Iterable[PolicyRule]) -> None:
        self.rules = list(rules)

    async def authorize(
        self,
        tool_spec: ToolSpec,
        payload: object,
        context: PolicyContext,
    ) -> PolicyDecision:
        for rule in self.rules:
            decision = await rule.evaluate(tool_spec, payload, context)
            if decision is not None:
                return decision
        return PolicyDecision(action=PolicyAction.ALLOW)
