from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from fastapi import HTTPException
from fastapi.routing import APIRoute

from marketplace_guard.api import create_app
from marketplace_guard.schemas import AlertActionRequest, SimulateRunRequest


def endpoint(app, path: str, method: str):
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path == path and method in route.methods:
            return route.endpoint
    raise RuntimeError(f"Route {method} {path} was not found.")


class MarketplaceGuardApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmpdir.name)
        self.app = create_app(workspace=self.workspace)
        self.simulate_run = endpoint(self.app, "/simulate-run", "POST")
        self.list_alerts = endpoint(self.app, "/alerts", "GET")
        self.get_alert = endpoint(self.app, "/alerts/{alert_id}", "GET")
        self.run_alert_action = endpoint(self.app, "/alerts/{alert_id}/actions", "POST")

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_simulate_run_creates_alerts(self) -> None:
        response = asyncio.run(
            self.simulate_run(
                SimulateRunRequest(session_id="demo-run", requested_by="qa-user")
            )
        )
        payload = response
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["data"]["alerts_created"], 3)
        self.assertTrue(
            all(item["estimated_loss"] >= 0 for item in payload["data"]["alerts"])
        )
        self.assertTrue(
            all(round(item["estimated_loss"], 2) == item["estimated_loss"] for item in payload["data"]["alerts"])
        )
        self.assertTrue(
            all(item["currency"] == "CLP" for item in payload["data"]["alerts"])
        )
        self.assertTrue(
            all(item["priority_score"] > 0 for item in payload["data"]["alerts"])
        )
        self.assertTrue(
            all("estimated_loss_component" in item for item in payload["data"]["alerts"])
        )
        self.assertTrue(
            all("negative_margin_component" in item for item in payload["data"]["alerts"])
        )
        self.assertTrue(
            all("volume_component" in item for item in payload["data"]["alerts"])
        )

        alerts_payload = asyncio.run(self.list_alerts())
        self.assertEqual(len(alerts_payload["data"]), 3)
        alert_types = {item["alert_type"] for item in alerts_payload["data"]}
        self.assertEqual(
            alert_types,
            {"broken_margin", "promo_margin_break", "price_inconsistency"},
        )
        self.assertGreaterEqual(
            alerts_payload["data"][0]["priority_score"],
            alerts_payload["data"][1]["priority_score"],
        )

    def test_block_action_requires_approval_then_blocks(self) -> None:
        asyncio.run(
            self.simulate_run(
                SimulateRunRequest(session_id="demo-run", requested_by="qa-user")
            )
        )
        alerts_payload = asyncio.run(self.list_alerts())
        blockable_alert = next(
            item
            for item in alerts_payload["data"]
            if item["suggested_action"] == "simulate_block_sku"
        )

        with self.assertRaises(HTTPException) as denied:
            asyncio.run(
                self.run_alert_action(
                    blockable_alert["id"],
                    AlertActionRequest(
                        action_type="simulate_block_sku",
                        requested_by="qa-user",
                        approved=False,
                    ),
                )
            )
        self.assertEqual(denied.exception.status_code, 409)
        self.assertEqual(denied.exception.detail["error"], "approval_required")

        approved_response = asyncio.run(
            self.run_alert_action(
                blockable_alert["id"],
                AlertActionRequest(
                    action_type="simulate_block_sku",
                    requested_by="qa-user",
                    approved=True,
                ),
            )
        )
        self.assertTrue(approved_response["ok"])
        detail_payload = asyncio.run(self.get_alert(blockable_alert["id"]))["data"]
        self.assertIn("estimated_loss", detail_payload["alert"])
        self.assertEqual(detail_payload["alert"]["currency"], "CLP")
        self.assertGreaterEqual(detail_payload["alert"]["estimated_loss"], 0)
        self.assertEqual(
            round(detail_payload["alert"]["estimated_loss"], 2),
            detail_payload["alert"]["estimated_loss"],
        )
        self.assertIn("estimated_loss_component", detail_payload["alert"])
        self.assertIn("negative_margin_component", detail_payload["alert"])
        self.assertIn("volume_component", detail_payload["alert"])
        self.assertEqual(detail_payload["alert"]["status"], "actioned")
        self.assertTrue(detail_payload["action_runs"])
        self.assertEqual(detail_payload["action_runs"][0]["status"], "completed")
