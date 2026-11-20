from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    unit: str
    stream: str
    allows_zero_or_negative_price: bool
    expiry_hours: int | None = None
    is_active: bool
