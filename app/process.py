import copy
import random
import concurrent.futures
from typing import Any, Optional, Tuple, List

import gspread

from decorator.retry import retry
from decorator.time_execution import time_execution
from model.crawl_model import G2GOfferItem, OfferItem, DeliveryTime, FUNOfferItem, StockNumInfo
from model.enums import StockType
from model.payload import PriceInfo, Row
from model.sheet_model import G2G, Product, StockInfo
from utils.biji_extract import bij_lowest_price
from utils.common_utils import getCNYRate
from utils.dd_utils import DD373Product, get_dd_min_price
from utils.fun_extract import fun_extract_offer_items
from utils.g2g_extract import g2g_extract_offer_items
from utils.ggsheet import (
    GSheet,
)
from utils.selenium_util import SeleniumUtil


def get_row_run_index(
        worksheet: gspread.worksheet.Worksheet,
        col_check_index: int = 2,
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
        black_list: list[str],
) -> bool:
    product_delivery_time = DeliveryTime.from_text(product.DELIVERY_TIME)
    if (
            offer_item.delivery_time is None
            or offer_item.delivery_time > product_delivery_time
    ):
        return False
    # if not offer_item.seller.feedback_count:
    #     offer_item.seller.feedback_count = 0
    # elif offer_item.seller.feedback_count < product.FEEDBACK:
    #     print(f"Feedback count: {offer_item.seller.feedback_count} for seller {offer_item.seller.name}, ignore")
    #     return False
    if offer_item.seller.name in black_list:
        return False
    if offer_item.min_unit is None or offer_item.min_unit > product.MIN_UNIT:
        return False
    if offer_item.min_stock is None or offer_item.min_stock < product.MINSTOCK:
        return False

    return True


def filter_valid_offer_items(
        product: Product,
        offer_items: list[OfferItem],
        black_list: list[str],
) -> list[OfferItem]:
    return [
        offer_item
        for offer_item in offer_items
        if is_valid_offer_item(product, offer_item, black_list)
    ]


def is_change_price(
        product: Product,
        offer_items: list[OfferItem],
        black_list: list[str],
) -> bool:
    if product.CHECK == 0:
        return False

    if product.EXCLUDE_ADS == 0:  # TODO:
        return False

    filtered_offer_items = filter_valid_offer_items(product, offer_items, black_list)
    if len(filtered_offer_items) == 0:
        return False

    return True


def identify_stock(
        gsheet: GSheet,
        stock_info: StockInfo,
) -> [StockType, StockNumInfo]:
    stock_1, stock_2 = stock_info.get_stocks()

    stock_fake = stock_info.STOCK_FAKE

    stock_num_info = StockNumInfo(
        stock_1=stock_1,
        stock_2=stock_2,
        stock_fake=stock_fake,
    )

    stock_type = StockType.stock_fake
    if stock_1 != -1 and stock_1 >= stock_info.STOCK_LIMIT:
        stock_type = StockType.stock_1
    if stock_2 != -1 and stock_2 >= stock_info.STOCK_LIMIT2:
        stock_type = StockType.stock_2
    return stock_type, stock_num_info


