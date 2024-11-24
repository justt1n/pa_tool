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

    def __to_seconds(self):
        if self.unit in [TimeUnit.Hour, TimeUnit.Hours]:
            return self.value * 60 * 60
        return self.value * 60

    def __gt__(self, orther: "DeliveryTime"):
        return self.__to_seconds() > orther.__to_seconds()

    def __lt__(self, orther: "DeliveryTime"):
        return self.__to_seconds() < orther.__to_seconds()

    def __ge__(self, orther: "DeliveryTime"):
        return self.__to_seconds() >= orther.__to_seconds()

    def __le__(self, orther: "DeliveryTime"):
        return self.__to_seconds() <= orther.__to_seconds()

    @staticmethod
    def from_text(
        txt: str,
    ) -> "DeliveryTime":
        # Remove duplicated white space
        while "  " in txt:
            txt = txt.replace("  ", " ")

        txt_splitted = txt.strip().split(" ")
        return DeliveryTime(
            value=int(txt_splitted[0]),
            unit=TimeUnit(txt_splitted[1]),
        )


class OfferItem(BaseModel):
    offer_id: str
    server: str
    seller: Seller
    delivery_time: DeliveryTime | None
    min_unit: int | None
    min_stock: int | None
    quantity: int | None
    price: float | None

    @staticmethod
    def min_offer_item(
        offer_items: list["OfferItem"],
    ) -> "OfferItem":
        min = offer_items[0]
        for offer_item in offer_items:
            if offer_item.price < min.price:  # type: ignore
                min = offer_item

        return min
