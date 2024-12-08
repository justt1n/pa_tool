import codecs
import json
import os
from datetime import datetime

from dotenv import load_dotenv

from app.process import calculate_price_change, is_change_price, get_row_run_index
from model.crawl_model import OfferItem
from model.payload import Row, PriceInfo
from utils.ggsheet import GSheet, Sheet
from utils.logger import setup_logging
from utils.pa_extract import extract_offer_items
from utils.selenium_util import SeleniumUtil
from gspread.utils import a1_to_rowcol

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


def process(
        BIJ_HOST_DATA: dict,
        gsheet: GSheet,
        browser: SeleniumUtil
):
    print("process")
    sheet = Sheet.from_sheet_id(
        gsheet=gsheet,
        sheet_id=os.getenv("SPREADSHEET_ID"),  # type: ignore
    )
    worksheet = sheet.open_worksheet(os.getenv("SHEET_NAME"))  # type: ignore
    row_indexes = get_row_run_index(worksheet=worksheet)
    for index in row_indexes:
        print(f"Row: {index}")
        row = Row.from_row_index(worksheet, index)
        if not isinstance(row, Row):
            continue
        offer_items = extract_offer_items(row.product.PRODUCT_COMPARE)
        sorted_offer_items = sorted(offer_items, key=lambda x: x.price)
        item_info, stock_fake_items = None, None
        if is_change_price(row.product, offer_items):
            [item_info, stock_fake_items] = calculate_price_change(
                gsheet, row, offer_items, BIJ_HOST_DATA, browser
            )
            print(f"Price change:\n{item_info.model_dump(mode="json")}")
        log_str = ""
        log_str += get_update_str(item_info, stock_fake_items)
        log_str += get_top_pa_offers_str(sorted_offer_items)
        write_to_log_cell(worksheet, index, log_str)
        _current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        write_to_log_cell(worksheet, index, _current_time, log_type="time")
        print("Next row...")


### LOG FUNC ###
def get_top_pa_offers_str(
        sorted_offer_items: list[OfferItem]
) -> str:
    _str = "Top 3 PA offers:\n"
    for i, item in enumerate(sorted_offer_items[:3]):
        _str += f"{i + 1}: {item.seller.name}: {item.price}\n"
    return _str


def get_update_str(item_info: PriceInfo, stock_fake_items: list) -> str:
    if item_info is None:
        return "No update\n"
    _current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    _str = f"Cập nhật thành công {item_info.adjusted_price} lúc {_current_time} "
    _str += f"PriceMax = {item_info.price_mac}, PriceMin = {item_info.price_min}, "
    _str += f"{item_info.stock_type}, "
    if stock_fake_items is None:
        return _str + "\n"
    if stock_fake_items:
        if stock_fake_items[0] is not None:
            _str += f"Min G2G: {stock_fake_items[0][1]}={stock_fake_items[0][0]}, "
        if stock_fake_items[1] is not None:
            _str += f"Min FUN: {stock_fake_items[1][1]}={stock_fake_items[1][0]}, "
        if stock_fake_items[2] is not None:
            _str += f"Min BIJ: {stock_fake_items[2][1]}={stock_fake_items[2][0]}, "
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
    BIJ_HOST_DATA = read_file_with_encoding(os.getenv('DATA_PATH'), encoding='utf-8')
    gsheet = GSheet()
    # normal_browser = SeleniumUtil(mode=1)
    headless_browser = SeleniumUtil(mode=2)
    process(BIJ_HOST_DATA, gsheet, headless_browser)
