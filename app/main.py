import codecs
import json
import os
import platform
import time
import zipfile
from datetime import datetime

import gspread
import wget

from model.payload import Product
from utils.ggsheet import GSheet
from utils.logger import setup_logging
from dotenv import load_dotenv
from decorator.time_execution import time_execution
from decorator.retry import retry


### SETUP ###
load_dotenv('settings.env')

setup_logging()
gs = GSheet()

### FUNCTIONS ###

def row_to_product(row: list) -> Product:
    """
    Hàm chuyển một dòng dữ liệu (row) thành đối tượng Product.

    :param row: Một danh sách chứa dữ liệu của một dòng trong Google Sheet.
    :return: Một đối tượng Product.
    """
    product_data = {}

    # Kiểm tra ánh xạ dữ liệu từ row vào các thuộc tính của Product
    for index, value in enumerate(row):
        if index < len(Product.__annotations__):  # Bảo đảm không vượt quá số thuộc tính trong class
            field_name = list(Product.__annotations__.keys())[index]
            # Gán giá trị hoặc None nếu ô trống
            product_data[field_name] = value if value != '' else None

    return Product(**product_data)

def get_payload():
    print("getting payload")
    data = gs.read_sheet_data(os.getenv('SHEET_NAME'))
    data.pop(0)
    payload = row_to_product(data)
    return payload


def do_payload(payload: Product):
    print("doing payload")
    print(payload)
    # Do something with payload


def process ():
    print('process')
    payloads = get_payload()
    print(payloads)
    for payload in payloads:
        do_payload(payload)

### MAIN ###

if __name__ == '__main__':
    process()