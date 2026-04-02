from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi.routing import APIRoute

from marketplace_guard.api import create_app
from marketplace_guard.schemas import SimulateRunRequest


def _endpoint(app, path: str, method: str):
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == path and method in route.methods:
            return route.endpoint
    raise RuntimeError(f"Route {method} {path} was not found.")


def main() -> None:
    workspace = Path(__file__).resolve().parent
    app = create_app(workspace=workspace)
    simulate_run = _endpoint(app, "/simulate-run", "POST")
    list_alerts = _endpoint(app, "/alerts", "GET")

    simulate_response = asyncio.run(
        simulate_run(
            SimulateRunRequest(session_id="marketplace-demo", requested_by="demo-user")
        )
    )
    alerts_response = asyncio.run(list_alerts())

    print("SIMULATE RUN")
    print(json.dumps(simulate_response, indent=2))
    print("\nALERTS")
    print(json.dumps(alerts_response, indent=2))


if __name__ == "__main__":
    main()
