from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.modules.listings.schemas import ListingResponse, SellerSummary
from pydantic import BaseModel, ConfigDict, Field


class OfferCreateRequest(BaseModel):
    quantity_kg: Decimal = Field(..., gt=0)
    price_per_kg: Decimal = Field(..., gt=0)


class OfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    listing_id: UUID
    buyer_id: UUID
    quantity_kg: Decimal
    price_per_kg: Decimal
    status: str
    created_at: datetime
    buyer: SellerSummary
    listing: ListingResponse
