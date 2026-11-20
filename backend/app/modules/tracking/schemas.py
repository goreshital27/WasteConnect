from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TrackingPositionCreate(BaseModel):
    lat: Decimal = Field(..., ge=-90, le=90, description="Latitude")
    lng: Decimal = Field(..., ge=-180, le=180, description="Longitude")


class TrackingPositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_id: UUID
    lat: Decimal
    lng: Decimal
    updated_at: datetime
