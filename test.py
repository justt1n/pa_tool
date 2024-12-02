from dotenv import load_dotenv

from app.login import login
from app.process import run
from utils.selenium_util import SeleniumUtil


def test():
    run()

def test_login():
    browser = SeleniumUtil()
    login(browser)

if __name__ == "__main__":
    load_dotenv('settings.env')
    test_login()