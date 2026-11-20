from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.modules.listings.schemas import CategorySummary, SellerSummary
from pydantic import BaseModel, ConfigDict, Field


class RequirementCreateRequest(BaseModel):
    category_id: UUID
    quantity_kg: Decimal = Field(..., gt=0)
    max_price_per_kg: Decimal = Field(..., ge=Decimal("-10000.00"), le=Decimal("1000000.00"))
    pincode: str = Field(..., min_length=6, max_length=10)


class RequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    buyer_id: UUID
    category_id: UUID
    quantity_kg: Decimal
    max_price_per_kg: Decimal
    pincode: str
    status: str
    created_at: datetime
    buyer: SellerSummary
    category: CategorySummary
