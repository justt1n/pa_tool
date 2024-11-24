from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
from typing import Annotated


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
    DONGIAGIAM_MIN: Annotated[float, "G"]
    DONGIAGIAM_MAX: Annotated[float, "H"]
    DONGIA_LAMTRON: Annotated[int, "I"]
    EXCLUDE_ADS: Annotated[int, "J"]
    DELIVERY_TIME: Annotated[str, "K"]
    FEEDBACK: Annotated[int, "L"]
    MIN_UNIT: Annotated[int, "M"]
    MINSTOCK: Annotated[int, "N"]
    IDSHEET_MIN: Annotated[str, "O"]
    SHEET_MIN: Annotated[str, "P"]
    CELL_MIN: Annotated[str, "Q"]
    IDSHEET_MIN2: Annotated[str, "R"]
    SHEET_MIN2: Annotated[str, "S"]
    CELL_MIN2: Annotated[str, "T"]
    DELIVERY0: Annotated[str, "U"]
    DELIVERY1: Annotated[str, "V"]
    STOCKREAD: Annotated[int, "W"]
    IDSHEET_MAX: Annotated[str, "X"]
    SHEET_MAX: Annotated[str, "Y"]
    CELL_MAX: Annotated[str, "Z"]


class StockInfo(BaseGSheetModel):
    IDSHEET_STOCK: Annotated[str, "AA"]
    SHEET_STOCK: Annotated[str, "AB"]
    CELL_STOCK: Annotated[str, "AC"]
    IDSHEET_STOCK2: Annotated[str, "AD"]
    SHEET_STOCK2: Annotated[str, "AE"]
    CELL_STOCK2: Annotated[str, "AF"]
    STOCK_LIMIT: Annotated[int | None, "AG"] = None
    STOCK_LIMIT2: Annotated[int | None, "AH"] = None
    STOCK_MAX: Annotated[int | None, "AI"] = None
    STOCK_FAKE: Annotated[int | None, "AJ"] = None


class G2G(BaseGSheetModel):
    G2G_CHECK: Annotated[int, "AK"]
    G2G_PROFIT: Annotated[float, "AL"]
    G2G_PRODUCT_COMPARE: Annotated[str, "AM"]
    G2G_DELIVERY_TIME: Annotated[int, "AN"]
    G2G_STOCK: Annotated[int, "AO"]
    G2G_MINUNIT: Annotated[int, "AP"]
    G2G_QUYDOIDONVI: Annotated[float, "AQ"]
    EXCEPTION1: Annotated[str | None, "AR"] = None
    SELLERNAME1: Annotated[str | None, "AS"] = None
    G2G_IDSHEET_BLACKLIST: Annotated[str, "AT"]
    G2G_SHEET_BLACKLIST: Annotated[str, "AU"]
    G2G_CELL_BLACKLIST: Annotated[str, "AV"]


class FUN(BaseGSheetModel):
    FUN_CHECK: Annotated[int, "AW"]
    FUN_PROFIT: Annotated[float, "AX"]
    FUN_DISCOUNTFEE: Annotated[float, "AY"]
    FUN_PRODUCT_COMPARE: Annotated[str, "AZ"]
    NAME2: Annotated[str | None, "BA"] = None
    FUN_FILTER21: Annotated[str | None, "BB"] = None
    FUN_FILTER22: Annotated[str | None, "BC"] = None
    FUN_FILTER23: Annotated[str | None, "BD"] = None
    FUN_FILTER24: Annotated[str | None, "BE"] = None
    PRICE2: Annotated[str | None, "BF"] = None
    FACTION2: Annotated[str | None, "BG"] = None
    FUN_STOCK: Annotated[int | None, "BH"] = None
    FUN_IDSHEET_BLACKLIST: Annotated[str, "BI"]
    FUN_SHEET_BLACKLIST: Annotated[str, "BJ"]
    FUN_CELL_BLACKLIST: Annotated[str, "BK"]


class BIJ(BaseGSheetModel):
    BIJ_CHECK: Annotated[int, "BL"]
    BIJ_PROFIT: Annotated[float, "BM"]
    BIJ_NAME: Annotated[str, "BN"]
    BIJ_SERVER: Annotated[str, "BO"]
    BIJ_DELIVERY_METHOD: Annotated[str, "BP"]
    BIJ_STOCKMIN: Annotated[int, "BQ"]
    BIJ_STOCKMAX: Annotated[int, "BR"]
    HESONHANDONGIA3: Annotated[float | None, "BS"] = None
