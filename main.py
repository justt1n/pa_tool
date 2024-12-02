import os

from dotenv import load_dotenv

from utils.ggsheet import GSheet, Sheet
from utils.logger import setup_logging
from utils.sheet_operator import query_multi_model_from_worksheet

### SETUP ###
load_dotenv('settings.env')

setup_logging()
gs = GSheet()


### FUNCTIONS ###


def process():
    print('process')
    sheet = Sheet.from_sheet_id(
        gsheet=gs,
        sheet_id=os.getenv("SPREADSHEET_ID"),
    )
    worksheet = sheet.open_worksheet(os.getenv("SHEET_NAME"))
    start_row = os.getenv("START_ROW")
    query_multi_model_from_worksheet(worksheet, start_row)



### MAIN ###

if __name__ == '__main__':
    process()
