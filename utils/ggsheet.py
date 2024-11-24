import gspread.urls
import gspread.utils
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from typing import Type, Any, TypeVar
from model.sheet_model import BaseGSheetModel
from pydantic import BaseModel

T = TypeVar("T", bound=BaseGSheetModel)


class GSheet:
    client: gspread.client.Client

    def __init__(self, keypath="key.json"):
        self.client = self.__get_gspread(keypath)

    def __get_gspread(self, keypath="key.json"):
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(keypath, scope)  # type: ignore
        client = gspread.auth.authorize(creds)  # type: ignore
        return client

    def get_sheet(
        self,
        sheet_id,
    ) -> gspread.spreadsheet.Spreadsheet:
        return self.client.open_by_key(sheet_id)

    def read_sheet_data(self, sheet_id):
        sheet = self.get_sheet(sheet_id)
        return sheet.sheet1.get_all_values()


class Sheet:
    gsheet: GSheet
    sheet_id: str
    sheet: gspread.spreadsheet.Spreadsheet

    def __init__(
        self,
        gsheet: GSheet,
        sheet_id: str,
    ) -> None:
        self.gsheet = gsheet
        self.sheet_id = sheet_id
        self.sheet = self.gsheet.get_sheet(self.sheet_id)

    def open_worksheet(
        self,
        worksheet_name: str,
    ) -> gspread.worksheet.Worksheet:
        return self.sheet.worksheet(worksheet_name)

    def __call__(self) -> gspread.spreadsheet.Spreadsheet:
        return self.sheet

    @staticmethod
    def extract_sheet_id_from_url(url: str):
        return gspread.utils.extract_id_from_url(url)

    @staticmethod
    def from_url(
        gsheet: GSheet,
        url: str,
    ) -> "Sheet":
        sheet_id = Sheet.extract_sheet_id_from_url(url)
        return Sheet(gsheet, sheet_id)

    @staticmethod
    def from_sheet_id(
        gsheet: GSheet,
        sheet_id: str,
    ) -> "Sheet":
        return Sheet(gsheet, sheet_id)


def query_model_from_worksheet(
    worksheet: gspread.worksheet.Worksheet,
    model: Type[T],
    row_index: list[int],
) -> list[T]:
    cells: list[str] = []
    model_fields = model.fields_exclude_row_index()
    for index in row_index:
        for _, propers in model_fields.items():
            cells.append(
                f"{propers.metadata[0]}{index}",
            )
    query_values = [value.first() for value in worksheet.batch_get(cells)]
    model_list: list[T] = []
    num_of_keys = len(model_fields.keys())
    for i, index in enumerate(row_index):
        model_dict = {}
        for j, model_field_name in enumerate(model_fields.keys()):
            model_dict[model_field_name] = query_values[i * num_of_keys + j]
        _model = model.model_validate(
            model_dict,
        )
        _model.row_index = index
        model_list.append(_model)
    return model_list


def update_model_to_worksheet(
    worksheet: gspread.worksheet.Worksheet,
    models: list[T],
) -> None:
    class UpdateCell(BaseModel):
        range: str
        values: Any

    data = []
    for model in models:
        model_fields = model.fields_exclude_row_index()
        model_dict = model.model_dump(mode="json")
        for field_name, proper in model_fields.items():
            data.append(
                UpdateCell(
                    range=f"{proper.metadata[0]}{model.row_index}",
                    values=[[model_dict[field_name]]],
                ).model_dump()
            )

    worksheet.batch_update(data)
