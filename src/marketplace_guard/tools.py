from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from valaris_agent_system.runtime.models import ExecutionContext, RetryPolicy, RiskLevel, ToolSpec
from valaris_agent_system.tools.base import BaseTool

from .db import MarketplaceRepository
from .domain import DetectionEngine
from .schemas import AnomalyRecord, DetectionResult, MarginResult, ProductSummary


class GetProductsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=50, ge=1, le=200)


class GetProductsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    products: List[ProductSummary]


class GetProductsTool(BaseTool):
    spec = ToolSpec(
        name="get_products",
        description="List products with current pricing coverage.",
        risk_level=RiskLevel.LOW,
    )
    input_model = GetProductsInput
    output_model = GetProductsOutput

    def __init__(self, repository: MarketplaceRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        payload: GetProductsInput,
        context: ExecutionContext,
    ) -> GetProductsOutput:
        return GetProductsOutput(products=self.repository.list_products()[: payload.limit])


class CalculateMarginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    listing_id: int


class CalculateMarginOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    margin: Optional[MarginResult] = None


class CalculateMarginTool(BaseTool):
    spec = ToolSpec(
        name="calculate_margin",
        description="Calculate the current margin for one listing.",
        risk_level=RiskLevel.LOW,
    )
    input_model = CalculateMarginInput
    output_model = CalculateMarginOutput

    def __init__(self, repository: MarketplaceRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        payload: CalculateMarginInput,
        context: ExecutionContext,
    ) -> CalculateMarginOutput:
        return CalculateMarginOutput(margin=self.repository.get_listing_margin(payload.listing_id))


class DetectAnomaliesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_alerts: int = Field(default=20, ge=1, le=100)


class DetectAnomaliesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    anomalies: List[AnomalyRecord] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)


class DetectAnomaliesTool(BaseTool):
    spec = ToolSpec(
        name="detect_anomalies",
        description="Run pricing and promotion rules against marketplace listings.",
        risk_level=RiskLevel.LOW,
        retry_policy=RetryPolicy(max_attempts=1),
    )
    input_model = DetectAnomaliesInput
    output_model = DetectAnomaliesOutput

    def __init__(
        self,
        repository: MarketplaceRepository,
        engine: DetectionEngine,
    ) -> None:
        self.repository = repository
        self.engine = engine

    async def execute(
        self,
        payload: DetectAnomaliesInput,
        context: ExecutionContext,
    ) -> DetectAnomaliesOutput:
        result: DetectionResult = self.engine.detect(self.repository.get_detection_snapshots())
        anomalies = result.anomalies[: payload.max_alerts]
        summary = dict(result.summary)
        summary["returned_alerts"] = len(anomalies)
        return DetectAnomaliesOutput(anomalies=anomalies, summary=summary)


class CreateAlertInput(AnomalyRecord):
    model_config = ConfigDict(extra="forbid")


class CreateAlertOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alert_id: int
    severity: str
    status: str
    suggested_action: str


class CreateAlertTool(BaseTool):
    spec = ToolSpec(
        name="create_alert",
        description="Persist a detected anomaly as an alert.",
        risk_level=RiskLevel.MEDIUM,
    )
    input_model = CreateAlertInput
    output_model = CreateAlertOutput

    def __init__(self, repository: MarketplaceRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        payload: CreateAlertInput,
        context: ExecutionContext,
    ) -> CreateAlertOutput:
        alert = self.repository.upsert_alert(payload.model_dump())
        return CreateAlertOutput(
            alert_id=alert.id,
            severity=alert.severity,
            status=alert.status,
            suggested_action=alert.suggested_action,
        )


class SimulateBlockSkuInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alert_id: int
    requested_by: str = "demo-user"


class SimulateBlockSkuOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_run_id: int
    listing_id: int
    publication_id: str
    new_status: str


class SimulateBlockSkuTool(BaseTool):
    spec = ToolSpec(
        name="simulate_block_sku",
        description="Simulate blocking a marketplace listing linked to an alert.",
        risk_level=RiskLevel.HIGH,
    )
    input_model = SimulateBlockSkuInput
    output_model = SimulateBlockSkuOutput

    def __init__(self, repository: MarketplaceRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        payload: SimulateBlockSkuInput,
        context: ExecutionContext,
    ) -> SimulateBlockSkuOutput:
        result = self.repository.simulate_block_listing(
            alert_id=payload.alert_id,
            requested_by=payload.requested_by,
        )
        return SimulateBlockSkuOutput(**result)
