import random
from typing import Any

import gspread

from decorator.retry import retry
from model.crawl_model import G2GOfferItem, OfferItem, DeliveryTime, FUNOfferItem
from model.enums import StockType
from model.payload import PriceInfo, Row
from model.sheet_model import G2G, Product, StockInfo
from utils.biji_extract import bij_lowest_price
from utils.fun_extract import fun_extract_offer_items
from utils.g2g_extract import g2g_extract_offer_items
from utils.ggsheet import (
    GSheet,
)
from utils.selenium_util import SeleniumUtil
from utils.utils import getCNYRate


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
    if not offer_item.seller.feedback_count:
        print("Can't get feedback count")
    elif offer_item.seller.feedback_count < product.FEEDBACK:
        print(f"Feedback count: {offer_item.seller.feedback_count} for seller {offer_item.seller.name}, ignore")
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
    if product.CHECK == 0:
        return False

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


@retry(retries=20, delay=0.25)
def calculate_price_stock_fake(
        gsheet: GSheet,
        row: Row,
        quantity: int,
        hostdata: dict,
        selenium: SeleniumUtil,
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
                round(g2g_min_offer_item.price_per_unit
                      * quantity
                      * row.g2g.G2G_PROFIT, 4)
                , g2g_min_offer_item.seller_name)
            print(f"\nG2G min price: {g2g_min_price}")
        else:
            print("No valid G2G offer items")

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
                round(fun_min_offer_item.price
                      * row.fun.FUN_PROFIT
                      * row.fun.FUN_DISCOUNTFEE
                      * quantity, 4)
                , fun_min_offer_item.seller)
            print(f"\nFUN min price: {fun_min_price}")
        else:
            print("No valid FUN offer items")

    bij_min_price = None
    CNY_RATE = getCNYRate(gsheet)
    if row.bij.BIJ_CHECK == 1:
        bij_min_offer_item = bij_lowest_price(hostdata, selenium, row.bij)
        if bij_min_offer_item:
            bij_min_price = (
                round(bij_min_offer_item.money
                      * row.bij.BIJ_PROFIT
                      * quantity
                      * row.bij.HESONHANDONGIA3
                      * CNY_RATE, 4)
                , bij_min_offer_item.username)
            print(f"\nBIJ min price: {bij_min_price}")
        else:
            print("No valid BIJ offer items")

    return min(
        [i for i in [g2g_min_price, fun_min_price, bij_min_price] if i is not None],
        key=lambda x: x[0]
    ), [g2g_min_price, fun_min_price, bij_min_price]


@retry(retries=20, delay=0.25, exception=Exception)
def calculate_price_change(
        gsheet: GSheet,
        row: Row,
        offer_items: list[OfferItem],
        BIJ_HOST_DATA: dict,
        selenium: SeleniumUtil,
) -> tuple[PriceInfo, list] | None:
    stock_type = identify_stock(
        gsheet,
        row.stock_info,
    )

    min_offer_item = OfferItem.min_offer_item(
        filter_valid_offer_items(
            row.product,
            offer_items,
        )
    )
    stock_fake_items = None
    if stock_type is StockType.stock_1:
        product_min_price = row.product.min_price_stock_1(gsheet) * min_offer_item.quantity
        product_max_price = row.product.max_price_stock_1(gsheet) * min_offer_item.quantity

    elif stock_type is StockType.stock_2:
        product_min_price = row.product.min_price_stock_2(gsheet) * min_offer_item.quantity
        product_max_price = row.product.max_price_stock_2(gsheet) * min_offer_item.quantity

    elif stock_type is StockType.stock_fake:
        (stock_fake_price, stock_fake_items) = calculate_price_stock_fake(
            gsheet=gsheet, row=row, quantity=min_offer_item.quantity, hostdata=BIJ_HOST_DATA, selenium=selenium
        )
        if stock_fake_price is None:
            return None
        return PriceInfo(
            price_min=round(stock_fake_price[0], 4),
            price_mac=round(stock_fake_price[0], 4),
            adjusted_price=round(stock_fake_price[0], 4),
            offer_item=min_offer_item,
            stock_type=stock_type,
        ), stock_fake_items

    range_adjust = None
    if min_offer_item.price < product_min_price:  # type: ignore
        adjusted_price = product_min_price
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
    ), stock_fake_items


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
