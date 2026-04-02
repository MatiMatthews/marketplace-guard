from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Type

from pydantic import BaseModel

from ..runtime.models import ExecutionContext, ToolSpec


class BaseTool(ABC):
    spec: ToolSpec
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]

    @abstractmethod
    async def execute(
        self,
        payload: BaseModel,
        context: ExecutionContext,
    ) -> BaseModel:
        raise NotImplementedError


__all__ = ["BaseTool"]
