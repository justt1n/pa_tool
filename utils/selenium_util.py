import pathlib

from selenium import webdriver
from selenium.webdriver.common.by import By

PATH_TO_EXTENSION = pathlib.Path(__file__).parent.parent.joinpath(
    "extensions/rektcaptcha"
)


class SeleniumUtil:
    def __init__(self):
        chrome_options = webdriver.ChromeOptions()

        chrome_options.add_argument(f"load-extension={PATH_TO_EXTENSION}")

        self.driver = webdriver.Chrome(options=chrome_options)

    def get(
        self,
        url: str,
    ) -> None:
        self.driver.get(url)

    def click_by_inner_text(
        self,
        txt: str,
    ) -> None:
        element = self.driver.find_element(By.XPATH, f"//*[text()='{txt}']")
        element.click()
