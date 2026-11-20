from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ListingCreateRequest(BaseModel):
    category_id: UUID
    title: str = Field(..., min_length=3, max_length=150)
    quantity_kg: Decimal = Field(..., gt=0)
    price_per_kg: Decimal = Field(..., ge=Decimal("-10000.00"), le=Decimal("1000000.00"))
    is_negotiable: bool = True
    area: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., min_length=6, max_length=10)
    expires_at: datetime | None = None


class SellerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    phone: str
    role: str
    area: str
    pincode: str


class CategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    unit: str
    stream: str = "dry"
    allows_zero_or_negative_price: bool = False
    expiry_hours: int | None = None


class ListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    seller_id: UUID
    category_id: UUID
    title: str
    quantity_kg: Decimal
    price_per_kg: Decimal
    is_negotiable: bool
    area: str
    pincode: str
    status: str
    expires_at: datetime | None = None
    is_expired: bool = False
    matches_count: int = 0
    created_at: datetime
    seller: SellerSummary
    category: CategorySummary
