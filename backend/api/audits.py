"""Audit endpoints."""

from __future__ import annotations

import json
from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.audit_log import log_action
from backend.core.config import settings
from backend.core.security import get_current_user
from backend.db.models import Audit, FairnessResult, Model, Recommendation, User
from backend.db.session import get_db
from backend.engine.metrics import METRIC_CATALOG
from backend.jobs.queue import enqueue_audit_job
from backend.schemas.schemas import (
    AuditCreateResponse,
    AuditDetailResponse,
    AuditListResponse,
    AuditSummary,
    FairnessResultResponse,
    ProtectedAttributeConfig,
    RecommendationResponse,
)

router = APIRouter()


@router.post("", response_model=AuditCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_audit(
    model_id: str = Form(...),
    file: UploadFile = File(...),
    prediction_column: str = Form(...),
    ground_truth_column: str | None = Form(default=None),
    protected_attributes: str = Form(...),
    selected_metrics: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuditCreateResponse:
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if model is None or model.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Model not found.")

    _validate_upload_size(file)
    attrs = _parse_protected_attributes(protected_attributes)
    metrics = _parse_selected_metrics(selected_metrics)
    _validate_ground_truth_requirements(metrics, ground_truth_column)

    upload_path = await _persist_upload(file)
    row_count = _validate_csv_columns(upload_path, prediction_column, ground_truth_column, attrs)

    audit = Audit(
        model_id=model.id,
        user_id=current_user.id,
        status="queued",
        dataset_row_count=row_count,
        protected_attributes=[a.model_dump() for a in attrs],
        selected_metrics=metrics,
        file_path=str(upload_path),
        ground_truth_column=ground_truth_column,
        prediction_column=prediction_column,
    )
    db.add(audit)
    await db.flush()

    try:
        await enqueue_audit_job(audit.id)
    except Exception as exc:
        audit.status = "failed"
        audit.error_message = f"Failed to enqueue audit job: {exc}"

    await log_action(
        db,
        action="audit.created",
        resource_type="Audit",
        resource_id=audit.id,
        user=current_user,
        details={"model_id": model.id, "selected_metrics": metrics},
    )
    return AuditCreateResponse(audit_id=audit.id, status=audit.status, created_at=audit.created_at)


@router.get("/{audit_id}", response_model=AuditDetailResponse)
async def get_audit(
    audit_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuditDetailResponse:
    result = await db.execute(
        select(Audit)
        .where(Audit.id == audit_id, Audit.user_id == current_user.id)
        .options(
            selectinload(Audit.results),
            selectinload(Audit.recommendations),
            selectinload(Audit.model),
        )
    )
    audit = result.scalar_one_or_none()
    if audit is None:
        raise HTTPException(status_code=404, detail="Audit not found.")

    return AuditDetailResponse(
        audit_id=audit.id,
        status=audit.status,
        overall_verdict=audit.overall_verdict,
        dataset_row_count=audit.dataset_row_count,
        results=[_map_result(r) for r in audit.results],
        recommendations=[_map_recommendation(r) for r in audit.recommendations],
        error_message=audit.error_message,
        started_at=audit.started_at,
        completed_at=audit.completed_at,
        narrative_summary=audit.narrative_summary,
        groq_enriched=audit.groq_enriched,
    )


@router.get("", response_model=AuditListResponse)
async def list_audits(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuditListResponse:
    page = max(page, 1)
    per_page = min(max(per_page, 1), 100)
    offset = (page - 1) * per_page

    total_query = await db.execute(
        select(func.count()).select_from(Audit).where(Audit.user_id == current_user.id)
    )
    total = int(total_query.scalar_one())

    rows = await db.execute(
        select(Audit, Model.name)
        .join(Model, Audit.model_id == Model.id)
        .where(Audit.user_id == current_user.id)
        .order_by(Audit.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )

    audits = [
        AuditSummary(
            audit_id=audit.id,
            model_id=audit.model_id,
            model_name=model_name,
            status=audit.status,
            overall_verdict=audit.overall_verdict,
            created_at=audit.created_at,
            groq_enriched=audit.groq_enriched,
        )
        for audit, model_name in rows.all()
    ]
    return AuditListResponse(audits=audits, total=total, page=page, per_page=per_page)


def _map_result(result: FairnessResult) -> FairnessResultResponse:
    return FairnessResultResponse(
        metric_name=result.metric_name,
        protected_attribute=result.protected_attribute,
        privileged_value=result.privileged_value,
        unprivileged_value=result.unprivileged_value,
        disparity=result.disparity,
        threshold=result.threshold,
        status=result.status,
        confidence_interval_lower=result.confidence_interval_lower,
        confidence_interval_upper=result.confidence_interval_upper,
        p_value=result.p_value,
        sample_size_privileged=result.sample_size_privileged,
        sample_size_unprivileged=result.sample_size_unprivileged,
        interpretation=result.interpretation,
    )


def _map_recommendation(item: Recommendation) -> RecommendationResponse:
    return RecommendationResponse(
        priority=item.priority,
        issue=item.issue,
        mitigation_strategy=item.mitigation_strategy,
        mitigation_strategy_enriched=item.mitigation_strategy_enriched,
        implementation_effort=item.implementation_effort,
    )


def _validate_upload_size(file: UploadFile) -> None:
    file.file.seek(0, 2)
    size_bytes = file.file.tell()
    file.file.seek(0)
    if size_bytes > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB upload limit.",
        )


def _parse_protected_attributes(raw: str) -> list[ProtectedAttributeConfig]:
    try:
        parsed = json.loads(raw)
        return [ProtectedAttributeConfig.model_validate(item) for item in parsed]
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"Invalid protected_attributes payload: {exc}"
        ) from exc


def _parse_selected_metrics(raw: str) -> list[str]:
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        raise HTTPException(
            status_code=422, detail=f"Invalid selected_metrics payload: {exc}"
        ) from exc
    if not isinstance(parsed, list) or not parsed:
        raise HTTPException(
            status_code=422, detail="selected_metrics must be a non-empty JSON array."
        )
    unknown = [name for name in parsed if name not in METRIC_CATALOG]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown metrics: {', '.join(unknown)}.")
    return [str(name) for name in parsed]


def _validate_ground_truth_requirements(
    selected_metrics: list[str], ground_truth_column: str | None
) -> None:
    requires_truth = any(METRIC_CATALOG[m]["requires_ground_truth"] for m in selected_metrics)
    if requires_truth and not ground_truth_column:
        raise HTTPException(
            status_code=422,
            detail="ground_truth_column is required for one or more selected metrics.",
        )


async def _persist_upload(file: UploadFile) -> Path:
    extension = Path(file.filename or "upload.csv").suffix or ".csv"
    if extension.lower() != ".csv":
        raise HTTPException(status_code=422, detail="Only CSV uploads are supported.")
    target = settings.upload_path / f"{uuid.uuid4()}{extension}"
    with target.open("wb") as out:
        out.write(await file.read())
    await file.close()
    return target


def _validate_csv_columns(
    file_path: Path,
    prediction_column: str,
    ground_truth_column: str | None,
    protected_attributes: list[ProtectedAttributeConfig],
) -> int:
    try:
        frame = pd.read_csv(file_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Malformed CSV file: {exc}") from exc

    columns = set(frame.columns.tolist())
    required_columns = {prediction_column, *[a.name for a in protected_attributes]}
    if ground_truth_column:
        required_columns.add(ground_truth_column)
    missing = sorted(col for col in required_columns if col not in columns)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"CSV missing required columns: {', '.join(missing)}.",
        )

    if not pd.api.types.is_numeric_dtype(frame[prediction_column]):
        raise HTTPException(
            status_code=422, detail=f"prediction_column '{prediction_column}' must be numeric."
        )
    if ground_truth_column and not pd.api.types.is_numeric_dtype(frame[ground_truth_column]):
        raise HTTPException(
            status_code=422, detail=f"ground_truth_column '{ground_truth_column}' must be numeric."
        )

    return int(len(frame))
