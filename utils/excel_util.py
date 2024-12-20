import codecs
import os
from typing import List, Dict

import pandas as pd
from pydantic import BaseModel

from constants import TEMPLATE_FOLDER


class CurrencyTemplate(BaseModel):
    action: str = "Sell"
    game: str
    server: str
    faction: str
    currency_per_unit: float
    total_units: float
    minimum_unit_per_order: float
    price_currency: str = "USD"
    price_per_unit: float
    ValueForDiscount: str
    discount: str
    title: str
    duration: int
    delivery_guarantee: int
    delivery_method: str = "Face to Face"
    delivery_character: str = ""
    delivery_instructions: str = ""
    description: str

    class Config:
        arbitrary_types_allowed = True


class ItemTemplate(BaseModel):
    game: str
    server: str
    faction: str
    item_category1: str
    item_category2: str
    item_category3: str
    item_per_unit: float
    unit_price: float
    min_unit_per_order: float
    price_currency: str = "USD"
    ValueForDiscount: float
    discount: float
    offer_duration: int
    delivery_guarantee: int
    delivery_info: str
    cover_image: str
    title: str
    description: str

    class Config:
        arbitrary_types_allowed = True


def currency_templates_to_dicts(templates: List[CurrencyTemplate]) -> List[Dict[str, any]]:
    return [template.dict() for template in templates]


def item_templates_to_dicts(templates: List[ItemTemplate]) -> List[Dict[str, any]]:
    return [template.dict() for template in templates]


def load_template(template_name: str) -> str:
    template_path = os.path.join(TEMPLATE_FOLDER, template_name)
    with codecs.open(template_path, 'r', encoding='utf-8', errors='ignore') as file:
        template_content = file.read()
    return template_content


def write_template_to_file(file_path: str, template_content: str):
    with open(file_path, 'w') as file:
        file.write(template_content)


def write_data_to_xlsx(file_path: str, data: List[Dict[str, any]]):
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)


def create_file_from_template(template_name: str, new_file_path: str, data: List[Dict[str, any]]):
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)

    template_content = load_template(template_name)
    write_template_to_file(new_file_path, template_content)
    write_data_to_xlsx(new_file_path, data)


def read_xlsx_file(file_path: str) -> List[Dict[str, any]]:
    df = pd.read_excel(file_path)
    return df.to_dict(orient='records')


def write_xlsx_file(file_path: str, data: List[Dict[str, any]]):
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)
    return True


def sample_usage():
    currency_templates = [
        CurrencyTemplate(game="OK", server="US", faction="Horde", currency_per_unit=1000, total_units=1000,
                         minimum_unit_per_order=100, price_per_unit=0.1, ValueForDiscount="USD", discount="5%",
                         title="Sell WoW Gold", duration=24, delivery_guarantee=24, description="Sell WoW Gold"),
        CurrencyTemplate(game="CHUa", server="US", faction="Alliance", currency_per_unit=1000, total_units=1000,
                         minimum_unit_per_order=100, price_per_unit=0.1, ValueForDiscount="USD", discount="5%",
                         title="Sell WoW Gold", duration=24, delivery_guarantee=24, description="Sell WoW Gold"),
    ]

    item_templates = [
        ItemTemplate(game="WoW", server="US", faction="Horde", item_category1="Item1", item_category2="Item2",
                     item_category3="Item3", item_per_unit=100, unit_price=0.1, min_unit_per_order=10,
                     ValueForDiscount=0.1, discount=0.05, offer_duration=24, delivery_guarantee=24,
                     delivery_info="Face to Face", cover_image="cover.jpg", title="Sell WoW Item",
                     description="Sell WoW Item"),
        ItemTemplate(game="WoW", server="US", faction="Alliance", item_category1="Item1", item_category2="Item2",
                     item_category3="Item3", item_per_unit=100, unit_price=0.1, min_unit_per_order=10,
                     ValueForDiscount=0.1, discount=0.05, offer_duration=24, delivery_guarantee=24,
                     delivery_info="Face to Face", cover_image="cover.jpg", title="Sell WoW Item",
                     description="Sell WoW Item"),
    ]

    currency_data = currency_templates_to_dicts(currency_templates)
    item_data = item_templates_to_dicts(item_templates)

    create_file_from_template("currency_template.xlsx", "storage/pa_template/new_currency_template.xlsx", currency_data)
    create_file_from_template("item_template.xlsx", "storage/pa_template/new_item_template.xlsx", item_data)
