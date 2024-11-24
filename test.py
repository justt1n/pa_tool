from utils.pa_extract import extract_offer_items
from utils.ggsheet import (
    GSheet,
    Sheet,
    query_model_from_worksheet,
    update_model_to_worksheet,
)
from model.sheet_model import Product, StockInfo, G2G, FUN, BIJ


def test():
    gsheet = GSheet()

    sheet = Sheet.from_sheet_id(gsheet, "1ckkWEa7xbOdFKbdqGxVkpVpMm1RG6dljmigitzeN7jc")
    sheet1 = sheet.open_worksheet("Sheet1")
    index_row = [4, 5]
    models = query_model_from_worksheet(sheet1, Product, index_row)
    print([model.model_dump(mode="json") for model in models])
    models[0].CHECK = 1
    models[1].CHECK = 1

    update_model_to_worksheet(sheet1, models)


if __name__ == "__main__":
    test()
