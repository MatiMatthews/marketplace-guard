from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from ..schemas import AnomalyRecord, DetectionResult


def _round_money(value: float) -> float:
    return round(value, 2)


def _normalize_positive_money(value: float) -> float:
    return round(max(0.0, float(value)), 2)


class DetectionEngine:
    def __init__(
        self,
        price_diff_pct_threshold: float = 0.08,
        price_diff_abs_threshold: float = 5000,
    ) -> None:
        self.price_diff_pct_threshold = price_diff_pct_threshold
        self.price_diff_abs_threshold = price_diff_abs_threshold

    def detect(self, snapshots: List[Dict[str, object]]) -> DetectionResult:
        anomalies: List[AnomalyRecord] = []
        by_product: Dict[int, List[Dict[str, object]]] = defaultdict(list)

        for snapshot in snapshots:
            by_product[int(snapshot["product_id"])].append(snapshot)
            if self._is_margin_broken(snapshot):
                anomalies.append(self._build_margin_alert(snapshot))

        for product_snapshots in by_product.values():
            inconsistency = self._build_price_inconsistency_alert(product_snapshots)
            if inconsistency is not None:
                anomalies.append(inconsistency)

        summary = {
            "total_candidates": len(anomalies),
            "broken_margin_count": sum(
                1 for item in anomalies if item.alert_type == "broken_margin"
            ),
            "promo_margin_break_count": sum(
                1 for item in anomalies if item.alert_type == "promo_margin_break"
            ),
            "price_inconsistency_count": sum(
                1 for item in anomalies if item.alert_type == "price_inconsistency"
            ),
        }
        return DetectionResult(anomalies=anomalies, summary=summary)

    @staticmethod
    def _is_margin_broken(snapshot: Dict[str, object]) -> bool:
        return float(snapshot["net_revenue"]) < float(snapshot["threshold_value"])

    @staticmethod
    def _build_priority_breakdown(
        estimated_loss: float,
        negative_margin: float,
        volume: float,
    ) -> Dict[str, float]:
        estimated_loss_component = min(60.0, max(0.0, estimated_loss) / 1000.0)
        negative_margin_component = min(25.0, max(0.0, negative_margin) / 500.0)
        volume_component = min(15.0, max(0.0, volume) * 2.0)
        priority_score = round(
            estimated_loss_component
            + negative_margin_component
            + volume_component,
            2,
        )
        return {
            "estimated_loss_component": round(estimated_loss_component, 2),
            "negative_margin_component": round(negative_margin_component, 2),
            "volume_component": round(volume_component, 2),
            "priority_score": priority_score,
        }

    def _build_margin_alert(self, snapshot: Dict[str, object]) -> AnomalyRecord:
        product_id = int(snapshot["product_id"])
        listing_id = int(snapshot["listing_id"])
        sku = str(snapshot["sku"])
        currency = str(snapshot.get("currency") or "CLP")
        channel_code = str(snapshot["channel_code"])
        gap = _round_money(float(snapshot["threshold_value"]) - float(snapshot["net_revenue"]))
        margin_value = _round_money(float(snapshot["margin_value"]))
        avg_daily_units = float(snapshot["avg_daily_units"])
        promotion_id = snapshot.get("promotion_id")
        has_active_promo = promotion_id is not None
        estimated_loss = _normalize_positive_money(gap * avg_daily_units)
        negative_margin = _round_money(max(0.0, -margin_value))
        impact_score = min(100.0, round(estimated_loss / 1000.0, 2))
        priority_breakdown = self._build_priority_breakdown(
            estimated_loss=estimated_loss,
            negative_margin=negative_margin,
            volume=avg_daily_units,
        )
        severity = "critical" if gap >= 6000 or avg_daily_units >= 5 else "high"
        alert_type = "promo_margin_break" if has_active_promo else "broken_margin"
        suggested_action = "simulate_block_sku" if gap >= 3000 else "mark_review"
        dedupe_key = f"{alert_type}:{listing_id}"
        title = (
            f"Promo activa rompe margen en {sku} / {channel_code}"
            if has_active_promo
            else f"Margen roto en {sku} / {channel_code}"
        )
        explanation = (
            f"El listing {sku} en {channel_code} queda con margen {margin_value} CLP "
            f"y un gap de {gap} CLP contra el margen mínimo requerido."
        )
        return AnomalyRecord(
            alert_type=alert_type,
            severity=severity,
            product_id=product_id,
            listing_id=listing_id,
            currency=currency,
            title=title,
            explanation=explanation,
            estimated_loss=estimated_loss,
            impact_score=impact_score,
            priority_score=priority_breakdown["priority_score"],
            estimated_loss_component=priority_breakdown["estimated_loss_component"],
            negative_margin_component=priority_breakdown["negative_margin_component"],
            volume_component=priority_breakdown["volume_component"],
            suggested_action=suggested_action,
            dedupe_key=dedupe_key,
            evidence={
                "sku": sku,
                "channel_code": channel_code,
                "final_price": _round_money(float(snapshot["final_price"])),
                "net_revenue": _round_money(float(snapshot["net_revenue"])),
                "margin_value": margin_value,
                "threshold_value": _round_money(float(snapshot["threshold_value"])),
                "margin_gap": gap,
                "estimated_loss": estimated_loss,
                "negative_margin": negative_margin,
                "avg_daily_units": avg_daily_units,
                "promotion_id": promotion_id,
                "promotion_name": snapshot.get("promotion_name"),
            },
        )

    def _build_price_inconsistency_alert(
        self,
        product_snapshots: List[Dict[str, object]],
    ) -> AnomalyRecord | None:
        active_snapshots = [
            snapshot
            for snapshot in product_snapshots
            if snapshot.get("listing_status") == "active"
        ]
        if len(active_snapshots) < 2:
            return None

        cheapest = min(active_snapshots, key=lambda item: float(item["final_price"]))
        most_expensive = max(active_snapshots, key=lambda item: float(item["final_price"]))
        low_price = float(cheapest["final_price"])
        high_price = float(most_expensive["final_price"])
        spread_abs = _round_money(high_price - low_price)
        if low_price <= 0:
            return None
        spread_pct = round(spread_abs / low_price, 4)
        if (
            spread_abs < self.price_diff_abs_threshold
            or spread_pct < self.price_diff_pct_threshold
        ):
            return None

        product_id = int(cheapest["product_id"])
        sku = str(cheapest["sku"])
        currency = str(cheapest.get("currency") or "CLP")
        total_daily_units = sum(float(snapshot["avg_daily_units"]) for snapshot in active_snapshots)
        worst_negative_margin = max(
            0.0,
            max(
                -float(snapshot["margin_value"])
                for snapshot in active_snapshots
            ),
        )
        estimated_loss = _normalize_positive_money(spread_abs * total_daily_units * 0.25)
        impact_score = min(100.0, round(estimated_loss / 1000.0, 2))
        priority_breakdown = self._build_priority_breakdown(
            estimated_loss=estimated_loss,
            negative_margin=worst_negative_margin,
            volume=total_daily_units,
        )
        severity = "high" if spread_pct >= 0.15 else "medium"
        return AnomalyRecord(
            alert_type="price_inconsistency",
            severity=severity,
            product_id=product_id,
            listing_id=None,
            currency=currency,
            title=f"Inconsistencia de precio entre canales para {sku}",
            explanation=(
                f"El SKU {sku} muestra una diferencia de {spread_abs} CLP "
                f"({round(spread_pct * 100, 1)}%) entre {cheapest['channel_code']} "
                f"y {most_expensive['channel_code']}."
            ),
            estimated_loss=estimated_loss,
            impact_score=impact_score,
            priority_score=priority_breakdown["priority_score"],
            estimated_loss_component=priority_breakdown["estimated_loss_component"],
            negative_margin_component=priority_breakdown["negative_margin_component"],
            volume_component=priority_breakdown["volume_component"],
            suggested_action="mark_review",
            dedupe_key=f"price_inconsistency:{product_id}",
            evidence={
                "sku": sku,
                "lowest_channel": cheapest["channel_code"],
                "highest_channel": most_expensive["channel_code"],
                "lowest_price": _round_money(low_price),
                "highest_price": _round_money(high_price),
                "spread_abs": spread_abs,
                "spread_pct": spread_pct,
                "estimated_loss": estimated_loss,
                "negative_margin": _round_money(worst_negative_margin),
                "total_daily_units": round(total_daily_units, 2),
                "channels_compared": [
                    {
                        "channel_code": snapshot["channel_code"],
                        "final_price": _round_money(float(snapshot["final_price"])),
                    }
                    for snapshot in sorted(
                        active_snapshots,
                        key=lambda item: float(item["final_price"]),
                    )
                ],
            },
        )
