from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int
    sku: str
    name: str
    brand: str
    category: str
    status: str
    currency: str
    channel_count: int
    active_listing_count: int
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    current_cost: Optional[float] = None
    min_margin_amount: Optional[float] = None


class MarginResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    listing_id: int
    product_id: int
    sku: str
    channel_code: str
    final_price: float
    fee_amount: float
    shipping_subsidy_amount: float
    unit_cost: float
    handling_cost: float
    min_margin_amount: float
    net_revenue: float
    margin_value: float
    threshold_value: float
    margin_gap: float
    margin_ok: bool
    promotion_id: Optional[int] = None
    promotion_name: Optional[str] = None


class AnomalyRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alert_type: Literal["broken_margin", "price_inconsistency", "promo_margin_break"]
    severity: Literal["critical", "high", "medium", "low"]
    status: str = "open"
    product_id: int
    listing_id: Optional[int] = None
    currency: Optional[str] = "CLP"
    title: str
    explanation: str
    estimated_loss: float
    impact_score: float
    priority_score: float
    estimated_loss_component: float
    negative_margin_component: float
    volume_component: float
    suggested_action: Literal["simulate_block_sku", "mark_review", "notify"]
    dedupe_key: str
    evidence: Dict[str, Any] = Field(default_factory=dict)


class DetectionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    anomalies: List[AnomalyRecord] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


class AlertRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    alert_type: str
    severity: str
    status: str
    product_id: int
    listing_id: Optional[int] = None
    currency: Optional[str] = "CLP"
    sku: str
    product_name: str
    channel_code: Optional[str] = None
    channel_name: Optional[str] = None
    title: str
    explanation: str
    estimated_loss: float
    impact_score: float
    priority_score: float
    estimated_loss_component: float
    negative_margin_component: float
    volume_component: float
    suggested_action: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ActionRunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    alert_id: int
    action_type: str
    target_type: str
    target_id: str
    status: str
    approval_status: str
    requested_by: str
    requested_at: str
    executed_at: Optional[str] = None
    result: Dict[str, Any] = Field(default_factory=dict)


class TimelineEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str
    timestamp: str
    title: str
    details: Dict[str, Any] = Field(default_factory=dict)


class AlertDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alert: AlertRecord
    pricing: Optional[MarginResult] = None
    timeline: List[TimelineEvent] = Field(default_factory=list)
    action_runs: List[ActionRunRecord] = Field(default_factory=list)


class SimulateRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: Optional[str] = None
    requested_by: str = "demo-user"


class AlertActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_type: Literal["simulate_block_sku", "mark_review", "notify"]
    requested_by: str = "demo-user"
    approved: bool = False


class RuntimeJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["simulate_run", "execute_block_action"]
    session_id: str
    requested_by: str = "demo-user"
    alert_id: Optional[int] = None


class RuntimeJobResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    final_output: str
    alerts_created: int = 0
    alert_ids: List[int] = Field(default_factory=list)
    requires_approval: bool = False
    action_run_id: Optional[int] = None
    events: List[Dict[str, Any]] = Field(default_factory=list)
