from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException

from .runtime import MarketplaceRuntimeService, build_runtime_components
from .schemas import AlertActionRequest, SimulateRunRequest


def _default_workspace() -> Path:
    configured = os.getenv("MARKETPLACE_GUARD_DATA_DIR")
    if configured:
        return Path(configured).resolve()
    return Path.cwd().resolve()


def create_app(workspace: Path | None = None) -> FastAPI:
    workspace = (workspace or _default_workspace()).resolve()
    repository, runtime, session_store, runtime_service = build_runtime_components(workspace)

    app = FastAPI(title="Marketplace Guard POC", version="0.1.0")
    app.state.repository = repository
    app.state.runtime = runtime
    app.state.session_store = session_store
    app.state.runtime_service = runtime_service

    @app.get("/products")
    async def list_products():
        products = app.state.repository.list_products()
        return {"ok": True, "data": [product.model_dump() for product in products]}

    @app.get("/alerts")
    async def list_alerts():
        alerts = app.state.repository.list_alerts()
        return {"ok": True, "data": [alert.model_dump() for alert in alerts]}

    @app.get("/alerts/{alert_id}")
    async def get_alert(alert_id: int):
        detail = app.state.repository.get_alert_detail(alert_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Alert not found.")
        return {"ok": True, "data": detail.model_dump()}

    @app.post("/simulate-run")
    async def simulate_run(payload: SimulateRunRequest):
        session_id = payload.session_id or f"simulate-{uuid.uuid4().hex[:8]}"
        result = await app.state.runtime_service.run_detection(
            session_id=session_id,
            requested_by=payload.requested_by,
        )
        alerts = [
            app.state.repository.get_alert(alert_id).model_dump()
            for alert_id in result.alert_ids
            if app.state.repository.get_alert(alert_id) is not None
        ]
        return {
            "ok": True,
            "data": {
                "session_id": result.session_id,
                "alerts_created": result.alerts_created,
                "alerts": alerts,
                "summary": result.final_output,
            },
            "meta": {"event_count": len(result.events)},
        }

    @app.post("/alerts/{alert_id}/actions")
    async def run_alert_action(alert_id: int, payload: AlertActionRequest):
        alert = app.state.repository.get_alert(alert_id)
        if alert is None:
            raise HTTPException(status_code=404, detail="Alert not found.")

        if payload.action_type == "mark_review":
            action_run = app.state.repository.mark_alert_under_review(
                alert_id=alert_id,
                requested_by=payload.requested_by,
            )
            return {"ok": True, "data": action_run.model_dump()}

        if payload.action_type == "notify":
            action_run = app.state.repository.create_notification(
                alert_id=alert_id,
                requested_by=payload.requested_by,
            )
            return {"ok": True, "data": action_run.model_dump()}

        result = await app.state.runtime_service.execute_block_action(
            alert_id=alert_id,
            requested_by=payload.requested_by,
            approved=payload.approved,
        )
        if result.requires_approval:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "approval_required",
                    "policy_action": "require_approval",
                    "action_run_id": result.action_run_id,
                    "session_id": result.session_id,
                },
            )

        detail = app.state.repository.get_alert_detail(alert_id)
        return {
            "ok": True,
            "data": {
                "session_id": result.session_id,
                "action_run_id": result.action_run_id,
                "summary": result.final_output,
                "alert": detail.model_dump() if detail is not None else None,
            },
        }

    @app.get("/health")
    async def health():
        return {"ok": True, "data": {"workspace": str(workspace)}}

    return app


app = create_app()
