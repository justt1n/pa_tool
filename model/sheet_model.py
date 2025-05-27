from pydantic import BaseModel
from pydantic.fields import FieldInfo
from typing import Annotated, cast

from decorator.time_execution import time_execution
from utils.ggsheet import GSheet, Sheet
from utils.google_api import StockManager


class BaseGSheetModel(BaseModel):
    row_index: int | None = None

    @classmethod
    def fields_exclude_row_index(
            cls,
    ) -> dict[str, FieldInfo]:
        dic: dict[str, FieldInfo] = {}
        for k, v in cls.model_fields.items():
            if k != "row_index":
                dic[k] = v
        return dic


class Product(BaseGSheetModel):
    CHECK: Annotated[int, "B"]
    Product_name: Annotated[str, "C"]
    Note: Annotated[str | None, "D"] = None
    Last_Update: Annotated[str | None, "E"] = None
    Product_link: Annotated[str, "F"]
    PRODUCT_COMPARE: Annotated[str, "G"]
    TITLE: Annotated[str | None, "H"] = ''
    DESCRIPTION: Annotated[str | None, "I"] = ''
    DURATION: Annotated[str | None, "J"] = ''
    DONGIAGIAM_MIN: Annotated[float, "K"]
    DONGIAGIAM_MAX: Annotated[float, "L"]
    DONGIA_LAMTRON: Annotated[int, "M"]
    EXCLUDE_ADS: Annotated[int, "N"]
    DELIVERY_TIME: Annotated[str, "O"]
    FEEDBACK: Annotated[int, "P"]
    MIN_UNIT: Annotated[int, "Q"]
    MINSTOCK: Annotated[int, "R"]
    IDSHEET_MIN: Annotated[str, "S"]
    SHEET_MIN: Annotated[str, "T"]
    CELL_MIN: Annotated[str, "U"]
    IDSHEET_MIN2: Annotated[str | None, "V"] = ''
    SHEET_MIN2: Annotated[str | None, "W"] = ''
    CELL_MIN2: Annotated[str | None, "X"] = ''
    DELIVERY0: Annotated[str, "Y"]
    DELIVERY1: Annotated[str, "Z"]
    STOCKREAD: Annotated[int, "AA"]
    IDSHEET_MAX: Annotated[str | None, "AB"] = ''
    SHEET_MAX: Annotated[str | None, "AC"] = ''
    CELL_MAX: Annotated[str | None, "AD"] = ''
    IDSHEET_MAX2: Annotated[str | None, "AE"] = ''
    SHEET_MAX2: Annotated[str | None, "AF"] = ''
    CELL_MAX2: Annotated[str | None, "AG"] = ''
    IDSHEET_MAX_STOCKFAKE: Annotated[str | None, "CM"] = ''
    SHEET_MAX_STOCKFAKE: Annotated[str | None, "CN"] = ''
    CELL_MAX_STOCKFAKE: Annotated[str | None, "CO"] = ''
    IDSHEET_MIN_STOCKFAKE: Annotated[str | None, "CP"] = ''
    SHEET_MIN_STOCKFAKE: Annotated[str | None, "CQ"] = ''
    CELL_MIN_STOCKFAKE: Annotated[str | None, "CR"] = ''

    def min_price_stock_1(
            self,
            gsheet: GSheet,
    ) -> float:
        try:
            sheet_manager = StockManager(self.IDSHEET_MIN)
            cell_value = sheet_manager.get_cell_float_value(f"'{self.SHEET_MIN}'!{self.CELL_MIN}")
            # sheet = Sheet.from_sheet_id(gsheet, self.IDSHEET_MIN)
            # worksheet = sheet.open_worksheet(self.SHEET_MIN)
            # cell_value = worksheet.batch_get([self.CELL_MIN])[0]

            return float(cell_value)  # type: ignore
        except Exception as e:
            print("No min price stock 1")
            return 0

    def max_price_stock_1(
            self,
            gsheet: GSheet,
    ) -> float:
        try:
            sheet_manager = StockManager(self.IDSHEET_MAX)
            cell_value = sheet_manager.get_cell_float_value(f"'{self.SHEET_MAX}'!{self.CELL_MAX}")
            return float(cell_value)  # type: ignore
        except Exception as e:
            print("No max price stock 1")
            return 999999

    def min_price_stock_2(
            self,
            gsheet: GSheet,
    ) -> float:
        try:
            sheet_manager = StockManager(self.IDSHEET_MIN2)
            cell_value = sheet_manager.get_cell_float_value(f"'{self.SHEET_MIN2}'!{self.CELL_MIN2}")
            return float(cell_value)  # type: ignore
        except Exception as e:
            print("No min price stock 2")
            return 0

    def max_price_stock_2(
            self,
            gsheet: GSheet,
    ) -> float:
        try:
            sheet_manager = StockManager(self.IDSHEET_MAX2)
            cell_value = sheet_manager.get_cell_float_value(f"'{self.SHEET_MAX2}'!{self.CELL_MAX2}")
            return float(cell_value)  # type: ignore
        except Exception as e:
            print("No max price stock 2")
            return 999999

    def get_stock_fake_min_price(self):
        sheet_manager = StockManager(self.IDSHEET_MIN_STOCKFAKE)
        cell_value = sheet_manager.get_cell_stock(f"'{self.SHEET_MIN_STOCKFAKE}'!{self.CELL_MIN_STOCKFAKE}")
        return float(cell_value)

    def get_stock_fake_max_price(self):
        sheet_manager = StockManager(self.IDSHEET_MAX_STOCKFAKE)
        cell_value = sheet_manager.get_cell_stock(f"'{self.SHEET_MAX_STOCKFAKE}'!{self.CELL_MAX_STOCKFAKE}")
        return float(cell_value)


