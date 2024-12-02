import re

from pydantic import BaseModel
from enum import Enum
from .sheet_model import G2G


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
    delivery_time: DeliveryTime
    min_unit: int
    min_stock: int
    quantity: int
    price: float

    @staticmethod
    def min_offer_item(
            offer_items: list["OfferItem"],
    ) -> "OfferItem":
        min = offer_items[0]
        for offer_item in offer_items:
            if offer_item.price < min.price:  # type: ignore
                min = offer_item

        return min


class G2GOfferItem(BaseModel):
    seller_name: str
    delivery_time: DeliveryTime
    stock: int
    min_purchase: int
    price_per_unit: float

    def is_valid(
            self,
            g2g: G2G,
            g2g_blacklist: list[str],
    ) -> bool:
        if self.seller_name in g2g_blacklist:
            return False

        if self.delivery_time.value > g2g.G2G_DELIVERY_TIME:
            return False

        if self.stock < g2g.G2G_STOCK:
            return False

        if self.min_purchase > g2g.G2G_MINUNIT:
            return False

        return True

    @staticmethod
    def filter_valid_g2g_offer_item(
            g2g: G2G,
            g2g_offer_items: list["G2GOfferItem"],
            g2g_blacklist: list[str],
    ) -> list["G2GOfferItem"]:
        valid_g2g_offer_items = []
        for g2g_offer_item in g2g_offer_items:
            if g2g_offer_item.is_valid(g2g, g2g_blacklist):
                valid_g2g_offer_items.append(g2g_offer_item)

        return valid_g2g_offer_items

    @staticmethod
    def min_offer_item(
            g2g_offer_items: list["G2GOfferItem"],
    ) -> "G2GOfferItem":
        min = g2g_offer_items[0]
        for g2g_offer_item in g2g_offer_items:
            if g2g_offer_item.price_per_unit < min.price_per_unit:
                min = g2g_offer_item

        return min


def extract_integers_from_string(s):
    return [int(num) for num in re.findall(r'\d+', s)]


class BijOfferItem(BaseModel):
    username: str
    money: float
    gold: list
    min_gold: int
    max_gold: int
    dept: str
    time: str
    link: str
    type: str
