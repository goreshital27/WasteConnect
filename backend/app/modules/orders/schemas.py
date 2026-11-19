from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.modules.listings.schemas import SellerSummary
from app.modules.offers.schemas import OfferResponse
from pydantic import BaseModel, ConfigDict, Field


class WeightRecordCreateRequest(BaseModel):
    stage: str = Field(..., pattern="^(collection|delivery)$")
    weight_kg: Decimal = Field(..., gt=0)


class WeightRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    stage: str
    weight_kg: Decimal
    created_at: datetime


class OrderStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    from_status: str | None
    to_status: str
    changed_by_id: UUID
    created_at: datetime


class OrderStatusTransitionRequest(BaseModel):
    target_status: str = Field(..., pattern="^(collected|delivered|completed|cancelled)$")


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_id: UUID
    seller_id: UUID
    buyer_id: UUID
    status: str
    created_at: datetime
    seller: SellerSummary
    buyer: SellerSummary
    offer: OfferResponse
    weight_records: list[WeightRecordResponse] = []
    status_history: list[OrderStatusHistoryResponse] = []
    collection_weight_kg: Decimal | None = None
    delivery_weight_kg: Decimal | None = None
    weight_difference_kg: Decimal | None = None
