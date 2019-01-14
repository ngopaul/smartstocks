
import sys
import re
import time
import os
import pandas as pd
from math import isnan
from pathlib import Path
from tabulate import tabulate
from bs4 import BeautifulSoup
from selenium import webdriver
from datetime import datetime, timedelta, date
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

""" Converts a MM/DD/YYYY string to a DateTime. """
def strDateToDatetime(mmddyy):
    [month, day, year] = map(lambda x : int(x), mmddyy.split('/'))
    return datetime(year, month, day)

""" Converts a DateTime object to a MM/DD/YYYY form. """
def datetimeToSimpleDate(dt):
    return dt.strftime("%m/%d/%Y")

""" Waits for the NASDAQ database to load. """
def wait_to_load(browser, max_time):
    count = 0
    while 'style="opacity: 0.5;"' in browser.page_source:
        time.sleep(0.5)
        count += 0.5
        if count >= max_time:
            return False
    return True

""" Returns if string is of the form XX:XX. """
def matches_time(text):
    if len(text) == 5 and text[2] == ':':
        return True
    return False

convertUTFWindowsData = pd.read_csv('UTF-8-Windows-1252.csv')

""" Converts Windows-1252 (or ISO 8859-1) wrongly encoded string back to UTF-8. """
def reencodeUTF(text):
    for row in convertUTFWindowsData.itertuples(index=True, name='Pandas'):
        text = text.replace(getattr(row, "Actual"), getattr(row, "Expected"))
    return text