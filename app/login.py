import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.selenium_util import SeleniumUtil


def login(
        _browser: SeleniumUtil,
        isHaveItem: bool = False,
) -> None:
    _browser.get(
        "https://www.playerauctions.com/wow-classic-gold/?Serverid=13563&Quantity=6000&PageIndex=1"
    )
    _browser.click_by_inner_text("LOG IN")

    username_tag = _browser.driver.find_element(By.ID, "username")
    username_tag.send_keys(os.getenv("PA_USERNAME"))

    pass_tag = _browser.driver.find_element(By.ID, "password")
    pass_tag.send_keys(os.getenv("PA_PASSWORD"))

    inner_text = " LOG IN "  # Replace with the desired text
    _browser.click_by_inner_text(inner_text)
    while True:
        try:
            print(
                _browser.driver.execute_script(
                    """
            var response = grecaptcha.getResponse();
            response.length
        """
                )
            )
            time.sleep(3)
        except Exception:
            break
    ### upload currency file
    _browser.get(
        "https://me.playerauctions.com/member/batchoffer/?menutype=offer&menusubtype=currencybulkoffertool"
    )

    file_path = os.path.abspath("storage/output/new_currency_file.xlsx")

    file_input = WebDriverWait(_browser.driver, 10).until(
        EC.presence_of_element_located((By.ID, "FileUpload1"))
    )
    # Upload the file using the absolute path
    file_input.send_keys(file_path)

    # Optionally, you can click the "BROWSE FILES" button if needed
    browse_button = _browser.driver.find_element(By.ID, "ckAgreePa")
    browse_button.click()
    _browser.click_by_inner_text("UPLOAD")
    ### end upload currency file

    if isHaveItem:
        ### upload item file
        _browser.get(
            "https://me.playerauctions.com/member/itemsbulkupload/?menutype=offer&menusubtype=itembulkoffertool"
        )

        file_path = os.path.abspath("storage/output/new_item_file.xlsx")

        file_input = WebDriverWait(_browser.driver, 10).until(
            EC.presence_of_element_located((By.ID, "FileUpload1"))
        )
        # Upload the file using the absolute path
        file_input.send_keys(file_path)

        # Optionally, you can click the "BROWSE FILES" button if needed
        browse_button = _browser.driver.find_element(By.ID, "ckAgreePa")
        browse_button.click()
        _browser.click_by_inner_text("UPLOAD")
        ### end upload item file

    time.sleep(15)
    _browser.close()


if __name__ == "__main__":
    browser = SeleniumUtil()
    login(browser)
