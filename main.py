import codecs
import json
import os
from datetime import datetime

from dotenv import load_dotenv
from gspread.utils import a1_to_rowcol

import constants
from QueryCurrency import query_currency
from QueryItem import query_item
from app.login import login
from app.process import calculate_price_change, is_change_price, get_row_run_index
from decorator.retry import retry
from model.crawl_model import OfferItem
from model.payload import Row, PriceInfo
from model.sheet_model import ExtraInfor
from utils.excel_util import CurrencyTemplate, currency_templates_to_dicts, item_templates_to_dicts, ItemTemplate, \
    create_file_from_template
from utils.exceptions import PACrawlerError
from utils.ggsheet import GSheet, Sheet
from utils.logger import setup_logging
from utils.pa_extract import extract_offer_items
from utils.selenium_util import SeleniumUtil

### SETUP ###
load_dotenv("settings.env")

setup_logging()
gs = GSheet()


### FUNCTIONS ###
def read_file_with_encoding(file_path, encoding='utf-8'):
    try:
        with codecs.open(file_path, 'r', encoding=encoding) as file:
            content = json.load(file)
        return content
    except UnicodeDecodeError as e:
        print(f"Error decoding file: {e}")
        return None


# def getCNYRate(gs: GSheet) -> float:
#     try:
#         _rate_sheet = os.getenv("CNY_RATE_SPREADSHEET_ID")
#         _rate_worksheet = os.getenv("CNY_RATE_SHEET_NAME")
#         _cell = os.getenv("CNY_RATE_CELL")
#         return gs.load_cell_value(_rate_sheet, _rate_worksheet, _cell)
#     except Exception as e:
#         print(f"Error reading CNY rate: {e}")
#         return 1


@retry(10, delay=30, exception=PACrawlerError)
def process(
        BIJ_HOST_DATA: dict,
        gsheet: GSheet,
        browser: SeleniumUtil
):
    print("process")
    try:
        sheet = Sheet.from_sheet_id(
            gsheet=gsheet,
            sheet_id=os.getenv("SPREADSHEET_ID"),  # type: ignore
        )
    except Exception as e:
        print(f"Error getting sheet: {e}")
        return
    try:
        worksheet = sheet.open_worksheet(os.getenv("SHEET_NAME"))  # type: ignore
    except Exception as e:
        print(f"Error getting worksheet: {e}")
        return
    row_indexes = get_row_run_index(worksheet=worksheet)

    currency_template = []
    item_template = []

    for index in row_indexes:
        print(f"Row: {index}")
        try:
            row = Row.from_row_index(worksheet, index)
        except Exception as e:
            print(f"Error getting row: {e}")
            _current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            write_to_log_cell(worksheet, index, _current_time, log_type="time")
            continue
        if not isinstance(row, Row):
            continue
        offer_items = extract_offer_items(row.product.PRODUCT_COMPARE)
        sorted_offer_items = sorted(offer_items, key=lambda x: x.price)
        item_info, stock_fake_items = None, None
        if is_change_price(row.product, offer_items):
            try:
                [item_info, stock_fake_items] = calculate_price_change(
                    gsheet, row, offer_items, BIJ_HOST_DATA, browser
                )
            except Exception as e:
                print(f"Error calculating price change: {e}")
                continue
            row.extra = correct_extra_data(row.extra)
            final_stock = row.stock_info.cal_stock()
            if "C" in row.product.Product_link:
                _currency_info = query_currency("storage/joined_data.db", row.product.Product_link)
                currency_template.append(
                    CurrencyTemplate(
                        game=_currency_info.Game,
                        server=_currency_info.Server,
                        faction=_currency_info.Faction,
                        currency_per_unit=sorted_offer_items[0].quantity,
                        total_units=final_stock,
                        minimum_unit_per_order=row.extra.MIN_UNIT_PER_ORDER,
                        price_per_unit=round(item_info.adjusted_price / sorted_offer_items[0].quantity, 4),
                        ValueForDiscount=row.extra.VALUE_FOR_DISCOUNT,
                        discount=row.extra.DISCOUNT,
                        title=row.product.TITLE,
                        duration=row.product.DURATION,
                        delivery_guarantee=row.extra.DELIVERY_GUARANTEE,
                        description=row.product.DESCRIPTION,
                    )
                )
            else:
                _item_info = query_item("storage/joined_data.db", row.product.Product_link)
                item_template.append(
                    ItemTemplate(
                        game=_item_info.game,
                        server=_item_info.server,
                        faction=_item_info.faction,
                        item_category1=_item_info.item_category1,
                        item_category2=_item_info.item_category2,
                        item_category3=_item_info.item_category3,
                        item_per_unit=sorted_offer_items[0].quantity,
                        unit_price=round(item_info.adjusted_price / sorted_offer_items[0].quantity, 4),
                        min_unit_per_order=row.extra.MIN_UNIT_PER_ORDER,
                        ValueForDiscount=row.extra.VALUE_FOR_DISCOUNT,
                        discount=row.extra.DISCOUNT,
                        offer_duration=row.product.DURATION,
                        delivery_guarantee=row.extra.DELIVERY_GUARANTEE,
                        delivery_info=row.extra.DELIVERY_INFO,
                        cover_image=row.extra.COVER_IMAGE,
                        title=row.product.TITLE,
                        description=row.product.DESCRIPTION,
                    )
                )

            print(f"Price change:\n{item_info.model_dump(mode='json')}")
            log_str = ""
            log_str += get_update_str(sorted_offer_items[0], item_info, stock_fake_items)
            log_str += get_top_pa_offers_str(sorted_offer_items, sorted_offer_items[0])
            write_to_log_cell(worksheet, index, log_str)
            _current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            write_to_log_cell(worksheet, index, _current_time, log_type="time")
        print("Next row...")
    currency_template = currency_templates_to_dicts(currency_template)
    item_template = item_templates_to_dicts(item_template)
    create_file_from_template("currency_template.xlsx", "storage/output/new_currency_file.xlsx",
                              currency_template)
    create_file_from_template("item_template.xlsx", "storage/output/new_item_file.xlsx", item_template)
    print("Create file successfully, check storage/output folder")
    raise PACrawlerError("Limit reached, retrying after 30s...")


