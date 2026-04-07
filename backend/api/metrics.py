"""Metrics catalog endpoints."""

from fastapi import APIRouter

from backend.engine.metrics import METRIC_CATALOG
from backend.schemas.schemas import MetricCatalogResponse, MetricInfo

router = APIRouter()


@router.get("", response_model=MetricCatalogResponse)
async def get_metrics() -> MetricCatalogResponse:
    metrics = [MetricInfo(**item) for item in METRIC_CATALOG.values()]
    return MetricCatalogResponse(metrics=metrics)
