import codecs
import json
import os
import time
from datetime import datetime
from typing import List

from dotenv import load_dotenv
from gspread.utils import a1_to_rowcol

import constants
from QueryCurrency import CurrencyQueryItem
from QueryItem import ItemQueryItem
from app.login import login
from app.process import calculate_price_change, get_row_run_index
from decorator.retry import retry
from decorator.time_execution import time_execution
from model.crawl_model import OfferItem
from model.enums import StockType
from model.payload import Row, PriceInfo
from model.sheet_model import ExtraInfor
from utils.excel_util import CurrencyTemplate, currency_templates_to_dicts, item_templates_to_dicts, ItemTemplate, \
    create_file_from_template, clear_output_directory
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

@time_execution
@retry(5, delay=15, exception=PACrawlerError)
def process(
        BIJ_HOST_DATA: dict,
        gsheet: GSheet,
        browser_list: List[SeleniumUtil]
):
    print("process")
    browser = browser_list[0]
    normal_browser = browser_list[1]
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
            pa_blacklist = row.stock_info.get_pa_blacklist()
        except Exception as e:
            print(f"Error getting row: {e}")
            _current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            write_to_log_cell(worksheet, index, "Error: " + _current_time, log_type="time")
            continue
        if not isinstance(row, Row):
            continue
        offer_items = extract_offer_items(row.product.PRODUCT_COMPARE, normal_browser)
        sorted_offer_items = sorted(offer_items, key=lambda x: x.price)
        item_info, stock_fake_items = None, None
        if True:
            try:
                [item_info, stock_fake_items] = calculate_price_change(
                    gsheet, row, offer_items, BIJ_HOST_DATA, browser, pa_blacklist
                )
                if item_info is None:
                    print("No item info")
                    continue
            except Exception as e:
                print(f"Error calculating price change: {e}")
                continue
            row.extra = correct_extra_data(row.extra)
            final_stock = row.stock_info.cal_stock()
            if "SPECIAL" in row.product.Product_link:
                _id_list = row.extra.get_game_list()
                for _id in _id_list:
                    _data_info = create_data_from_str(_id)
                    if _data_info is None:
                        print(f"Error creating data from string: {_id}")
                        continue
                    elif isinstance(_data_info, CurrencyQueryItem):
                        _currency_info = _data_info
                        currency_template.append(
                            CurrencyTemplate(
                                game=_currency_info.Game,
                                server=_currency_info.Server,
                                faction=_currency_info.Faction,
                                currency_per_unit=row.extra.CURRENCY_PER_UNIT,
                                total_units=min(final_stock, 10000),
                                minimum_unit_per_order=row.extra.MIN_UNIT_PER_ORDER,
                                price_per_unit=float(
                                    f"{item_info.adjusted_price * float(row.extra.CURRENCY_PER_UNIT):.3f}"),
                                ValueForDiscount=row.extra.VALUE_FOR_DISCOUNT,
                                discount=row.extra.DISCOUNT,
                                title=row.product.TITLE,
                                duration=row.product.DURATION,
                                delivery_guarantee=row.extra.DELIVERY_GUARANTEE,
                                description=row.product.DESCRIPTION,
                            )
                        )
                    else:
                        _item_info = _data_info
                        item_template.append(
                            ItemTemplate(
                                game=_item_info.game,
                                server=_item_info.server,
                                faction=_item_info.faction,
                                item_category1=_item_info.item_category1,
                                item_category2=_item_info.item_category2,
                                item_category3=_item_info.item_category3,
                                item_per_unit=row.extra.CURRENCY_PER_UNIT,
                                unit_price=float(
                                    f"{item_info.adjusted_price * float(row.extra.CURRENCY_PER_UNIT):.2f}"),
                                min_unit_per_order=row.extra.MIN_UNIT_PER_ORDER,
                                ValueForDiscount=row.extra.VALUE_FOR_DISCOUNT,
                                discount=row.extra.DISCOUNT,
                                offer_duration=row.product.DURATION,
                                delivery_guarantee=row.extra.DELIVERY_GUARANTEE,
                                delivery_info='',
                                cover_image='',
                                title=row.product.TITLE,
                                description=row.product.DESCRIPTION,
                            )
                        )
            else:
                _data_info = create_data_from_str(row.product.Product_link)
                if _data_info is None:
                    print(f"Error creating data from string: {row.product.Product_link}")
                    continue
                if isinstance(_data_info, CurrencyQueryItem):
                    _currency_info = _data_info
                    currency_template.append(
                        CurrencyTemplate(
                            game=_currency_info.Game,
                            server=_currency_info.Server,
                            faction=_currency_info.Faction,
                            currency_per_unit=row.extra.CURRENCY_PER_UNIT,
                            total_units=min(final_stock, 9999),
                            minimum_unit_per_order=row.extra.MIN_UNIT_PER_ORDER,
                            price_per_unit=float(f"{item_info.adjusted_price * float(row.extra.CURRENCY_PER_UNIT):.3f}"),
                            ValueForDiscount=row.extra.VALUE_FOR_DISCOUNT,
                            discount=row.extra.DISCOUNT,
                            title=row.product.TITLE,
                            duration=row.product.DURATION,
                            delivery_guarantee=row.extra.DELIVERY_GUARANTEE,
                            description=row.product.DESCRIPTION,
                        )
                    )
                else:
                    _item_info = _data_info
                    item_template.append(
                        ItemTemplate(
                            game=_item_info.game,
                            server=_item_info.server,
                            faction=_item_info.faction,
                            item_category1=_item_info.item_category1,
                            item_category2=_item_info.item_category2,
                            item_category3=_item_info.item_category3,
                            item_per_unit=row.extra.CURRENCY_PER_UNIT,
                            unit_price=float(f"{item_info.adjusted_price * float(row.extra.CURRENCY_PER_UNIT):.2f}"),
                            total_units=min(final_stock, 9999),
                            min_unit_per_order=row.extra.MIN_UNIT_PER_ORDER,
                            ValueForDiscount=row.extra.VALUE_FOR_DISCOUNT,
                            discount=row.extra.DISCOUNT,
                            offer_duration=row.product.DURATION,
                            delivery_guarantee=row.extra.DELIVERY_GUARANTEE,
                            delivery_info='',
                            cover_image='',
                            title=row.product.TITLE,
                            description=row.product.DESCRIPTION,
                        )
                    )
            print(f"Price change:\n{item_info.model_dump(mode='json')}")
            log_str = ""
            for offer_item in offer_items:
                if not offer_item.seller.canGetFeedback:
                    log_str += f"Can't get feedback from {offer_item.seller.name}\n"
            log_str += get_update_str(sorted_offer_items[0], item_info, stock_fake_items, row.product.DONGIA_LAMTRON)
            log_str += get_top_pa_offers_str(sorted_offer_items, sorted_offer_items[0], row.product.DONGIA_LAMTRON)
            write_to_log_cell(worksheet, index, log_str)
            _current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            write_to_log_cell(worksheet, index, _current_time, log_type="time")
        # else:
        #     print("No valid offer item")
        #     _current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S") + "\nNo valid offer item\n"
        #     write_to_log_cell(worksheet, index, _current_time, log_type="time")
        try:
            __time_sleep = float(os.getenv("TIME_SLEEP_ROW"))
        except Exception:
            print("No time sleep each row (add TIME_SLEEP_ROW to settings file), set default to ")
            __time_sleep = 0
        print(f"Sleeping for {__time_sleep} seconds")
        time.sleep(__time_sleep)
        print("Next row...")
    currency_template = currency_templates_to_dicts(currency_template)
    is_have_item = False
    if len(item_template) > 0:
        is_have_item = True
        item_template = item_templates_to_dicts(item_template)
    clear_output_directory("storage/output/item")
    clear_output_directory("storage/output/currency")
    create_file_from_template("currency_template.xlsx", "storage/output/currency/new_currency_file.xlsx",
                              currency_template)
    create_file_from_template("item_template.xlsx", "storage/output/item/new_item_file.xlsx",
                              item_template)
    print("Create file successfully, check storage/output folder")

    try:
        normal_browser = SeleniumUtil(mode=1)
        upload_data_to_site(normal_browser, is_have_item)
    except Exception as _e:
        raise PACrawlerError(f"Error uploading data to site: {_e}")


