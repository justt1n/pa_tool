import random
import gspread
from typing import Any

from utils.biji_extract import bij_lowest_price
from utils.ggsheet import (
    GSheet,
    Sheet,
)
from utils.sheet_operator import (
    query_model_from_worksheet,
    update_model_to_worksheet,
    query_multi_model_from_worksheet,
)
from utils.pa_extract import extract_offer_items
from utils.g2g_extract import g2g_extract_offer_items
from utils.fun_extract import fun_extract_offer_items
from utils.biji_extract import bij_lowest_price
from model.sheet_model import G2G, Product, StockInfo, FUN, BIJ
from model.crawl_model import G2GOfferItem, OfferItem, DeliveryTime, FUNOfferItem
from model.payload import PriceInfo, Row
from model.enums import StockType


def get_row_run_index(
    worksheet: gspread.worksheet.Worksheet,
    col_check_index: int = 1,
    value_check: Any = "1",
) -> list[int]:
    row_indexes: list[int] = []
    for i, row_value in enumerate(worksheet.col_values(col_check_index), start=1):
        if row_value == value_check:
            row_indexes.append(i)

    return row_indexes


def is_valid_offer_item(
    product: Product,
    offer_item: OfferItem,
) -> bool:
    product_delivery_time = DeliveryTime.from_text(product.DELIVERY_TIME)
    if (
        offer_item.delivery_time is None
        or offer_item.delivery_time > product_delivery_time
    ):
        return False
    if offer_item.seller.feedback_count < product.FEEDBACK:
        return False
    if offer_item.min_unit is None or offer_item.min_unit > product.MIN_UNIT:
        return False
    if offer_item.min_stock is None or offer_item.min_stock < product.MINSTOCK:
        return False

    return True


def filter_valid_offer_items(
    product: Product,
    offer_items: list[OfferItem],
) -> list[OfferItem]:
    return [
        offer_item
        for offer_item in offer_items
        if is_valid_offer_item(product, offer_item)
    ]


def is_offer_items_contain_my_name() -> bool:
    # TODO:
    return False


def is_change_price(
    product: Product,
    offer_items: list[OfferItem],
) -> bool:
    if is_offer_items_contain_my_name():
        return False

    if product.EXCLUDE_ADS == 0:  # TODO:
        return False

    filtered_offer_items = filter_valid_offer_items(product, offer_items)
    if len(filtered_offer_items) == 0:
        return False

    return True


def identify_stock(
    gsheet: GSheet,
    stock_info: StockInfo,
) -> StockType:
    if stock_info.stock_1(gsheet) >= stock_info.STOCK_LIMIT:
        return StockType.stock_1
    if stock_info.stock_2(gsheet) >= stock_info.STOCK_LIMIT2:
        return StockType.stock_2
    return StockType.stock_fake


def calculate_price_stock_fake(
    gsheet: GSheet,
    row: Row,
    quantity: int,
):
    g2g_min_price = None
    if row.g2g.G2G_CHECK == 1:
        g2g_offer_items = g2g_extract_offer_items(row.g2g.G2G_PRODUCT_COMPARE)
        filtered_g2g_offer_items = G2GOfferItem.filter_valid_g2g_offer_item(
            g2g=row.g2g,
            g2g_blacklist=row.g2g.get_blacklist(gsheet),
            g2g_offer_items=g2g_offer_items,
        )
        if filtered_g2g_offer_items:
            g2g_min_offer_item = G2GOfferItem.min_offer_item(filtered_g2g_offer_items)
            g2g_min_price = (
                g2g_min_offer_item.price_per_unit * quantity * row.g2g.G2G_PROFIT
            )
            print(f"G2G min price: {g2g_min_price}")

    fun_min_price = None
    if row.fun.FUN_CHECK == 1:
        fun_offer_items = fun_extract_offer_items(
            row.fun.FUN_PRODUCT_COMPARE,
            [
                i
                for i in [
                    row.fun.FUN_FILTER21,
                    row.fun.FUN_FILTER22,
                    row.fun.FUN_FILTER23,
                    row.fun.FUN_FILTER24,
                ]
                if i is not None
            ],
        )
        filtered_fun_offer_items = FUNOfferItem.filter_valid_fun_offer_items(
            fun=row.fun,
            fun_offer_items=fun_offer_items,
            fun_blacklist=row.fun.get_blacklist(gsheet),
        )
        if filtered_fun_offer_items:
            fun_min_offer_item = FUNOfferItem.min_offer_item(filtered_fun_offer_items)
            fun_min_price = (
                fun_min_offer_item.price
                * row.fun.FUN_PROFIT
                * row.fun.FUN_DISCOUNTFEE
                * quantity
            )
            print(f"FUN min price: {fun_min_price}")

        bij_min_price = None
        if row.bij.BIJ_CHECK == 1:
            pass

    return min(
        [i for i in [g2g_min_price, fun_min_price, bij_min_price] if i is not None]
    )


