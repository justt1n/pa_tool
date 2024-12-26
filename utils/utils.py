import os

def getCNYRate(gs) -> float:
    try:
        _rate_sheet = os.getenv("CNY_RATE_SPREADSHEET_ID")
        _rate_worksheet = os.getenv("CNY_RATE_SHEET_NAME")
        _cell = os.getenv("CNY_RATE_CELL")
        return gs.load_cell_value(_rate_sheet, _rate_worksheet, _cell)
    except Exception as e:
        print(f"Error reading CNY rate: {e}")
        return 1