def correct_extra_data(extra: ExtraInfor) -> ExtraInfor:
    if extra.VALUE_FOR_DISCOUNT is None:
        extra.VALUE_FOR_DISCOUNT = ""
    if extra.DISCOUNT is None:
        extra.DISCOUNT = ""
    return extra


def create_data_from_str(s: str) -> CurrencyQueryItem | ItemQueryItem | None:
    s = s.split(",")
    if len(s) == 0:
        raise Exception("Empty string")
    elif len(s) == 3:
        return CurrencyQueryItem(
            ID="",
            Game=s[0],
            Server=s[1],
            Faction=s[2],
        )
    elif len(s) == 6:
        return ItemQueryItem(
            ID="",
            game=s[0],
            server=s[1],
            faction=s[2],
            item_category1=s[3],
            item_category2=s[4],
            item_category3=s[5]
        )
    return None


def upload_data_to_site(browser: SeleniumUtil, isHaveItem: bool):
    login(browser, isHaveItem)


### LOG FUNC ###
def get_top_pa_offers_str(
        sorted_offer_items: list[OfferItem]
        , offer_item: OfferItem
        , round_num
) -> str:
    _str = "Top 3 PA offers:\n"
    for i, item in enumerate(sorted_offer_items[:3]):
        if i == 0:
            _str += f"{i + 1}: {item.seller.name}: {round(item.price / offer_item.quantity, round_num):.{round_num}f}\n"
            continue
        _str += f"{i + 1}: {item.seller.name}: {round(item.price / offer_item.quantity, round_num):.{round_num}f}\n"
    return _str


