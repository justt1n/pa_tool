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
    CHECK: Annotated[int, "A"]
    Product_name: Annotated[str, "B"]
    Note: Annotated[str | None, "C"] = None
    Last_Update: Annotated[str | None, "D"] = None
    Product_link: Annotated[str, "E"]
    PRODUCT_COMPARE: Annotated[str, "F"]
    TITLE: Annotated[str, "G"]
    DESCRIPTION: Annotated[str, "H"]
    DURATION: Annotated[str, "I"]
    DONGIAGIAM_MIN: Annotated[float, "J"]
    DONGIAGIAM_MAX: Annotated[float, "K"]
    DONGIA_LAMTRON: Annotated[int, "L"]
    EXCLUDE_ADS: Annotated[int, "M"]
    DELIVERY_TIME: Annotated[str, "N"]
    FEEDBACK: Annotated[int, "O"]
    MIN_UNIT: Annotated[int, "P"]
    MINSTOCK: Annotated[int, "Q"]
    IDSHEET_MIN: Annotated[str, "R"]
    SHEET_MIN: Annotated[str, "S"]
    CELL_MIN: Annotated[str, "T"]
    IDSHEET_MIN2: Annotated[str, "U"]
    SHEET_MIN2: Annotated[str, "V"]
    CELL_MIN2: Annotated[str, "W"]
    DELIVERY0: Annotated[str, "X"]
    DELIVERY1: Annotated[str, "Y"]
    STOCKREAD: Annotated[int, "Z"]
    IDSHEET_MAX: Annotated[str, "AA"]
    SHEET_MAX: Annotated[str, "AB"]
    CELL_MAX: Annotated[str, "AC"]
    IDSHEET_MAX2: Annotated[str, "AD"]
    SHEET_MAX2: Annotated[str, "AE"]
    CELL_MAX2: Annotated[str, "AF"]

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
    IDSHEET_STOCK: Annotated[str, "AD"]
    SHEET_STOCK: Annotated[str, "AE"]
    CELL_STOCK: Annotated[str, "AF"]
    IDSHEET_STOCK2: Annotated[str, "AG"]
    SHEET_STOCK2: Annotated[str, "AH"]
    CELL_STOCK2: Annotated[str, "AI"]
    STOCK_LIMIT: Annotated[int, "AJ"]
    STOCK_LIMIT2: Annotated[int, "AK"]
    STOCK_MAX: Annotated[int | None, "AL"] = None
    STOCK_FAKE: Annotated[int | None, "AM"] = None

    def stock_1(
        self,
        gsheet: GSheet,
    ) -> int:
        sheet = Sheet.from_sheet_id(gsheet, self.IDSHEET_STOCK)
        worksheet = sheet.open_worksheet(self.SHEET_STOCK)
        cell_value = worksheet.batch_get([self.CELL_STOCK])[0]
        try:
            return int(cell_value.first())  # type: ignore
        except Exception as e:
            print(e)
            return 0

    def stock_2(
        self,
        gsheet: GSheet,
    ) -> int:
        sheet = Sheet.from_sheet_id(gsheet, self.IDSHEET_STOCK2)
        worksheet = sheet.open_worksheet(self.SHEET_STOCK2)
        cell_value = worksheet.batch_get([self.CELL_STOCK2])[0]
        try:
            return int(cell_value.first())  # type: ignore
        except Exception as e:
            print(e)
            return 0


class G2G(BaseGSheetModel):
    G2G_CHECK: Annotated[int, "AN"]
    G2G_PROFIT: Annotated[float, "AO"]
    G2G_PRODUCT_COMPARE: Annotated[str, "AP"]
    G2G_DELIVERY_TIME: Annotated[int, "AQ"]
    G2G_STOCK: Annotated[int, "AR"]
    G2G_MINUNIT: Annotated[int, "AS"]
    G2G_QUYDOIDONVI: Annotated[float, "AT"]
    EXCEPTION1: Annotated[str | None, "AU"] = None
    SELLERNAME1: Annotated[str | None, "AV"] = None
    G2G_IDSHEET_BLACKLIST: Annotated[str, "AW"]
    G2G_SHEET_BLACKLIST: Annotated[str, "AX"]
    G2G_CELL_BLACKLIST: Annotated[str, "AY"]

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
        blacklist = []
        for value in query_values:
            blacklist.append(value[0])
        return blacklist


class FUN(BaseGSheetModel):
    FUN_CHECK: Annotated[int, "AZ"]
    FUN_PROFIT: Annotated[float, "BA"]
    FUN_DISCOUNTFEE: Annotated[float, "BB"]
    FUN_PRODUCT_COMPARE: Annotated[str, "BC"]
    NAME2: Annotated[str | None, "BD"] = None
    FUN_FILTER21: Annotated[str | None, "BE"] = None
    FUN_FILTER22: Annotated[str | None, "BF"] = None
    FUN_FILTER23: Annotated[str | None, "BG"] = None
    FUN_FILTER24: Annotated[str | None, "BH"] = None
    PRICE2: Annotated[str | None, "BI"] = None
    FACTION2: Annotated[str | None, "BJ"] = None
    FUN_STOCK: Annotated[int, "BK"]
    FUN_IDSHEET_BLACKLIST: Annotated[str, "BL"]
    FUN_SHEET_BLACKLIST: Annotated[str, "BM"]
    FUN_CELL_BLACKLIST: Annotated[str, "BN"]

    def get_blacklist(self, gsheet: GSheet) -> list[str]:
        sheet = Sheet.from_sheet_id(gsheet, self.FUN_IDSHEET_BLACKLIST)
        worksheet = sheet.open_worksheet(self.FUN_SHEET_BLACKLIST)
        query_values = worksheet.batch_get([self.FUN_CELL_BLACKLIST])[0]
        blacklist = []
        for value in query_values:
            blacklist.append(value[0])
        return blacklist


class BIJ(BaseGSheetModel):
    BIJ_CHECK: Annotated[int, "BO"]
    BIJ_PROFIT: Annotated[float, "BP"]
    BIJ_NAME: Annotated[str, "BQ"]
    BIJ_SERVER: Annotated[str, "BR"]
    BIJ_DELIVERY_METHOD: Annotated[str, "BS"]
    BIJ_STOCKMIN: Annotated[int, "BT"]
    BIJ_STOCKMAX: Annotated[int, "BU"]
    HESONHANDONGIA3: Annotated[float | None, "BV"] = None
