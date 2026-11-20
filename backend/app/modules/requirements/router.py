from typing import Annotated, Any
from uuid import UUID

from app.core.database import get_db
from app.core.permissions.auth import get_current_user
from app.modules.auth.models import User
from app.modules.requirements.schemas import RequirementCreateRequest, RequirementResponse
from app.modules.requirements.service import RequirementService
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/requirements", tags=["Requirements"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
)
def create_requirement(
    req: RequirementCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    item = RequirementService.create_requirement(db, current_user.id, req)
    return {
        "code": "SUCCESS",
        "data": RequirementResponse.model_validate(item).model_dump(mode="json"),
    }


@router.get(
    "/mine",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def list_my_requirements(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    items = RequirementService.get_my_requirements(db, current_user.id)
    return {
        "code": "SUCCESS",
        "data": [RequirementResponse.model_validate(r).model_dump(mode="json") for r in items],
    }


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def list_open_requirements(
    db: Annotated[Session, Depends(get_db)],
    category_id: UUID | None = None,
    category: str | None = None,
    pincode: str | None = None,
) -> dict[str, Any]:
    items = RequirementService.get_open_requirements(
        db,
        category_id=category_id,
        category_code=category,
        pincode=pincode,
    )
    return {
        "code": "SUCCESS",
        "data": [RequirementResponse.model_validate(r).model_dump(mode="json") for r in items],
    }


@router.post(
    "/{requirement_id}/close",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def close_requirement(
    requirement_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    item = RequirementService.close_requirement(db, requirement_id, current_user.id)
    return {
        "code": "SUCCESS",
        "data": RequirementResponse.model_validate(item).model_dump(mode="json"),
    }