class StockInfo(BaseGSheetModel):
    IDSHEET_STOCK: Annotated[str, "AH"]
    SHEET_STOCK: Annotated[str, "AI"]
    CELL_STOCK: Annotated[str, "AJ"]
    IDSHEET_STOCK2: Annotated[str | None, "AK"] = ''
    SHEET_STOCK2: Annotated[str | None, "AL"] = ''
    CELL_STOCK2: Annotated[str | None, "AM"] = ''
    STOCK_LIMIT: Annotated[int, "AN"]
    STOCK_LIMIT2: Annotated[int | None, "AO"] = 0
    STOCK_MAX: Annotated[int | None, "AP"] = None
    STOCK_FAKE: Annotated[int | None, "AQ"] = None
    PA_IDSHEET_BLACKLIST: Annotated[str | None, "AR"] = ""
    PA_SHEET_BLACKLIST: Annotated[str | None, "AS"] = ""
    PA_CELL_BLACKLIST: Annotated[str | None, "AT"] = ""
    _stock1: int | None = 0
    _stock2: int | None = 0

    def get_pa_blacklist(self) -> list[str]:
        blacklist = []
        try:
            sheet_manager = StockManager(self.PA_IDSHEET_BLACKLIST)
            blacklist = sheet_manager.get_multiple_str_cells(f"'{self.PA_SHEET_BLACKLIST}'!{self.PA_CELL_BLACKLIST}")
        except Exception as e:
            print("Cant get pa blacklist: ", e)
            pass
        return blacklist

    def stock_1(self) -> int:
        try:
            stock_mng = StockManager(self.IDSHEET_STOCK)
            stock1 = stock_mng.get_cell_float_value(f"'{self.SHEET_STOCK}'!{self.CELL_STOCK}")
            self._stock1 = stock1  # type: ignore
            return stock1  # type: ignore
        except Exception as e:
            self._stock1 = -1
            print("No Stock 1 or wrong sheet id")
            return -1

    def stock_2(self) -> int:
        try:
            stock_mng = StockManager(self.IDSHEET_STOCK2)
            stock2 = stock_mng.get_cell_float_value(f"'{self.SHEET_STOCK2}'!{self.CELL_STOCK2}")
            self._stock2 = stock2  # type: ignore
            return stock2  # type: ignore
        except Exception as e:
            self._stock2 = -1
            print("No Stock 2 or wrong sheet id")
            return -1

    def get_stocks(self):
        if self.IDSHEET_STOCK == self.IDSHEET_STOCK2:
            stock_manager = StockManager(self.IDSHEET_STOCK)
            cell1 = f"'{self.SHEET_STOCK}'!{self.CELL_STOCK}"
            cell2 = f"'{self.SHEET_STOCK}'!{self.CELL_STOCK2}"
            try:
                stock1, stock2 = stock_manager.get_multiple_cells([cell1, cell2])
            except Exception as e:
                stock1 = self.stock_1()
                stock2 = self.stock_2()
        else:
            stock1 = self.stock_1()
            stock2 = self.stock_2()
        self._stock1 = stock1
        self._stock2 = stock2
        return stock1, stock2

    def cal_stock(self) -> int:
        if self._stock1 == 0 or self._stock1 < self.STOCK_LIMIT:
            if self._stock2 == 0 or self._stock2 < self.STOCK_LIMIT2:
                return self.STOCK_FAKE
            return self._stock2
        return self._stock1


