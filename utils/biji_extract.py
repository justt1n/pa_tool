import codecs
import json
import logging
import os
import platform
import time
import zipfile
from datetime import datetime

import gspread
import wget
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

## Retry functions

def get_cell_text(cell, retries=3):
    for _ in range(retries):
        try:
            return cell.text
        except StaleElementReferenceException:
            time.sleep(0.25)
    raise StaleElementReferenceException("Failed to get cell text after retries")


def get_row_elements(row, retries=3):
    while retries > 0:
        try:
            return row.find_elements(By.TAG_NAME, 'td')
        except StaleElementReferenceException:
            retries -= 1
            if retries == 0:
                raise
            time.sleep(0.25)


def find_link_element(cell, retries=3):
    for _ in range(retries):
        try:
            return cell.find_elements(By.TAG_NAME, 'a')[1]
        except StaleElementReferenceException:
            time.sleep(0.25)
    raise StaleElementReferenceException("Failed to find link element after retries")


def get_link_attribute(link_element, attribute='href', retries=3):
    for _ in range(retries):
        try:
            return link_element.get_attribute(attribute)
        except StaleElementReferenceException:
            time.sleep(0.25)
    raise StaleElementReferenceException(f"Failed to get attribute '{attribute}' after retries")


def get_row_elements_with_retries(row, retries=3):
    for _ in range(retries):
        try:
            return row.find_elements(By.TAG_NAME, 'td')
        except StaleElementReferenceException:
            time.sleep(0.25)
    raise StaleElementReferenceException("Failed to find row elements after retries")


def find_elements_with_retries(parent_element, by, value, retries=3):
    for _ in range(retries):
        try:
            return parent_element.find_elements(by, value)
        except StaleElementReferenceException:
            time.sleep(0.25)
    raise StaleElementReferenceException(f"Failed to find elements by {by}='{value}' after retries")



def get_hostname_by_hostid(data, hostid):
    for entry in data:
        if entry['hostid'] == str(hostid):
            return entry['hostname']
    return None

def extract_data(data):
    data = data
    payloads = []
    for data_row in data:
        data_row[2] = get_hostname_by_hostid(HOST_DATA, data_row[2])
        payloads.append(Payload.Payload(data_row))
    return payloads