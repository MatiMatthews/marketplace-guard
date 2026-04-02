from __future__ import annotations

from typing import Dict, List

from ..runtime.models import ToolSpec
from .base import BaseTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        name = tool.spec.name
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered.")
        self._tools[name] = tool

    def get(self, name: str) -> BaseTool:
        return self._tools[name]

    def has(self, name: str) -> bool:
        return name in self._tools

    def tool_specs(self) -> List[ToolSpec]:
        return [tool.spec for tool in self._tools.values()]


__all__ = ["ToolRegistry"]