def calculate_price_change(
    gsheet: GSheet,
    row: Row,
    offer_items: list[OfferItem],
    BIJ_HOST_DATA: list,
) -> PriceInfo:
    stock_type = identify_stock(
        gsheet,
        row.stock_info,
    )
    if stock_type is StockType.stock_1:
        product_min_price = row.product.min_price_stock_1(gsheet)
        product_max_price = row.product.max_price_stock_1(gsheet)

    elif stock_type is StockType.stock_2:
        product_min_price = row.product.min_price_stock_2(gsheet)
        product_max_price = row.product.max_price_stock_2(gsheet)

    elif stock_type is StockType.stock_fake:
        stock_fake_price = calculate_price_stock_fake(
            gsheet=gsheet, row=row, quantity=offer_items[0].quantity
        )
        product_min_price = stock_fake_price  # TODO
        product_max_price = stock_fake_price  # TODO

    min_offer_item = OfferItem.min_offer_item(
        filter_valid_offer_items(
            row.product,
            offer_items,
        )
    )
    range_adjust = None
    if min_offer_item.price < product_min_price:  # type: ignore
        adjusted_price = min_offer_item
    elif min_offer_item.price > product_max_price:  # type: ignore
        adjusted_price = product_max_price
    else:
        range_adjust = random.uniform(
            row.product.DONGIAGIAM_MIN, row.product.DONGIAGIAM_MAX
        )
        adjusted_price = round(
            min_offer_item.price - range_adjust,  # type: ignore
            row.product.DONGIA_LAMTRON,
        )
    return PriceInfo(
        price_min=product_min_price,
        price_mac=product_max_price,
        adjusted_price=round(adjusted_price, row.product.DONGIA_LAMTRON),  # type: ignore
        offer_item=min_offer_item,
        stock_type=stock_type,
        range_adjust=range_adjust,
    )


def g2g_lowest_price(
    gsheet: GSheet,
    g2g: G2G,
) -> G2GOfferItem:
    g2g_offer_items = g2g_extract_offer_items(g2g.G2G_PRODUCT_COMPARE)
    filtered_g2g_offer_items = G2GOfferItem.filter_valid_g2g_offer_item(
        g2g,
        g2g_offer_items,
        g2g.get_blacklist(gsheet),
    )
    return G2GOfferItem.min_offer_item(filtered_g2g_offer_items)


def run():
    gsheet = GSheet()
    sheet = Sheet.from_sheet_id(
        gsheet=gsheet,
        sheet_id="1ckkWEa7xbOdFKbdqGxVkpVpMm1RG6dljmigitzeN7jc",
    )
    worksheet = sheet.open_worksheet("Sheet1")
    row_indexes = [7, 8]
    for index in row_indexes:
        row = Row.from_row_index(worksheet, index)
        offer_items = extract_offer_items(row.product.PRODUCT_COMPARE)
        if is_change_price(row.product, offer_items):
            print(
                calculate_price_change(
                    gsheet, row.product, row.stock_info, offer_items
                ).model_dump(mode="json")
            )