class G2G(BaseGSheetModel):
    G2G_CHECK: Annotated[int | None, "AU"] = 0
    G2G_PROFIT: Annotated[float | None, "AV"] = 0
    G2G_PRODUCT_COMPARE: Annotated[str | None, "AW"] = ''
    G2G_DELIVERY_TIME: Annotated[int | None, "AX"] = 0
    G2G_STOCK: Annotated[int | None, "AY"] = 0
    G2G_MINUNIT: Annotated[int | None, "AZ"] = 0
    G2G_QUYDOIDONVI: Annotated[float | None, "BA"] = 0
    G2G_IDSHEET_BLACKLIST: Annotated[str | None, "BB"] = ''
    G2G_SHEET_BLACKLIST: Annotated[str | None, "BC"] = ''
    G2G_CELL_BLACKLIST: Annotated[str | None, "BD"] = ''

    def get_blacklist(
            self,
            gsheet: GSheet,
    ) -> list[str]:
        sheet_manager = StockManager(self.G2G_IDSHEET_BLACKLIST)
        blacklist = sheet_manager.get_multiple_str_cells(f"'{self.G2G_SHEET_BLACKLIST}'!{self.G2G_CELL_BLACKLIST}")
        # blacklist = [item for sublist in query_values for item in sublist]
        return blacklist

# BE BF BG BH BI BJ BK BL BM BN BO BP BQ BR BS
class FUN(BaseGSheetModel):
    FUN_CHECK: Annotated[int | None, "BE"] = 0
    FUN_PROFIT: Annotated[float | None, "BF"] = 0
    FUN_DISCOUNTFEE: Annotated[float | None, "BG"] = 0
    FUN_PRODUCT_COMPARE: Annotated[str | None, "BH"] = ''
    NAME2: Annotated[str | None, "BI"] = None
    FACTION: Annotated[str | None, "BJ"] = ''
    FUN_FILTER21: Annotated[str | None, "BK"] = None
    FUN_FILTER22: Annotated[str | None, "BL"] = None
    FUN_FILTER23: Annotated[str | None, "BM"] = None
    FUN_FILTER24: Annotated[str | None, "BN"] = None
    FUN_HESONHANDONGIA: Annotated[float | None, "BO"] = None
    FUN_STOCK: Annotated[int | None, "BP"] = 0
    FUN_IDSHEET_BLACKLIST: Annotated[str | None, "BQ"] = ''
    FUN_SHEET_BLACKLIST: Annotated[str | None, "BR"] = ''
    FUN_CELL_BLACKLIST: Annotated[str | None, "BS"] = ''

    def get_blacklist(self, gsheet: GSheet) -> list[str]:
        sheet_manager = StockManager(self.FUN_IDSHEET_BLACKLIST)
        blacklist = sheet_manager.get_multiple_str_cells(f"'{self.FUN_SHEET_BLACKLIST}'!{self.FUN_CELL_BLACKLIST}")
        return blacklist

# BT BJ BV BW BX BY BZ CA CB CC CD
class BIJ(BaseGSheetModel):
    BIJ_CHECK: Annotated[int | None, "BT"] = 0
    BIJ_PROFIT: Annotated[float | None, "BU"] = 0
    BIJ_NAME: Annotated[str | None, "BV"] = ''
    BIJ_SERVER: Annotated[str | None, "BW"] = ''
    BIJ_DELIVERY_METHOD: Annotated[str | None, "BX"] = ''
    BIJ_STOCKMIN: Annotated[int | None, "BY"] = 0
    BIJ_STOCKMAX: Annotated[int | None, "BZ"] = 0
    HESONHANDONGIA3: Annotated[float | None, "CA"] = 0
    BIJ_IDSHEET_BLACKLIST: Annotated[str | None, "CB"] = ''
    BIJ_SHEET_BLACKLIST: Annotated[str | None, "CC"] = ''
    BIJ_CELL_BLACKLIST: Annotated[str | None, "CD"] = ''

    def get_blacklist(self, gsheet: GSheet) -> list[str]:
        sheet_manager = StockManager(self.BIJ_IDSHEET_BLACKLIST)
        blacklist = sheet_manager.get_multiple_str_cells(f"'{self.BIJ_SHEET_BLACKLIST}'!{self.BIJ_CELL_BLACKLIST}")
        return blacklist

