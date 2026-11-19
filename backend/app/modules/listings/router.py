from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from app.core.database import get_db
from app.core.permissions.auth import get_current_user
from app.modules.auth.models import User
from app.modules.listings.schemas import ListingCreateRequest, ListingResponse
from app.modules.listings.service import ListingService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

router = APIRouter(tags=["Listings"])


@router.post(
    "/listings",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
)
def create_listing(
    req: ListingCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    listing = ListingService.create_listing(db, current_user.id, req)
    return {
        "code": "SUCCESS",
        "data": ListingResponse.model_validate(listing).model_dump(mode="json"),
    }


@router.get(
    "/listings",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def list_listings(
    db: Annotated[Session, Depends(get_db)],
    category_id: UUID | None = None,
    category: str | None = None,
    pincode: str | None = None,
    min_quantity: Annotated[Decimal | None, Query(gt=0)] = None,
    status_filter: str | None = "open",
) -> dict[str, Any]:
    listings = ListingService.get_listings(
        db,
        category_id=category_id,
        category_code=category,
        pincode=pincode,
        min_quantity=min_quantity,
        status_filter=status_filter,
    )
    return {
        "code": "SUCCESS",
        "data": [ListingResponse.model_validate(item).model_dump(mode="json") for item in listings],
    }


@router.get(
    "/listings/mine",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def my_listings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    listings = ListingService.get_seller_listings(db, current_user.id)
    return {
        "code": "SUCCESS",
        "data": [ListingResponse.model_validate(item).model_dump(mode="json") for item in listings],
    }


@router.get(
    "/listings/{listing_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def get_listing(
    listing_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    listing = ListingService.get_listing_by_id(db, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "LISTING_NOT_FOUND", "detail": "Listing not found"},
        )
    return {
        "code": "SUCCESS",
        "data": ListingResponse.model_validate(listing).model_dump(mode="json"),
    }


@router.post(
    "/listings/{listing_id}/cancel",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def cancel_listing(
    listing_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    listing = ListingService.cancel_listing(db, listing_id, current_user.id)
    return {
        "code": "SUCCESS",
        "data": ListingResponse.model_validate(listing).model_dump(mode="json"),
    }
