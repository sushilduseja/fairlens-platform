"""Model endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.audit_log import log_action
from backend.core.security import get_current_user
from backend.db.models import Model, User
from backend.db.session import get_db
from backend.schemas.schemas import ModelCreateRequest, ModelListResponse, ModelResponse

router = APIRouter()


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    payload: ModelCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelResponse:
    model = Model(
        user_id=current_user.id,
        name=payload.name,
        use_case=payload.use_case,
        description=payload.description,
    )
    db.add(model)
    await db.flush()
    await log_action(
        db,
        "model.created",
        "Model",
        model.id,
        user=current_user,
        details={"name": model.name, "use_case": model.use_case},
    )
    await db.refresh(model)
    return ModelResponse(
        model_id=model.id,
        name=model.name,
        use_case=model.use_case,
        description=model.description,
        created_at=model.created_at,
    )


@router.get("", response_model=ModelListResponse)
async def list_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelListResponse:
    query = await db.execute(
        select(Model).where(Model.user_id == current_user.id).order_by(Model.created_at.desc())
    )
    models = query.scalars().all()
    return ModelListResponse(
        models=[
            ModelResponse(
                model_id=model.id,
                name=model.name,
                use_case=model.use_case,
                description=model.description,
                created_at=model.created_at,
            )
            for model in models
        ]
    )
