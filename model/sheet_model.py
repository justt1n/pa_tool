from pydantic import BaseModel
from pydantic.fields import FieldInfo
from typing import Annotated, cast
from utils.ggsheet import GSheet, Sheet


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
    IDSHEET_MIN2: Annotated[str, "V"]
    SHEET_MIN2: Annotated[str, "W"]
    CELL_MIN2: Annotated[str, "X"]
    DELIVERY0: Annotated[str, "Y"]
    DELIVERY1: Annotated[str, "Z"]
    STOCKREAD: Annotated[int, "AA"]
    IDSHEET_MAX: Annotated[str, "AB"]
    SHEET_MAX: Annotated[str, "AC"]
    CELL_MAX: Annotated[str, "AD"]
    IDSHEET_MAX2: Annotated[str, "AE"]
    SHEET_MAX2: Annotated[str, "AF"]
    CELL_MAX2: Annotated[str, "AG"]

    def min_price_stock_1(
        self,
        gsheet: GSheet,
    ) -> float:
        sheet = Sheet.from_sheet_id(gsheet, self.IDSHEET_MIN)
        worksheet = sheet.open_worksheet(self.SHEET_MIN)
        cell_value = worksheet.batch_get([self.CELL_MIN])[0]

        return float(cell_value.first())  # type: ignore

    def max_price_stock_1(
        self,
        gsheet: GSheet,
    ) -> float:
        sheet = Sheet.from_sheet_id(gsheet, self.IDSHEET_MAX)
        worksheet = sheet.open_worksheet(self.SHEET_MAX)
        cell_value = worksheet.batch_get([self.CELL_MAX])[0]
        return float(cell_value.first())  # type: ignore

    def min_price_stock_2(
        self,
        gsheet: GSheet,
    ) -> float:
        sheet = Sheet.from_sheet_id(gsheet, self.IDSHEET_MIN2)
        worksheet = sheet.open_worksheet(self.SHEET_MIN2)
        cell_value = worksheet.batch_get([self.CELL_MIN2])[0]
        return float(cell_value.first())  # type: ignore

    def max_price_stock_2(
        self,
        gsheet: GSheet,
    ) -> float:
        sheet = Sheet.from_sheet_id(gsheet, self.IDSHEET_MAX2)
        worksheet = sheet.open_worksheet(self.SHEET_MAX2)
        cell_value = worksheet.batch_get([self.CELL_MAX2])[0]
        return float(cell_value.first())  # type: ignore


class StockInfo(BaseGSheetModel):
    IDSHEET_STOCK: Annotated[str, "AH"]
    SHEET_STOCK: Annotated[str, "AI"]
    CELL_STOCK: Annotated[str, "AJ"]
    IDSHEET_STOCK2: Annotated[str, "AK"]
    SHEET_STOCK2: Annotated[str, "AL"]
    CELL_STOCK2: Annotated[str, "AM"]
    STOCK_LIMIT: Annotated[int, "AN"]
    STOCK_LIMIT2: Annotated[int, "AO"]
    STOCK_MAX: Annotated[int | None, "AP"] = None
    STOCK_FAKE: Annotated[int | None, "AQ"] = None
    _stock1: int | None = 0
    _stock2: int | None = 0

    def stock_1(
        self,
        gsheet: GSheet,
    ) -> int:
        sheet = Sheet.from_sheet_id(gsheet, self.IDSHEET_STOCK)
        worksheet = sheet.open_worksheet(self.SHEET_STOCK)
        cell_value = worksheet.batch_get([self.CELL_STOCK])[0]
        try:
            self._stock1 = int(cell_value.first())  # type: ignore
            return int(cell_value.first())  # type: ignore
        except Exception as e:
            print(e)
            raise Exception("Error getting stock 1")

    def stock_2(
        self,
        gsheet: GSheet,
    ) -> int:
        sheet = Sheet.from_sheet_id(gsheet, self.IDSHEET_STOCK2)
        worksheet = sheet.open_worksheet(self.SHEET_STOCK2)
        cell_value = worksheet.batch_get([self.CELL_STOCK2])[0]
        try:
            self._stock2 = int(cell_value.first())  # type: ignore
            return int(cell_value.first())  # type: ignore
        except Exception as e:
            print(e)
            raise Exception("Error getting stock 2")

    def cal_stock(self) -> int:
        if self._stock1 < self.STOCK_LIMIT:
            if self._stock2 < self.STOCK_LIMIT2:
                return self.STOCK_FAKE
            return self._stock2
        return self._stock1

