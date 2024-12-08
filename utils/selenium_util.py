import os
import pathlib
import time

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from decorator.retry import retry

PATH_TO_EXTENSION = pathlib.Path(__file__).parent.parent.joinpath(
    "extensions/rektcaptcha"
)


class SeleniumUtil:
    def __init__(self, mode: int):
        _driver_path = ChromeDriverManager().install()
        _chrome_service = Service(executable_path=_driver_path)
        _chrome_options = webdriver.ChromeOptions()
        _retry_time = int(os.getenv("RETRIES_TIME", 5))
        self.driver = None
        if mode == 1:
            _chrome_options.add_argument(f"load-extension={os.getenv('PATH_TO_EXTENSION', PATH_TO_EXTENSION)}")
            for _ in range(_retry_time):
                try:
                    self.driver = webdriver.Chrome(service=_chrome_service, options=_chrome_options)
                    self.driver.maximize_window()
                    break
                except WebDriverException:
                    time.sleep(0.25)
            if self.driver is None:
                raise WebDriverException("Failed to open driver and navigate to URL after retries")
        elif mode == 2:
            _chrome_options.add_argument("--headless")
            _chrome_options.add_argument("--no-sandbox")

            for _ in range(_retry_time):
                try:
                    driver = webdriver.Chrome(service=_chrome_service, options=_chrome_options)
                    self.driver = driver
                    break
                except WebDriverException:
                    time.sleep(0.25)
            if self.driver is None:
                raise WebDriverException("Failed to open driver and navigate to URL after retries")
        else:
            raise ValueError("Invalid mode")

    def get(self, url):
        self.driver.get(url)

    @retry(retries=10, delay=1.5, exception=WebDriverException)
    def click_by_inner_text(self, text):
        element = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{text}')]"))
        )
        element.click()