#CE CF CG CH CI CJ CK CL
class ExtraInfor(BaseGSheetModel):
    MIN_UNIT_PER_ORDER: Annotated[int, "CE"]
    VALUE_FOR_DISCOUNT: Annotated[str | None, "CF"] = ""
    DISCOUNT: Annotated[str | None, "CG"] = ""
    DELIVERY_GUARANTEE: Annotated[int, "CH"]
    CURRENCY_PER_UNIT: Annotated[float, "CI"]
    GAME_LIST_SHEET_ID: Annotated[str | None, "CJ"] = ""
    GAME_LIST_SHEET: Annotated[str | None, "CK"] = ""
    GAME_LIST_CELLS: Annotated[str | None, "CL"] = ""

    def get_game_list(self) -> list[str]:
        sheet_manager = StockManager(self.GAME_LIST_SHEET_ID)
        game_list = sheet_manager.get_multiple_str_cells(f"'{self.GAME_LIST_SHEET}'!{self.GAME_LIST_CELLS}")
        return game_list


# CS CT CU CV CW CX
class DD(BaseGSheetModel):
    DD_CHECK: Annotated[int | None, "CS"] = 0
    DD_PROFIT: Annotated[float | None, "CT"] = 0
    DD_QUYDOIDONVI: Annotated[float | None, "CU"] = 0
    DD_PRODUCT_COMPARE: Annotated[str | None, "CV"] = ''
    DD_STOCKMIN: Annotated[int | None, "CW"] = 0
    DD_LEVELMIN: Annotated[int | None, "CX"] = 0


class PriceSheet1(BaseGSheetModel):
    SHEET_CHECK: Annotated[int | None, "CY"] = 0
    SHEET_PROFIT: Annotated[float | None, "CZ"] = 0
    HE_SO_NHAN: Annotated[float | None, "DA"] = 0
    QUYDOIDONVI: Annotated[float | None, "DB"] = 0
    ID_SHEET_PRICE: Annotated[str | None, "DC"] = ""
    SHEET_PRICE: Annotated[str | None, "DD"] = ""
    CELL_PRICE: Annotated[str | None, "DE"] = ""

    def get_price(self) -> float:
        sheet_manager = StockManager(self.ID_SHEET_PRICE)
        price = sheet_manager.get_cell_float_value(f"'{self.SHEET_PRICE}'!{self.CELL_PRICE}")
        return float(price)


class PriceSheet2(BaseGSheetModel):
    SHEET_CHECK: Annotated[int | None, "DF"] = 0
    SHEET_PROFIT: Annotated[float | None, "DG"] = 0
    HE_SO_NHAN: Annotated[float | None, "DH"] = 0
    QUYDOIDONVI: Annotated[float | None, "DI"] = 0
    ID_SHEET_PRICE: Annotated[str | None, "DJ"] = ""
    SHEET_PRICE: Annotated[str | None, "DK"] = ""
    CELL_PRICE: Annotated[str | None, "DL"] = ""

    def get_price(self) -> float:
        sheet_manager = StockManager(self.ID_SHEET_PRICE)
        price = sheet_manager.get_cell_float_value(f"'{self.SHEET_PRICE}'!{self.CELL_PRICE}")
        return float(price)


class PriceSheet3(BaseGSheetModel):
    SHEET_CHECK: Annotated[int | None, "DM"] = 0
    SHEET_PROFIT: Annotated[float | None, "DN"] = 0
    HE_SO_NHAN: Annotated[float | None, "DO"] = 0
    QUYDOIDONVI: Annotated[float | None, "DP"] = 0
    ID_SHEET_PRICE: Annotated[str | None, "DQ"] = ""
    SHEET_PRICE: Annotated[str | None, "DR"] = ""
    CELL_PRICE: Annotated[str | None, "DS"] = ""

    def get_price(self) -> float:
        sheet_manager = StockManager(self.ID_SHEET_PRICE)
        price = sheet_manager.get_cell_float_value(f"'{self.SHEET_PRICE}'!{self.CELL_PRICE}")
        return float(price)


class PriceSheet4(BaseGSheetModel):
    SHEET_CHECK: Annotated[int | None, "DT"] = 0
    SHEET_PROFIT: Annotated[float | None, "DU"] = 0
    HE_SO_NHAN: Annotated[float | None, "DV"] = 0
    QUYDOIDONVI: Annotated[float | None, "DW"] = 0
    ID_SHEET_PRICE: Annotated[str | None, "DX"] = ""
    SHEET_PRICE: Annotated[str | None, "DY"] = ""
    CELL_PRICE: Annotated[str | None, "DZ"] = ""

    def get_price(self) -> float:
        sheet_manager = StockManager(self.ID_SHEET_PRICE)
        price = sheet_manager.get_cell_float_value(f"'{self.SHEET_PRICE}'!{self.CELL_PRICE}")
        return float(price)





