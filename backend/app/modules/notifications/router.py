from typing import Annotated, Any
from uuid import UUID

from app.core.database import get_db
from app.core.permissions.auth import get_current_user
from app.modules.auth.models import User
from app.modules.notifications.schemas import NotificationResponse
from app.modules.notifications.service import NotificationService
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    items = NotificationService.get_user_notifications(db, current_user.id)
    unread_count = NotificationService.get_unread_count(db, current_user.id)
    data = []
    for item in items:
        d = NotificationResponse.model_validate(item).model_dump(mode="json")
        d["is_read"] = item.read_at is not None
        data.append(d)
    return {
        "code": "SUCCESS",
        "data": {
            "unread_count": unread_count,
            "items": data,
        },
    }


@router.post(
    "/{notification_id}/read",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def mark_notification_read(
    notification_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    item = NotificationService.mark_as_read(db, notification_id, current_user.id)
    d = NotificationResponse.model_validate(item).model_dump(mode="json")
    d["is_read"] = item.read_at is not None
    return {
        "code": "SUCCESS",
        "data": d,
    }


@router.post(
    "/read-all",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def mark_all_notifications_read(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    count = NotificationService.mark_all_as_read(db, current_user.id)
    return {
        "code": "SUCCESS",
        "data": {"marked_read": count},
    }
