from oauth2client.service_account import ServiceAccountCredentials
import gspread


def split_sheet_id_from_url(url):
    return url.split('/')[-1]


class GSheet():

    def __init__(self, keypath="key.json"):
        self.client = self.get_gspread(keypath)


    def get_gspread(self, keypath="key.json"):
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(keypath, scope)
        client = gspread.authorize(creds)
        return client
    
    def get_sheet(self, sheet_id):
        return self.client.open(sheet_id)

    def read_sheet_data(self, sheet_id):
        sheet = self.get_sheet(sheet_id)
        return sheet.sheet1.get_all_values()