class G2G(BaseGSheetModel):
    G2G_CHECK: Annotated[int, "AR"]
    G2G_PROFIT: Annotated[float, "AS"]
    G2G_PRODUCT_COMPARE: Annotated[str, "AT"]
    G2G_DELIVERY_TIME: Annotated[int, "AU"]
    G2G_STOCK: Annotated[int, "AV"]
    G2G_MINUNIT: Annotated[int, "AW"]
    G2G_QUYDOIDONVI: Annotated[float, "AX"]
    EXCEPTION1: Annotated[str | None, "AY"] = None
    SELLERNAME1: Annotated[str | None, "AZ"] = None
    G2G_IDSHEET_BLACKLIST: Annotated[str, "BA"]
    G2G_SHEET_BLACKLIST: Annotated[str, "BB"]
    G2G_CELL_BLACKLIST: Annotated[str, "BC"]

    def get_blacklist(
        self,
        gsheet: GSheet,
    ) -> list[str]:
        sheet = Sheet.from_sheet_id(
            gsheet,
            self.G2G_IDSHEET_BLACKLIST,
        )
        worksheet = sheet.open_worksheet(
            worksheet_name=self.G2G_SHEET_BLACKLIST,
        )
        query_values = worksheet.batch_get([self.G2G_CELL_BLACKLIST])[0]
        blacklist = [item for sublist in query_values for item in sublist]
        return blacklist


class FUN(BaseGSheetModel):
    FUN_CHECK: Annotated[int, "BD"]
    FUN_PROFIT: Annotated[float, "BE"]
    FUN_DISCOUNTFEE: Annotated[float, "BF"]
    FUN_PRODUCT_COMPARE: Annotated[str, "BG"]
    NAME2: Annotated[str | None, "BH"] = None
    FUN_FILTER21: Annotated[str | None, "BI"] = None
    FUN_FILTER22: Annotated[str | None, "BJ"] = None
    FUN_FILTER23: Annotated[str | None, "BK"] = None
    FUN_FILTER24: Annotated[str | None, "BL"] = None
    FUN_QUYDOIDONVI: Annotated[float, "BM"] = None
    PRICE2: Annotated[str | None, "BN"] = None
    FACTION2: Annotated[str | None, "BO"] = None
    FUN_STOCK: Annotated[int, "BP"]
    FUN_IDSHEET_BLACKLIST: Annotated[str, "BQ"]
    FUN_SHEET_BLACKLIST: Annotated[str, "BR"]
    FUN_CELL_BLACKLIST: Annotated[str, "BS"]

    def get_blacklist(self, gsheet: GSheet) -> list[str]:
        sheet = Sheet.from_sheet_id(gsheet, self.FUN_IDSHEET_BLACKLIST)
        worksheet = sheet.open_worksheet(self.FUN_SHEET_BLACKLIST)
        query_values = worksheet.batch_get([self.FUN_CELL_BLACKLIST])[0]
        blacklist = [item for sublist in query_values for item in sublist]
        return blacklist


class BIJ(BaseGSheetModel):
    BIJ_CHECK: Annotated[int, "BT"]
    BIJ_PROFIT: Annotated[float, "BU"]
    BIJ_NAME: Annotated[str, "BV"]
    BIJ_SERVER: Annotated[str, "BW"]
    BIJ_DELIVERY_METHOD: Annotated[str, "BX"]
    BIJ_STOCKMIN: Annotated[int, "BY"]
    BIJ_STOCKMAX: Annotated[int, "BZ"]
    HESONHANDONGIA3: Annotated[float | None, "CA"] = None
    BIJ_IDSHEET_BLACKLIST: Annotated[str | None, "CB"] = None
    BIJ_SHEET_BLACKLIST: Annotated[str | None, "CC"] = None
    BIJ_CELL_BLACKLIST: Annotated[str | None, "CD"] = None

    def get_blacklist(self, gsheet: GSheet) -> list[str]:
        sheet = Sheet.from_sheet_id(gsheet, self.BIJ_IDSHEET_BLACKLIST)
        worksheet = sheet.open_worksheet(self.BIJ_SHEET_BLACKLIST)
        query_values = worksheet.batch_get([self.BIJ_CELL_BLACKLIST])[0]
        blacklist = [item for sublist in query_values for item in sublist]
        return blacklist


class ExtraInfor(BaseGSheetModel):
    MIN_UNIT_PER_ORDER: Annotated[int, "CE"]
    VALUE_FOR_DISCOUNT: Annotated[str | None, "CF"] = ""
    DISCOUNT: Annotated[str | None, "CG"] = ""
    DELIVERY_GUARANTEE: Annotated[int, "CH"]
