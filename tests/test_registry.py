from __future__ import annotations

import unittest

from valaris_agent_system.tools import SumNumbersTool, ToolRegistry


class ToolRegistryTests(unittest.TestCase):
    def test_register(self) -> None:
        registry = ToolRegistry()
        tool = SumNumbersTool()

        registry.register(tool)

        self.assertTrue(registry.has(tool.spec.name))
        self.assertIs(registry.get(tool.spec.name), tool)

    def test_duplicate_registration(self) -> None:
        registry = ToolRegistry()
        registry.register(SumNumbersTool())

        with self.assertRaises(ValueError):
            registry.register(SumNumbersTool())

    def test_lookup(self) -> None:
        registry = ToolRegistry()

        with self.assertRaises(KeyError):
            registry.get("missing_tool")
