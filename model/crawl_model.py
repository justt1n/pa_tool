from pydantic import BaseModel
from enum import Enum


class Seller(BaseModel):
    name: str
    feedback_count: int


class TimeUnit(Enum):
    Hours = "Hours"
    Hour = "Hour"
    Minutes = "Minutes"
    Minute = "Minute"


class DeliveryTime(BaseModel):
    value: int
    unit: TimeUnit


class OfferItem(BaseModel):
    offer_id: str
    server: str
    seller: Seller
    delivery_time: DeliveryTime | None
    min_unit: int | None
    min_stock: int | None
    price: float | None
