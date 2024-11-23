from selenium.webdriver.chromium import webdriver


class SeleniumUtil:
    def __init__(self):
        self.driver = webdriver.Chrome()

    def get(self, url):
        self.driver.get(url)

    def find_element_by_xpath(self, xpath):
        return self.driver.find_element_by_xpath(xpath)

    def find_elements_by_xpath(self, xpath):
        return self.driver.find_elements_by_xpath(xpath)

    def close(self):
        self.driver.close()

    def quit(self):
        self.driver.quit()