# @retry(retries=2, delay=0.1)
# def calculate_price_stock_fake(
#         gsheet: GSheet,
#         row: Row,
#         quantity: int,
#         hostdata: dict,
#         selenium: SeleniumUtil,
# ):
#     g2g_min_price = None
#     if row.g2g.G2G_CHECK == 1:
#         g2g_offer_items = g2g_extract_offer_items(row.g2g.G2G_PRODUCT_COMPARE)
#         filtered_g2g_offer_items = G2GOfferItem.filter_valid_g2g_offer_item(
#             g2g=row.g2g,
#             g2g_blacklist=row.g2g.get_blacklist(gsheet),
#             g2g_offer_items=g2g_offer_items,
#         )
#         if filtered_g2g_offer_items:
#             g2g_min_offer_item = G2GOfferItem.min_offer_item(filtered_g2g_offer_items)
#             g2g_min_price = (
#                 round(g2g_min_offer_item.price_per_unit
#                       * row.g2g.G2G_PROFIT, 4)
#                 , g2g_min_offer_item.seller_name)
#             print(f"\nG2G min price: {g2g_min_price}")
#         else:
#             print("No valid G2G offer items")
#
#     fun_min_price = None
#     if row.fun.FUN_CHECK == 1:
#         fun_offer_items = fun_extract_offer_items(
#             row.fun.FUN_PRODUCT_COMPARE,
#             [
#                 i
#                 for i in [
#                 row.fun.FUN_FILTER21,
#                 row.fun.FUN_FILTER22,
#                 row.fun.FUN_FILTER23,
#                 row.fun.FUN_FILTER24,
#             ]
#                 if i is not None
#             ],
#         )
#         filtered_fun_offer_items = FUNOfferItem.filter_valid_fun_offer_items(
#             fun=row.fun,
#             fun_offer_items=fun_offer_items,
#             fun_blacklist=row.fun.get_blacklist(gsheet),
#         )
#         if filtered_fun_offer_items:
#             fun_min_offer_item = FUNOfferItem.min_offer_item(filtered_fun_offer_items)
#             fun_min_price = (
#                 round(fun_min_offer_item.price
#                       * row.fun.FUN_PROFIT
#                       * row.fun.FUN_DISCOUNTFEE
#                       * row.fun.FUN_HESONHANDONGIA
#                       , 4)
#                 , fun_min_offer_item.seller)
#             print(f"\nFUN min price: {fun_min_price}")
#         else:
#             print("No valid FUN offer items")
#
#     bij_min_price = None
#     CNY_RATE = getCNYRate()
#     # print("HEre")
#     _black_list = row.bij.get_blacklist(gsheet)
#     if row.bij.BIJ_CHECK == 1:
#         bij_min_offer_item = None
#         for attempt in range(2):
#             try:
#                 bij_min_offer_item = bij_lowest_price(hostdata, selenium, row.bij, black_list=_black_list)
#                 break  # Exit the loop if successful
#             except Exception as e:
#                 print("Renew browser")
#                 selenium = SeleniumUtil(mode=2)
#                 if attempt == 1:
#                     print("Error when getting BIJ", e)
#         if bij_min_offer_item:
#             bij_min_price = (
#                 round(bij_min_offer_item.money
#                       * row.bij.BIJ_PROFIT
#                       * row.bij.HESONHANDONGIA3
#                       * CNY_RATE, 4)
#                 , bij_min_offer_item.username)
#             print(f"\nBIJ min price: {bij_min_price}")
#         else:
#             print("No valid BIJ offer items")
#
#     return min(
#         [i for i in [g2g_min_price, fun_min_price, bij_min_price] if i is not None and i[0] > 0],
#         key=lambda x: x[0]
#     ), [g2g_min_price, fun_min_price, bij_min_price]
#

