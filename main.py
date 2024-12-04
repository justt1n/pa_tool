import codecs
import json
import os

from dotenv import load_dotenv

from utils.biji_extract import bij_lowest_price
from utils.ggsheet import GSheet, Sheet
from utils.logger import setup_logging
from model.payload import Row
from app.process import calculate_price_change, is_change_price, get_row_run_index
from utils.pa_extract import extract_offer_items
from app.login import login
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
        offer_items = extract_offer_items(row.product.PRODUCT_COMPARE)
        if is_change_price(row.product, offer_items):
            print(
                calculate_price_change(
                    gsheet, row, offer_items, BIJ_HOST_DATA, browser
                ).model_dump(mode="json")
            )



### MAIN ###

if __name__ == "__main__":
    BIJ_HOST_DATA = read_file_with_encoding(os.getenv('DATA_PATH'), encoding='utf-8')
    gsheet = GSheet()
    browser = SeleniumUtil()
    # login(browser)
    process(BIJ_HOST_DATA, gsheet, browser)

