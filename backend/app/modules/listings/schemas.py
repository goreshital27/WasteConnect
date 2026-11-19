from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ListingCreateRequest(BaseModel):
    category_id: UUID
    title: str = Field(..., min_length=3, max_length=150)
    quantity_kg: Decimal = Field(..., gt=0)
    price_per_kg: Decimal = Field(..., gt=0)
    is_negotiable: bool = True
    area: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., min_length=6, max_length=10)


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
    created_at: datetime
    seller: SellerSummary
    category: CategorySummary
