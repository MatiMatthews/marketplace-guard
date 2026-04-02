from __future__ import annotations

from fastapi import FastAPI

from .agent_runtime import AgentRuntime
from .models import TurnRequest


def create_app(runtime: AgentRuntime) -> FastAPI:
    app = FastAPI(title="VALARIS Agent System", version="0.1.0")

    @app.post("/v1/turns")
    async def run_turn(request: TurnRequest):
        result = await runtime.run(request)
        return result.model_dump(mode="json")

    return app
