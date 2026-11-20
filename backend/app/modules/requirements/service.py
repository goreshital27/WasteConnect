from uuid import UUID

from app.modules.catalog.models import WasteCategory
from app.modules.matching.service import MatchingService
from app.modules.requirements.models import Requirement
from app.modules.requirements.schemas import RequirementCreateRequest
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session


class RequirementService:
    @staticmethod
    def create_requirement(
        db: Session,
        buyer_id: UUID,
        req: RequirementCreateRequest,
    ) -> Requirement:
        category = db.scalar(select(WasteCategory).where(WasteCategory.id == req.category_id))
        if not category or not category.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CATEGORY_NOT_FOUND", "detail": "Active category not found"},
            )

        requirement = Requirement(
            buyer_id=buyer_id,
            category_id=req.category_id,
            quantity_kg=req.quantity_kg,
            max_price_per_kg=req.max_price_per_kg,
            pincode=req.pincode.strip(),
            status="open",
        )
        db.add(requirement)
        db.flush()

        # Match against open listings
        MatchingService.match_new_requirement(db, requirement)

        db.commit()
        db.refresh(requirement)
        return requirement

    @staticmethod
    def get_my_requirements(db: Session, buyer_id: UUID) -> list[Requirement]:
        stmt = (
            select(Requirement)
            .where(Requirement.buyer_id == buyer_id)
            .order_by(Requirement.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_open_requirements(
        db: Session,
        category_id: UUID | None = None,
        category_code: str | None = None,
        pincode: str | None = None,
    ) -> list[Requirement]:
        stmt = select(Requirement).where(Requirement.status == "open")
        if category_id:
            stmt = stmt.where(Requirement.category_id == category_id)
        if category_code:
            stmt = stmt.join(Requirement.category).where(
                WasteCategory.code == category_code.lower().strip()
            )
        if pincode:
            stmt = stmt.where(Requirement.pincode == pincode.strip())
        stmt = stmt.order_by(Requirement.created_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def close_requirement(db: Session, requirement_id: UUID, user_id: UUID) -> Requirement:
        req = db.scalar(select(Requirement).where(Requirement.id == requirement_id))
        if not req:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "REQUIREMENT_NOT_FOUND", "detail": "Requirement not found"},
            )
        if req.buyer_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "detail": "Only the creator can close this requirement",
                },
            )
        req.status = "closed"
        db.commit()
        db.refresh(req)
        return req