@time_execution
@retry(retries=3, delay=0.25, exception=Exception)
def calculate_price_change(
        gsheet: GSheet,
        row: Row,
        offer_items: list[OfferItem],
        BIJ_HOST_DATA: dict,
        selenium: SeleniumUtil,
        black_list: list[str],
) -> None | tuple[PriceInfo, list[tuple[float, str] | None]] | tuple[PriceInfo, None]:
    stock_type, stock_num_info = identify_stock(
        gsheet,
        row.stock_info,
    )
    offer_items_copy = copy.deepcopy(offer_items)

    # Ensure min_offer_item is valid before proceeding
    valid_filtered_offer_items = filter_valid_offer_items(
        row.product,
        offer_items_copy,  # Use the copy for filtering
        black_list=black_list
    )
    if not valid_filtered_offer_items:
        # print("No valid offer items after initial filtering for min_offer_item.")
        return None  # Cannot proceed without a base offer item

    min_offer_item = OfferItem.min_offer_item(valid_filtered_offer_items)

    if min_offer_item is None or min_offer_item.quantity == 0:  # Check for None and zero quantity
        # print("Min offer item is None or has zero quantity.")
        return None

    _ref_seller = min_offer_item.seller.name
    min_offer_item.price = min_offer_item.price / min_offer_item.quantity  # Price per unit
    _ref_price = min_offer_item.price
    stock_fake_items = None

    product_min_price: float = -1.0
    product_max_price: float = -1.0
    adjusted_price: float = 0.0
    range_adjust: float = 0.0

    if stock_type is StockType.stock_1:
        product_min_price = float(row.product.min_price_stock_1(gsheet))
        product_max_price = float(row.product.max_price_stock_1(gsheet))

    elif stock_type is StockType.stock_2:
        product_min_price = float(row.product.min_price_stock_2(gsheet))
        product_max_price = float(row.product.max_price_stock_2(gsheet))

    elif stock_type is StockType.stock_fake:
        stock_fake_price_tuple, stock_fake_items = calculate_price_stock_fake(
            gsheet=gsheet, row=row, quantity=min_offer_item.quantity, hostdata=BIJ_HOST_DATA, selenium=selenium
        )
        if stock_fake_price_tuple is None or stock_fake_price_tuple[0] <= 0:  # Ensure valid price
            # print("Stock fake price is None or not positive.")
            return None

        stock_fake_price_value = stock_fake_price_tuple[0]

        # These are the min/max for the "stock_fake" scenario itself
        product_min_price = float(row.product.get_stock_fake_min_price())  # Renamed for clarity within block
        product_max_price = float(row.product.get_stock_fake_max_price())  # Renamed for clarity

        range_adjust = random.uniform(row.product.DONGIAGIAM_MIN, row.product.DONGIAGIAM_MAX)

        if int(product_min_price) == -1 and int(product_max_price) == -1:
            # Filter items not in blacklist for finding closest if no min/max defined
            valid_offers_for_closest = [item for item in valid_filtered_offer_items if
                                        item.seller.name not in black_list and item.quantity > 0]
            if not valid_offers_for_closest:
                # print("No valid offers to find closest when stock_fake min/max are -1.")
                return None  # Cannot determine price

            # Find offer item closest to stock_fake_price_value (competitor price)
            closest_offer_to_competitor = min(
                valid_offers_for_closest,
                key=lambda item: abs((item.price / item.quantity) - stock_fake_price_value)
            )
            adjusted_price = round(
                (closest_offer_to_competitor.price / closest_offer_to_competitor.quantity) - range_adjust,
                row.product.DONGIA_LAMTRON,
            )
            # Ensure our price is at least the competitor's price (or our calculated version of it)
            adjusted_price = max(adjusted_price, stock_fake_price_value)

        elif product_min_price != -1.0 and stock_fake_price_value < product_min_price:
            adjusted_price = product_min_price
        elif product_max_price != -1.0 and stock_fake_price_value > product_max_price:
            adjusted_price = product_max_price
        else:
            # Price based on competitor + random adjustment (if competitor price is within our min/max or no min/max)
            adjusted_price = round(
                stock_fake_price_value + range_adjust,  # User may want to be above competitor
                row.product.DONGIA_LAMTRON,
            )

        # General clamping based on our own product's min_offer_item and defined fake_stock min/max
        # Ensure adjusted_price is not below our own min_offer_item's price (minus an adjustment)
        # And not below the product_min_price for stock_fake
        lower_bound_candidate = min_offer_item.price - range_adjust  # Potential price based on our cheapest valid offer

        current_lower_bound = lower_bound_candidate
        if product_min_price != -1.0:
            current_lower_bound = max(lower_bound_candidate, product_min_price)

        adjusted_price = max(adjusted_price, current_lower_bound)

        if product_max_price != -1.0:
            adjusted_price = min(adjusted_price, product_max_price)

        adjusted_price = round(adjusted_price, row.product.DONGIA_LAMTRON)

        # Attempt to undercut a slightly higher priced seller
        # Sort by price per unit
        sorted_valid_offers = sorted([item for item in valid_filtered_offer_items if item.quantity > 0],
                                     key=lambda item: item.price / item.quantity)

        _profit_margin_for_undercut = random.uniform(row.product.DONGIAGIAM_MIN, row.product.DONGIAGIAM_MAX)
        closest_price, closest_seller = get_closest_offer_item(sorted_valid_offers, adjusted_price,
                                                               _profit_margin_for_undercut, black_list)

        if closest_price != -1 and closest_price > 0:  # Ensure positive price
            adjusted_price = closest_price
            _ref_seller = closest_seller
            _ref_price = closest_price + _profit_margin_for_undercut  # This is the target competitor price we undercut

            # Re-clamp and re-round after getting closest_price
            if product_min_price != -1.0:
                adjusted_price = max(adjusted_price, product_min_price)
            if product_max_price != -1.0:
                adjusted_price = min(adjusted_price, product_max_price)
            adjusted_price = round(adjusted_price, row.product.DONGIA_LAMTRON)

        _display_min_price = round(product_min_price, 4) if product_min_price != -1.0 else -1.0
        _display_max_price = round(product_max_price, 4) if product_max_price != -1.0 else -1.0

        return PriceInfo(
            price_min=_display_min_price,
            price_mac=_display_max_price,
            adjusted_price=adjusted_price,
            offer_item=min_offer_item,  # This is the original min_offer_item (price per unit)
            stock_type=stock_type,
            stock_num_info=stock_num_info,
            ref_seller=_ref_seller,
            ref_price=_ref_price
        ), stock_fake_items

    # For stock_1 and stock_2 types
    range_adjust = random.uniform(
        row.product.DONGIAGIAM_MIN, row.product.DONGIAGIAM_MAX
    )

    # Initial adjusted price based on min_offer_item and product's own min/max for this stock type
    if product_min_price != -1.0 and min_offer_item.price < product_min_price:
        adjusted_price = product_min_price
    elif product_max_price != -1.0 and min_offer_item.price > product_max_price:
        adjusted_price = product_max_price
    else:  # min_offer_item.price is within bounds, or bounds are not set
        adjusted_price = round(
            min_offer_item.price - range_adjust,  # Undercut our own cheapest offer slightly
            row.product.DONGIA_LAMTRON,
        )

    # Re-apply clamping with product's min/max for this stock type
    # Ensure adjusted_price is not below (our min_offer_item - range_adjust)
    # And also not below the defined product_min_price for this stock type

    lower_bound_candidate_stock12 = min_offer_item.price - range_adjust
    current_lower_bound_stock12 = lower_bound_candidate_stock12
    if product_min_price != -1.0:
        current_lower_bound_stock12 = max(lower_bound_candidate_stock12, product_min_price)

    adjusted_price = max(adjusted_price, current_lower_bound_stock12)

    if product_max_price != -1.0:
        adjusted_price = min(adjusted_price, product_max_price)

    adjusted_price = round(adjusted_price, row.product.DONGIA_LAMTRON)

    # Attempt to undercut a slightly higher priced seller from the general offers list
    # Sort by price per unit
    sorted_valid_offers_stock12 = sorted([item for item in valid_filtered_offer_items if item.quantity > 0],
                                         key=lambda item: item.price / item.quantity)
    _profit_margin_for_undercut_stock12 = random.uniform(row.product.DONGIAGIAM_MIN, row.product.DONGIAGIAM_MAX)
    closest_price, closest_seller = get_closest_offer_item(sorted_valid_offers_stock12, adjusted_price,
                                                           _profit_margin_for_undercut_stock12, black_list)

    if closest_price != -1 and closest_price > 0:  # Ensure positive price
        adjusted_price = closest_price
        _ref_seller = closest_seller
        _ref_price = closest_price + _profit_margin_for_undercut_stock12  # Target competitor price

        # Re-clamp and re-round after getting closest_price
        if product_min_price != -1.0:
            adjusted_price = max(adjusted_price, product_min_price)
        if product_max_price != -1.0:
            adjusted_price = min(adjusted_price, product_max_price)
        adjusted_price = round(adjusted_price, row.product.DONGIA_LAMTRON)

    _display_product_min_price = product_min_price if product_min_price != -1.0 else -1.0
    _display_product_max_price = product_max_price if product_max_price != -1.0 else -1.0

    return PriceInfo(
        price_min=_display_product_min_price,
        price_mac=_display_product_max_price,
        adjusted_price=adjusted_price,
        offer_item=min_offer_item,  # This is the original min_offer_item (price per unit)
        stock_type=stock_type,
        range_adjust=range_adjust,  # This might be the initial range_adjust
        stock_num_info=stock_num_info,
        ref_seller=_ref_seller,
        ref_price=_ref_price
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


def get_closest_offer_item(
        sorted_offer_items: list[OfferItem],
        price: float,
        profit: float,
        black_list: list[str]
):
    if len(sorted_offer_items) >= 1:
        if price < sorted_offer_items[0].price:
            return -1, "Keep"
    # Filter offer items that have a price above the target price
    above_price_items = [item for item in sorted_offer_items if
                         (item.price / item.quantity) > price and item.seller.name not in black_list]

    if not above_price_items:
        # If no items are above the target price, return the item with the highest price
        closest_item = max(sorted_offer_items, key=lambda item: item.price / item.quantity)
    else:
        # Find the item with the lowest price among those above the target price
        closest_item = min(above_price_items, key=lambda item: item.price / item.quantity)

    # Create a copy of the closest item
    adjusted_item = copy.deepcopy(closest_item)

    # Adjust the price by the profit factor
    adjusted_item.price = (adjusted_item.price / adjusted_item.quantity) - profit

    return adjusted_item.price, adjusted_item.seller.name


def _process_g2g(row: Row, gsheet: GSheet) -> Optional[Tuple[float, str]]:
    try:
        print("Starting G2G fetch...")
        g2g_offer_items = g2g_extract_offer_items(row.g2g.G2G_PRODUCT_COMPARE)
        filtered_g2g_offer_items = G2GOfferItem.filter_valid_g2g_offer_item(
            g2g=row.g2g,
            g2g_blacklist=row.g2g.get_blacklist(gsheet),
            g2g_offer_items=g2g_offer_items,
        )
        if filtered_g2g_offer_items:
            g2g_min_offer_item = G2GOfferItem.min_offer_item(filtered_g2g_offer_items)
            g2g_min_price = (
                round(g2g_min_offer_item.price_per_unit * row.g2g.G2G_PROFIT, 4),
                g2g_min_offer_item.seller_name
            )
            print(f"G2G min price calculated: {g2g_min_price}")
            return g2g_min_price
        else:
            print("No valid G2G offer items")
            return None
    except Exception as e:
        print(f"Error processing G2G: {e}")
        return None


def _process_fun(row: Row, gsheet: GSheet) -> Optional[Tuple[float, str]]:
    try:
        print("Starting FUN fetch...")
        fun_offer_items = fun_extract_offer_items(
            row.fun.FUN_PRODUCT_COMPARE,
            [
                i
                for i in [
                row.fun.FUN_FILTER21, row.fun.FUN_FILTER22,
                row.fun.FUN_FILTER23, row.fun.FUN_FILTER24,
            ] if i is not None
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
                round(
                    fun_min_offer_item.price * row.fun.FUN_PROFIT * row.fun.FUN_DISCOUNTFEE * row.fun.FUN_HESONHANDONGIA,
                    4),
                fun_min_offer_item.seller
            )
            print(f"FUN min price calculated: {fun_min_price}")
            return fun_min_price
        else:
            print("No valid FUN offer items")
            return None
    except Exception as e:
        print(f"Error processing FUN: {e}")
        return None


def _process_bij(row: Row, gsheet: GSheet, hostdata: dict, selenium: SeleniumUtil) -> Optional[Tuple[float, str]]:
    try:
        print("Starting BIJ fetch...")
        CNY_RATE = getCNYRate()
        _black_list = row.bij.get_blacklist(gsheet)
        bij_min_offer_item = None
        for attempt in range(2):
            try:
                bij_min_offer_item = bij_lowest_price(hostdata, selenium, row.bij, black_list=_black_list)
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for BIJ. Error: {e}")
                if attempt == 1:
                    print("Error when getting BIJ after retries", e)
                    raise  # Ném lại lỗi sau khi hết số lần thử

        if bij_min_offer_item:
            bij_min_price = (
                round(bij_min_offer_item.money * row.bij.BIJ_PROFIT * row.bij.HESONHANDONGIA3 * CNY_RATE, 4),
                bij_min_offer_item.username
            )
            print(f"BIJ min price calculated: {bij_min_price}")
            return bij_min_price
        else:
            print("No valid BIJ offer items")
            return None
    except Exception as e:
        print(f"Error processing BIJ: {e}")
        return None


def _process_dd(row: Row, gsheet: GSheet) -> Optional[Tuple[float, str]]:
    try:
        print("Starting DD fetch...")
        dd_min_offer_item = None
        for attempt in range(2):
            try:
                dd_min_offer_item = get_dd_min_price(row.dd)
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for DD. Error: {e}")
                if attempt == 1:
                    print("Error when getting DD after retries", e)
                    raise
        return dd_min_offer_item
    except Exception as e:
        print(f"Error processing DD: {e}")
        return None


@retry(retries=2, delay=0.1)
@time_execution
def calculate_price_stock_fake(
        gsheet: GSheet,
        row: Row,
        quantity: int,  # Biến này không được sử dụng trong logic gốc? Vẫn giữ lại param.
        hostdata: dict,
        selenium: SeleniumUtil,
) -> Tuple[Optional[Tuple[float, str]], List[Optional[Tuple[float, str]]]]:  # Trả về tuple(min_price, list_all_prices)

    g2g_future = None
    fun_future = None
    bij_future = None
    dd_future = None

    results = {}  # Dictionary để lưu kết quả theo nguồn

    # Sử dụng ThreadPoolExecutor để chạy song song
    # max_workers=3 để giới hạn số luồng bằng số nguồn dữ liệu
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Submit G2G task
        if row.g2g.G2G_CHECK == 1:
            print("Submitting G2G task...")
            g2g_future = executor.submit(_process_g2g, row, gsheet)

        # Submit FUN task
        if row.fun.FUN_CHECK == 1:
            print("Submitting FUN task...")
            fun_future = executor.submit(_process_fun, row, gsheet)

        # Submit BIJ task
        if row.bij.BIJ_CHECK == 1:
            print("Submitting BIJ task...")
            bij_future = executor.submit(_process_bij, row, gsheet, hostdata, selenium)

        if row.dd.DD_CHECK == 1:
            print("Submitting DD task...")
            dd_future = executor.submit(_process_dd, row, gsheet)

        if g2g_future:
            try:
                results['g2g'] = g2g_future.result()  # Lấy kết quả từ luồng G2G
                print(f"G2G Result received: {results['g2g']}")
            except Exception as e:
                print(f"G2G task failed with exception: {e}")
                results['g2g'] = None
        else:
            results['g2g'] = None

        if fun_future:
            try:
                results['fun'] = fun_future.result()  # Lấy kết quả từ luồng FUN
                print(f"FUN Result received: {results['fun']}")
            except Exception as e:
                print(f"FUN task failed with exception: {e}")
                results['fun'] = None
        else:
            results['fun'] = None

        if bij_future:
            try:
                results['bij'] = bij_future.result()  # Lấy kết quả từ luồng BIJ
                print(f"BIJ Result received: {results['bij']}")
            except Exception as e:
                print(f"BIJ task failed with exception: {e}")
                results['bij'] = None
        else:
            results['bij'] = None

        if dd_future:
            try:
                results['dd'] = dd_future.result()  # Lấy kết quả từ luồng DD
                print(f"DD Result received: {results['dd']}")
            except Exception as e:
                print(f"DD task failed with exception: {e}")
                results['dd'] = None

    g2g_min_price = results.get('g2g')
    fun_min_price = results.get('fun')
    bij_min_price = results.get('bij')
    dd_min_price = results.get('dd')

    all_prices: List[Optional[Tuple[float, str]]] = [g2g_min_price, fun_min_price, bij_min_price, dd_min_price]
    valid_prices = [p for p in all_prices if p is not None and p[0] > 0]

    if not valid_prices:
        print("No valid prices found from any source.")
        final_min_price = None
    else:
        final_min_price = min(valid_prices, key=lambda x: x[0])
        print(f"Overall minimum price: {final_min_price}")

    return final_min_price, all_prices