def correct_extra_data(extra: ExtraInfor) -> ExtraInfor:
    if extra.VALUE_FOR_DISCOUNT is None:
        extra.VALUE_FOR_DISCOUNT = ""
    if extra.DISCOUNT is None:
        extra.DISCOUNT = ""
    return extra


def upload_data_to_site(browser: SeleniumUtil):
    login(browser)





### LOG FUNC ###
def get_top_pa_offers_str(
        sorted_offer_items: list[OfferItem]
        , offer_item: OfferItem) -> str:
    _str = "Top 3 PA offers:\n"
    for i, item in enumerate(sorted_offer_items[:3]):
        _str += f"{i + 1}: {item.seller.name}: {item.price} ({round(item.price / offer_item.quantity, 4)})\n"
    return _str


def get_update_str(offer_item: OfferItem, item_info: PriceInfo, stock_fake_items: list) -> str:
    quantity = offer_item.quantity
    if item_info is None:
        return "No update\n"
    _current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    _str = f"Cập nhật thành công {item_info.adjusted_price} lúc {_current_time}\n"
    _str += f"Đơn giá cập nhật: {round(item_info.adjusted_price / quantity, 4)}\n"
    _str += f"PriceMax = {item_info.price_mac} ({item_info.price_mac/quantity}), PriceMin = {item_info.price_min} ({item_info.price_min/quantity}), \n"
    _str += f"{item_info.stock_type}, "
    if stock_fake_items is None:
        return _str + "\n"
    if stock_fake_items:
        if stock_fake_items[0] is not None:
            _str += f"\nMin G2G: {stock_fake_items[0][1]} = {stock_fake_items[0][0]} ({stock_fake_items[0][0] / quantity}), \n"
        else:
            _str += "\nMin G2G: no matching seller\n"
        if stock_fake_items[1] is not None:
            _str += f"Min FUN: {stock_fake_items[1][1]} = {stock_fake_items[1][0]} ({stock_fake_items[1][0] / quantity}), \n"
        else:
            _str += "Min FUN: no matching seller\n"
        if stock_fake_items[2] is not None:
            _str += f"Min BIJ: {stock_fake_items[2][1]} = {stock_fake_items[2][0]} ({stock_fake_items[2][0] / quantity}), \n"
        else:
            _str += "Min BIJ: no matching seller\n"
    return _str + "\n"


def write_to_log_cell(
        worksheet,
        row_index,
        log_str,
        log_type="log"
):
    try:
        r, c = None, None
        if log_type == "log":
            r, c = a1_to_rowcol(f"C{row_index}")
        if log_type == "time":
            r, c = a1_to_rowcol(f"D{row_index}")
        worksheet.update_cell(r, c, log_str)
    except Exception as e:
        print(f"Error writing to log cell: {e}")


### MAIN ###

if __name__ == "__main__":
    BIJ_HOST_DATA = read_file_with_encoding(constants.DATA_PATH, encoding='utf-8')
    gsheet = GSheet(constants.KEY_PATH)
    normal_browser = SeleniumUtil(mode=1)
    headless_browser = SeleniumUtil(mode=2)
    while True:
        process(BIJ_HOST_DATA, gsheet, headless_browser)
        # upload_data_to_site(normal_browser)
        print("Done")