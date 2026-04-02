from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from ..schemas import ActionRunRecord, AlertDetail, AlertRecord, MarginResult, ProductSummary, TimelineEvent


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class MarketplaceRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        schema_path = Path(__file__).with_name("schema.sql")
        schema_sql = schema_path.read_text(encoding="utf-8")
        with self.connection() as conn:
            conn.executescript(schema_sql)
            self._ensure_alert_schema_columns(conn)

    def seed_mock_data(self) -> None:
        seed_path = Path(__file__).with_name("seed.sql")
        seed_sql = seed_path.read_text(encoding="utf-8")
        with self.connection() as conn:
            conn.executescript(seed_sql)

    def list_products(self) -> List[ProductSummary]:
        query = """
        WITH latest_cost AS (
            SELECT c1.*
            FROM costs c1
            JOIN (
                SELECT product_id, MAX(effective_from) AS effective_from
                FROM costs
                GROUP BY product_id
            ) c2
              ON c1.product_id = c2.product_id
             AND c1.effective_from = c2.effective_from
        ),
        latest_price AS (
            SELECT p1.*
            FROM prices p1
            JOIN (
                SELECT listing_id, MAX(captured_at) AS captured_at
                FROM prices
                GROUP BY listing_id
            ) p2
              ON p1.listing_id = p2.listing_id
             AND p1.captured_at = p2.captured_at
        )
        SELECT
            products.id AS product_id,
            products.sku,
            products.name,
            products.brand,
            products.category,
            products.status,
            products.currency,
            COUNT(DISTINCT listings.channel_id) AS channel_count,
            SUM(CASE WHEN listings.listing_status = 'active' THEN 1 ELSE 0 END) AS active_listing_count,
            MIN(latest_price.final_price) AS min_price,
            MAX(latest_price.final_price) AS max_price,
            latest_cost.unit_cost AS current_cost,
            latest_cost.min_margin_amount AS min_margin_amount
        FROM products
        LEFT JOIN listings ON listings.product_id = products.id
        LEFT JOIN latest_price ON latest_price.listing_id = listings.id
        LEFT JOIN latest_cost ON latest_cost.product_id = products.id
        GROUP BY products.id, products.sku, products.name, products.brand, products.category,
                 products.status, products.currency, latest_cost.unit_cost, latest_cost.min_margin_amount
        ORDER BY products.sku
        """
        with self.connection() as conn:
            rows = conn.execute(query).fetchall()
        return [ProductSummary.model_validate(dict(row)) for row in rows]

    def get_listing_margin(self, listing_id: int) -> Optional[MarginResult]:
        snapshots = self.get_detection_snapshots()
        for snapshot in snapshots:
            if int(snapshot["listing_id"]) == listing_id:
                allowed_keys = set(MarginResult.model_fields.keys())
                filtered_snapshot = {
                    key: value
                    for key, value in snapshot.items()
                    if key in allowed_keys
                }
                return MarginResult.model_validate(filtered_snapshot)
        return None

    def get_detection_snapshots(self) -> List[Dict[str, Any]]:
        query = """
        WITH latest_price AS (
            SELECT p1.*
            FROM prices p1
            JOIN (
                SELECT listing_id, MAX(captured_at) AS captured_at
                FROM prices
                GROUP BY listing_id
            ) p2
              ON p1.listing_id = p2.listing_id
             AND p1.captured_at = p2.captured_at
        ),
        latest_cost AS (
            SELECT c1.*
            FROM costs c1
            JOIN (
                SELECT product_id, MAX(effective_from) AS effective_from
                FROM costs
                GROUP BY product_id
            ) c2
              ON c1.product_id = c2.product_id
             AND c1.effective_from = c2.effective_from
        ),
        active_promo AS (
            SELECT p.*
            FROM promotions p
            WHERE p.status = 'active'
        )
        SELECT
            listings.id AS listing_id,
            listings.product_id,
            listings.listing_status,
            listings.avg_daily_units,
            listings.inventory_qty,
            products.sku,
            products.currency,
            products.name AS product_name,
            channels.code AS channel_code,
            channels.name AS channel_name,
            latest_price.final_price,
            latest_price.fee_amount,
            latest_price.shipping_subsidy_amount,
            latest_price.captured_at,
            latest_cost.unit_cost,
            latest_cost.handling_cost,
            latest_cost.min_margin_amount,
            active_promo.id AS promotion_id,
            active_promo.promo_type AS promotion_name
        FROM listings
        JOIN products ON products.id = listings.product_id
        JOIN channels ON channels.id = listings.channel_id
        JOIN latest_price ON latest_price.listing_id = listings.id
        JOIN latest_cost ON latest_cost.product_id = listings.product_id
        LEFT JOIN active_promo ON active_promo.listing_id = listings.id
        ORDER BY listings.id
        """
        with self.connection() as conn:
            rows = conn.execute(query).fetchall()
        snapshots: List[Dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            net_revenue = float(item["final_price"]) - float(item["fee_amount"]) - float(
                item["shipping_subsidy_amount"]
            )
            threshold_value = float(item["unit_cost"]) + float(item["handling_cost"]) + float(
                item["min_margin_amount"]
            )
            margin_value = net_revenue - float(item["unit_cost"]) - float(item["handling_cost"])
            item["net_revenue"] = round(net_revenue, 2)
            item["threshold_value"] = round(threshold_value, 2)
            item["margin_value"] = round(margin_value, 2)
            item["margin_gap"] = round(threshold_value - net_revenue, 2)
            item["margin_ok"] = net_revenue >= threshold_value
            snapshots.append(item)
        return snapshots

    def upsert_alert(self, payload: Dict[str, Any]) -> AlertRecord:
        now = utc_now_iso()
        evidence_json = json.dumps(payload["evidence"], sort_keys=True)
        with self.connection() as conn:
            existing = conn.execute(
                "SELECT id, created_at FROM alerts WHERE dedupe_key = ?",
                (payload["dedupe_key"],),
            ).fetchone()
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO alerts (
                        alert_type, severity, status, product_id, listing_id, title, explanation,
                        estimated_loss, impact_score, priority_score, estimated_loss_component,
                        negative_margin_component, volume_component, suggested_action,
                        dedupe_key, evidence_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload["alert_type"],
                        payload["severity"],
                        payload.get("status", "open"),
                        payload["product_id"],
                        payload.get("listing_id"),
                        payload["title"],
                        payload["explanation"],
                        payload["estimated_loss"],
                        payload["impact_score"],
                        payload["priority_score"],
                        payload["estimated_loss_component"],
                        payload["negative_margin_component"],
                        payload["volume_component"],
                        payload["suggested_action"],
                        payload["dedupe_key"],
                        evidence_json,
                        now,
                        now,
                    ),
                )
                alert_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
            else:
                alert_id = int(existing["id"])
                conn.execute(
                    """
                    UPDATE alerts
                       SET severity = ?,
                           status = ?,
                           product_id = ?,
                           listing_id = ?,
                           title = ?,
                           explanation = ?,
                           estimated_loss = ?,
                           impact_score = ?,
                           priority_score = ?,
                           estimated_loss_component = ?,
                           negative_margin_component = ?,
                           volume_component = ?,
                           suggested_action = ?,
                           evidence_json = ?,
                           updated_at = ?
                     WHERE id = ?
                    """,
                    (
                        payload["severity"],
                        payload.get("status", "open"),
                        payload["product_id"],
                        payload.get("listing_id"),
                        payload["title"],
                        payload["explanation"],
                        payload["estimated_loss"],
                        payload["impact_score"],
                        payload["priority_score"],
                        payload["estimated_loss_component"],
                        payload["negative_margin_component"],
                        payload["volume_component"],
                        payload["suggested_action"],
                        evidence_json,
                        now,
                        alert_id,
                    ),
                )
        alert = self.get_alert(alert_id)
        if alert is None:
            raise RuntimeError(f"Alert {alert_id} was not persisted.")
        return alert

    def list_alerts(self) -> List[AlertRecord]:
        query = """
        SELECT
            alerts.id,
            alerts.alert_type,
            alerts.severity,
            alerts.status,
            alerts.product_id,
            alerts.listing_id,
            products.currency,
            products.sku,
            products.name AS product_name,
            channels.code AS channel_code,
            channels.name AS channel_name,
            alerts.title,
            alerts.explanation,
            alerts.estimated_loss,
            alerts.impact_score,
            alerts.priority_score,
            alerts.estimated_loss_component,
            alerts.negative_margin_component,
            alerts.volume_component,
            alerts.suggested_action,
            alerts.evidence_json,
            alerts.created_at,
            alerts.updated_at
        FROM alerts
        JOIN products ON products.id = alerts.product_id
        LEFT JOIN listings ON listings.id = alerts.listing_id
        LEFT JOIN channels ON channels.id = listings.channel_id
        ORDER BY alerts.priority_score DESC, alerts.impact_score DESC, alerts.created_at DESC
        """
        with self.connection() as conn:
            rows = conn.execute(query).fetchall()
        return [self._row_to_alert(row) for row in rows]

    def get_alert(self, alert_id: int) -> Optional[AlertRecord]:
        query = """
        SELECT
            alerts.id,
            alerts.alert_type,
            alerts.severity,
            alerts.status,
            alerts.product_id,
            alerts.listing_id,
            products.currency,
            products.sku,
            products.name AS product_name,
            channels.code AS channel_code,
            channels.name AS channel_name,
            alerts.title,
            alerts.explanation,
            alerts.estimated_loss,
            alerts.impact_score,
            alerts.priority_score,
            alerts.estimated_loss_component,
            alerts.negative_margin_component,
            alerts.volume_component,
            alerts.suggested_action,
            alerts.evidence_json,
            alerts.created_at,
            alerts.updated_at
        FROM alerts
        JOIN products ON products.id = alerts.product_id
        LEFT JOIN listings ON listings.id = alerts.listing_id
        LEFT JOIN channels ON channels.id = listings.channel_id
        WHERE alerts.id = ?
        """
        with self.connection() as conn:
            row = conn.execute(query, (alert_id,)).fetchone()
        return None if row is None else self._row_to_alert(row)

    def get_alert_detail(self, alert_id: int) -> Optional[AlertDetail]:
        alert = self.get_alert(alert_id)
        if alert is None:
            return None
        pricing = self.get_listing_margin(alert.listing_id) if alert.listing_id else None
        action_runs = self.list_action_runs(alert_id)
        timeline = [
            TimelineEvent(
                event_type="alert_created",
                timestamp=alert.created_at,
                title="Alerta creada",
                details={
                    "severity": alert.severity,
                    "suggested_action": alert.suggested_action,
                },
            )
        ]
        for action_run in action_runs:
            timeline.append(
                TimelineEvent(
                    event_type="action_run",
                    timestamp=action_run.requested_at,
                    title=f"Acción {action_run.action_type}",
                    details={
                        "status": action_run.status,
                        "approval_status": action_run.approval_status,
                        "requested_by": action_run.requested_by,
                    },
                )
            )
        return AlertDetail(alert=alert, pricing=pricing, timeline=timeline, action_runs=action_runs)

    def list_action_runs(self, alert_id: int) -> List[ActionRunRecord]:
        query = """
        SELECT id, alert_id, action_type, target_type, target_id, status, approval_status,
               requested_by, requested_at, executed_at, result_json
        FROM action_runs
        WHERE alert_id = ?
        ORDER BY requested_at DESC, id DESC
        """
        with self.connection() as conn:
            rows = conn.execute(query, (alert_id,)).fetchall()
        return [self._row_to_action_run(row) for row in rows]

    def create_action_run(
        self,
        alert_id: int,
        action_type: str,
        target_type: str,
        target_id: str,
        status: str,
        approval_status: str,
        requested_by: str,
        result: Dict[str, Any],
        executed_at: Optional[str] = None,
    ) -> ActionRunRecord:
        requested_at = utc_now_iso()
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO action_runs (
                    alert_id, action_type, target_type, target_id, status, approval_status,
                    requested_by, requested_at, executed_at, result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert_id,
                    action_type,
                    target_type,
                    target_id,
                    status,
                    approval_status,
                    requested_by,
                    requested_at,
                    executed_at,
                    json.dumps(result, sort_keys=True),
                ),
            )
            action_run_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
        action_runs = self.list_action_runs(alert_id)
        for action_run in action_runs:
            if action_run.id == action_run_id:
                return action_run
        raise RuntimeError(f"Action run {action_run_id} was not persisted.")

    def mark_alert_under_review(self, alert_id: int, requested_by: str) -> ActionRunRecord:
        alert = self.get_alert(alert_id)
        if alert is None:
            raise ValueError(f"Alert {alert_id} does not exist.")
        with self.connection() as conn:
            conn.execute(
                "UPDATE alerts SET status = ?, updated_at = ? WHERE id = ?",
                ("under_review", utc_now_iso(), alert_id),
            )
        return self.create_action_run(
            alert_id=alert_id,
            action_type="mark_review",
            target_type="alert",
            target_id=str(alert_id),
            status="completed",
            approval_status="not_required",
            requested_by=requested_by,
            result={"message": "Alerta marcada en revisión."},
            executed_at=utc_now_iso(),
        )

    def create_notification(self, alert_id: int, requested_by: str) -> ActionRunRecord:
        alert = self.get_alert(alert_id)
        if alert is None:
            raise ValueError(f"Alert {alert_id} does not exist.")
        with self.connection() as conn:
            conn.execute(
                "UPDATE alerts SET status = ?, updated_at = ? WHERE id = ?",
                ("notified", utc_now_iso(), alert_id),
                )
        return self.create_action_run(
            alert_id=alert_id,
            action_type="notify",
            target_type="alert",
            target_id=str(alert_id),
            status="completed",
            approval_status="not_required",
            requested_by=requested_by,
            result={"message": "Notificación simulada enviada."},
            executed_at=utc_now_iso(),
        )

    def simulate_block_listing(self, alert_id: int, requested_by: str) -> Dict[str, Any]:
        alert = self.get_alert(alert_id)
        if alert is None:
            raise ValueError(f"Alert {alert_id} does not exist.")
        if alert.listing_id is None:
            raise ValueError(f"Alert {alert_id} is not linked to a specific listing.")

        executed_at = utc_now_iso()
        with self.connection() as conn:
            listing = conn.execute(
                "SELECT publication_id, listing_status FROM listings WHERE id = ?",
                (alert.listing_id,),
            ).fetchone()
            if listing is None:
                raise ValueError(f"Listing {alert.listing_id} does not exist.")
            conn.execute(
                "UPDATE listings SET listing_status = ? WHERE id = ?",
                ("blocked", alert.listing_id),
            )
            conn.execute(
                "UPDATE alerts SET status = ?, updated_at = ? WHERE id = ?",
                ("actioned", executed_at, alert_id),
            )
        action_run = self.create_action_run(
            alert_id=alert_id,
            action_type="simulate_block_sku",
            target_type="listing",
            target_id=str(alert.listing_id),
            status="completed",
            approval_status="approved",
            requested_by=requested_by,
            result={
                "listing_id": alert.listing_id,
                "publication_id": listing["publication_id"],
                "previous_status": listing["listing_status"],
                "new_status": "blocked",
            },
            executed_at=executed_at,
        )
        return {
            "action_run_id": action_run.id,
            "listing_id": alert.listing_id,
            "publication_id": listing["publication_id"],
            "new_status": "blocked",
        }

    def record_approval_required(self, alert_id: int, requested_by: str) -> ActionRunRecord:
        alert = self.get_alert(alert_id)
        if alert is None:
            raise ValueError(f"Alert {alert_id} does not exist.")
        target_id = str(alert.listing_id or alert.id)
        return self.create_action_run(
            alert_id=alert_id,
            action_type="simulate_block_sku",
            target_type="listing" if alert.listing_id else "alert",
            target_id=target_id,
            status="needs_approval",
            approval_status="required",
            requested_by=requested_by,
            result={"message": "La policy requiere approval para bloquear la publicación."},
        )

    @staticmethod
    def _row_to_alert(row: sqlite3.Row) -> AlertRecord:
        payload = dict(row)
        payload["evidence"] = json.loads(payload.pop("evidence_json"))
        return AlertRecord.model_validate(payload)

    @staticmethod
    def _row_to_action_run(row: sqlite3.Row) -> ActionRunRecord:
        payload = dict(row)
        payload["result"] = json.loads(payload.pop("result_json"))
        return ActionRunRecord.model_validate(payload)

    @staticmethod
    def _ensure_alert_schema_columns(conn: sqlite3.Connection) -> None:
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(alerts)").fetchall()
        }
        required_columns = {
            "estimated_loss": "REAL NOT NULL DEFAULT 0",
            "priority_score": "REAL NOT NULL DEFAULT 0",
            "estimated_loss_component": "REAL NOT NULL DEFAULT 0",
            "negative_margin_component": "REAL NOT NULL DEFAULT 0",
            "volume_component": "REAL NOT NULL DEFAULT 0",
        }
        for column_name, definition in required_columns.items():
            if column_name in columns:
                continue
            try:
                conn.execute(
                    f"ALTER TABLE alerts ADD COLUMN {column_name} {definition}"
                )
            except sqlite3.OperationalError as exc:
                if "duplicate column name" not in str(exc).lower():
                    raise