def get_update_str(offer_item: OfferItem, item_info: PriceInfo, stock_fake_items: list, round_num) -> str:
    quantity = offer_item.quantity
    if item_info is None:
        return "No update\n"
    _current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    _str = f"Cập nhật thành công {round(item_info.adjusted_price, round_num):.{round_num}f} lúc {_current_time} theo seller: {item_info.ref_seller}\n"

    if item_info.stock_type is StockType.stock_1:
        _str += f"Stocktype=stock_1: {item_info.stock_num_info.stock_1}\n"
    elif item_info.stock_type is StockType.stock_2:
        _str += f"Stocktype=stock_2: {item_info.stock_num_info.stock_2}\n"
    else:
        _str += f"Stocktype=stock_fake: {item_info.stock_num_info.stock_fake}\n"

    if stock_fake_items is None:
        _price_min_formatted = f"{item_info.price_min:.{round_num}f}"
        _price_max_formatted = f"{item_info.price_mac:.{round_num}f}"
        _str += f"PriceMin = {_price_min_formatted}, PriceMax = {_price_max_formatted},\n"
        return _str + "\n"
    if stock_fake_items:
        _pmin = item_info.price_min
        _pmax = item_info.price_mac
        if int(item_info.price_min) == -1:
            _pmin = "Cant get price"
        if int(item_info.price_mac) == -1:
            _pmax = "Cant get price"
        _str += f"PriceMin = {_pmin}, PriceMax = {_pmax}, \n"
        if stock_fake_items[0] is not None:
            _str += f"\nMin G2G: {stock_fake_items[0][1]} = {stock_fake_items[0][0]}, \n"
        else:
            _str += "\nMin G2G: no matching seller\n"
        if stock_fake_items[1] is not None:
            _str += f"Min FUN: {stock_fake_items[1][1]} = {stock_fake_items[1][0]}, \n"
        else:
            _str += "Min FUN: no matching seller\n"
        if stock_fake_items[2] is not None:
            _str += f"Min BIJ: {stock_fake_items[2][1]} = {stock_fake_items[2][0]}, \n"
        else:
            _str += "Min BIJ: no matching seller\n"
        if stock_fake_items[3] is not None:
            _str += f"Min DD: {stock_fake_items[3][1]} = {stock_fake_items[3][0]}, \n"
        else:
            _str += "Min DD: no matching seller\n"
        if stock_fake_items[4] is not None:
            _str += f"Min SheetPrice1: {stock_fake_items[4][1]} = {stock_fake_items[4][0]}, \n"
        else:
            _str += "Min SheetPrice1: no matching seller\n"
        if stock_fake_items[5] is not None:
            _str += f"Min SheetPrice2: {stock_fake_items[5][1]} = {stock_fake_items[5][0]}, \n"
        else:
            _str += "Min SheetPrice2: no matching seller\n"
        if stock_fake_items[6] is not None:
            _str += f"Min SheetPrice3: {stock_fake_items[6][1]} = {stock_fake_items[6][0]}, \n"
        else:
            _str += "Min SheetPrice3: no matching seller\n"
        if stock_fake_items[7] is not None:
            _str += f"Min SheetPrice4: {stock_fake_items[7][1]} = {stock_fake_items[7][0]}, \n"
        else:
            _str += "Min SheetPrice4: no matching seller\n"

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
            r, c = a1_to_rowcol(f"D{row_index}")
        if log_type == "time":
            r, c = a1_to_rowcol(f"E{row_index}")
        if log_type == "error":
            r, c = a1_to_rowcol(f"CK{row_index}")
        worksheet.update_cell(r, c, log_str)
    except Exception as e:
        print(f"Error writing to log cell: {e}")


### MAIN ###

if __name__ == "__main__":
    print("Starting...")
    BIJ_HOST_DATA = read_file_with_encoding(constants.DATA_PATH, encoding='utf-8')
    gsheet = GSheet(constants.KEY_PATH)
    headless_browser = SeleniumUtil(mode=2)
    normal_browser = SeleniumUtil(mode=1)
    normal_browser.driver.minimize_window()
    browser_list = [headless_browser, normal_browser]
    while True:
        try:
            process(BIJ_HOST_DATA, gsheet, browser_list)
            try:
                _time_sleep = float(os.getenv("TIME_SLEEP"))
            except Exception:
                print("No time sleep (TIME_SLEEP), set default to 2")
                _time_sleep = 2
            print(f"Sleeping for {_time_sleep} seconds")
            time.sleep(_time_sleep)
            # test_browser = SeleniumUtil(mode=1)
            # login(test_browser, False)
        except Exception as e:
            _str_error = f"Error: {e}"
            sheet = Sheet.from_sheet_id(
                gsheet=gsheet,
                sheet_id=os.getenv("SPREADSHEET_ID"),  # type: ignore
            )
            worksheet = sheet.open_worksheet(os.getenv("SHEET_NAME"))  # type: ignore
            _current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            write_to_log_cell(worksheet, 2, f"Error on: {_current_time}" + _str_error, log_type="error")
        print("Done")
