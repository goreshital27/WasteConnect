from datetime import UTC, datetime
from uuid import UUID

from app.modules.notifications.models import Notification
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session


class NotificationService:
    @staticmethod
    def get_user_notifications(db: Session, user_id: UUID) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_unread_count(db: Session, user_id: UUID) -> int:
        stmt = (
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
        )
        return len(list(db.scalars(stmt).all()))

    @staticmethod
    def mark_as_read(db: Session, notification_id: UUID, user_id: UUID) -> Notification:
        notif = db.scalar(select(Notification).where(Notification.id == notification_id))
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "NOTIFICATION_NOT_FOUND", "detail": "Notification not found"},
            )
        if notif.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "detail": "Access forbidden"},
            )
        if not notif.read_at:
            notif.read_at = datetime.now(UTC)
            db.commit()
            db.refresh(notif)
        return notif

    @staticmethod
    def mark_all_as_read(db: Session, user_id: UUID) -> int:
        now = datetime.now(UTC)
        result = db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .values(read_at=now)
        )
        db.commit()
        return result.rowcount or 0
