from typing import Annotated, Any
from uuid import UUID

from app.core.database import get_db
from app.core.permissions.auth import get_current_user
from app.modules.auth.models import User
from app.modules.offers.schemas import OfferCreateRequest, OfferResponse
from app.modules.offers.service import OfferService
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter(tags=["Offers"])


@router.post(
    "/listings/{listing_id}/offers",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
)
def create_offer(
    listing_id: UUID,
    req: OfferCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    offer = OfferService.create_offer(db, listing_id, current_user.id, req)
    return {
        "code": "SUCCESS",
        "data": OfferResponse.model_validate(offer).model_dump(mode="json"),
    }


@router.get(
    "/offers/received",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def received_offers(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    offers = OfferService.get_received_offers(db, current_user.id)
    return {
        "code": "SUCCESS",
        "data": [OfferResponse.model_validate(o).model_dump(mode="json") for o in offers],
    }


@router.get(
    "/offers/sent",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def sent_offers(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    offers = OfferService.get_sent_offers(db, current_user.id)
    return {
        "code": "SUCCESS",
        "data": [OfferResponse.model_validate(o).model_dump(mode="json") for o in offers],
    }


@router.post(
    "/offers/{offer_id}/accept",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def accept_offer(
    offer_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    offer, order = OfferService.accept_offer(db, offer_id, current_user.id)
    return {
        "code": "SUCCESS",
        "data": {
            "offer": OfferResponse.model_validate(offer).model_dump(mode="json"),
            "order_id": str(order.id),
        },
    }


@router.post(
    "/offers/{offer_id}/reject",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def reject_offer(
    offer_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    offer = OfferService.reject_offer(db, offer_id, current_user.id)
    return {
        "code": "SUCCESS",
        "data": OfferResponse.model_validate(offer).model_dump(mode="json"),
    }
