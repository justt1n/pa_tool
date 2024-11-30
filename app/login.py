import time
from selenium.webdriver.common.by import By

from utils.selenium_util import SeleniumUtil


def login(
    browser: SeleniumUtil,
) -> None:
    browser.get(
        "https://www.playerauctions.com/wow-classic-gold/?Serverid=13563&Quantity=6000&PageIndex=1"
    )

    browser.click_by_inner_text("LOG IN")

    username_tag = browser.driver.find_element(By.ID, "username")
    username_tag.send_keys("")

    pass_tag = browser.driver.find_element(By.ID, "password")
    pass_tag.send_keys("")

    inner_text = " LOG IN "  # Replace with the desired text
    browser.click_by_inner_text(inner_text)
    while True:
        try:
            print(
                browser.driver.execute_script(
                    """
            var response = grecaptcha.getResponse();
            response.length
        """
                )
            )
            time.sleep(3)
        except Exception:
            break

    browser.get(
        "https://me.playerauctions.com/member/batchoffer/?menutype=offer&menusubtype=currencybulkoffertool"
    )
