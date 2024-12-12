import os
from typing import List, Dict

import openpyxl

from constants import TEMPLATE_FOLDER
from model.payload import PriceInfo


def read_xlsx_file(file_path: str) -> List[Dict[str, any]]:
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active
    data = []

    headers = [cell.value for cell in sheet[1]]
    for row in sheet.iter_rows(min_row=2, values_only=True):
        row_data = {headers[i]: row[i] for i in range(len(headers))}
        data.append(row_data)

    return data


def write_xlsx_file(file_path: str, data: List[Dict[str, any]]):
    workbook = openpyxl.Workbook()
    sheet = workbook.active

    if not data:
        workbook.save(file_path)
        return

    headers = data[0].keys()
    sheet.append(list(headers))

    for row_data in data:
        sheet.append(list(row_data.values()))

    workbook.save(file_path)
    return True


def create_row_to_write(item: PriceInfo) -> Dict[str, any]:
    return {
        "name": item.name,
        "price": item.price,
        "stock": item.stock,
        "delivery_time": item.delivery_time,
        "min_unit": item.min_unit,
        "seller": item.seller,
    }


def load_template(template_name):
    template_path = os.path.join(TEMPLATE_FOLDER, template_name)
    with open(template_path, 'r') as file:
        template_content = file.read()
    return template_content
