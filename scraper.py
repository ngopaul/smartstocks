import sys
import requests
import re
from bs4 import BeautifulSoup
import time
from datetime import datetime
from datetime import timedelta
import os
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import pandas as pd
from tabulate import tabulate
from math import isnan

########################################################################################

got_color = 0
try:
    from colorama import Fore, Back, Style
    # raise Exception("I don't want to use colorama")
    got_color = 1
except:
    print("Use 'pip install colorama' in order to get pretty colors.")

########################################################################################

keyword = 'google'
symbol = 'GOOG'

if __name__ == "__main__":
    keyword = sys.argv[1]
    symbol = sys.argv[2]
else:
    print("Use the first argument to specify a keyword to search for news.\n",
    "Use the second keyword to specify a ticker name, with a . for classes (i.e. BRK.A or BRK.B)\n",
    "Using the default of google and GOOG.")

########################################################################################

# executable included
geckodriver = "browser/geckodriver.exe"
options = webdriver.FirefoxOptions()
# options.add_argument('-headless')

ffprofile = webdriver.FirefoxProfile("browser/profile")
browser = webdriver.Firefox(ffprofile, executable_path=geckodriver, firefox_options=options)

""" Converts a MM/DD/YYYY string to a DateTime. """
def strDateToDatetime(mmddyy):
    [month, day, year] = map(lambda x : int(x), mmddyy.split('/'))
    return datetime(year, month, day)

""" Converts a DateTime object to a MM/DD/YYYY form. """
def datetimeToSimpleDate(dt):
    return dt.strftime("%m/%d/%Y")

""" Converts a positive number to GREEN, a null or 0 to WHITE, and a negative to RED. """
def stockColor(num):
    if num > 0:
        return Fore.GREEN
    if num < 0:
        return Fore.RED
    else:
        return Fore.WHITE

url1 = "https://news.google.com/search?q=" + keyword # + "&hl=en-US&gl=US&ceid=US:en"
url2 = "https://www.nasdaq.com/symbol/" + symbol.lower() + "/historical"

########################################################################################

print("Scraping:", url2)

browser.get(url2)
select = Select(browser.find_element_by_id('ddlTimeFrame'))
select.select_by_value('1y')
time.sleep(2)
browser_data = browser.page_source
soup = BeautifulSoup(browser_data, 'html.parser')

tablecontainer = soup.find_all('div', {'id' : 'historicalContainer'})[0]
table = tablecontainer.find_all('table')[0]
df = pd.read_html(str(table))[0]
# Fixing some unreadable column names
df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
# Dropping a NAN row
df = df.drop([0], axis=0)
print( tabulate(df, headers='keys', tablefmt='psql') )

latest_date = strDateToDatetime(df.iloc[0, 0])
print("Got latest date:", datetimeToSimpleDate(latest_date))
oldest_date = strDateToDatetime(df.tail(1).iloc[0, 0])
print("Got oldest date:", datetimeToSimpleDate(oldest_date))

########################################################################################

print("Scraping:", url1)

browser.get(url1)
browser_data = browser.page_source
soup = BeautifulSoup(browser_data, 'html.parser')

# Gets title, description, and date in the current timezone
for article in soup.find_all('div', {'class' : 'xrnccd'}):
    title = article.find_all('span')[0].text.strip()
    description = article.find_all('p', {'class' : 'HO8did Baotjf'})[0].text.strip()
    date = datetime.fromtimestamp(int(
        re.search(
            '(?<=(datetime="seconds: ))(\d)+', 
            str(article.find_all('time')[0]))
            .group(0)))
    
    # Get start stock value. Assume if, upon not having the date in the df, going back will always find a valid date before the oldest time.
    daysBack = 0
    gotStart = False
    while not gotStart:
        articleDatemmddyy = datetimeToSimpleDate(date - timedelta(days=daysBack))
        try:
            stockStartValue = df.loc[df['Date'] == articleDatemmddyy].iloc[0, 1]
            gotStart = True
        except:
            daysBack += 1

    # Calculate 1 day change, 3 day change, 1 week change
    after1day = float('nan')
    after3day = float('nan')
    after1week = float('nan')
    currentdate = date + timedelta(days=0)
    daysCounted = 0
    while currentdate < latest_date:
        if not isnan(after1day) and not isnan(after3day) and not isnan(after1week):
            break
        daysCounted += 1
        currentdate += timedelta(days=1)
        currentDatemmddyy = currentdate.strftime("%m/%d/%Y")
        if daysCounted >= 1 and isnan(after1day):
            try:
                after1day = df.loc[df['Date'] == currentDatemmddyy].iloc[0, 4]
            except:
                pass
        if daysCounted >= 3 and isnan(after3day):
            try:
                after3day = df.loc[df['Date'] == currentDatemmddyy].iloc[0, 4]
            except:
                pass
        if daysCounted > 7 and isnan(after1week):
            try:
                after1week = df.loc[df['Date'] == currentDatemmddyy].iloc[0, 4]
            except:
                pass
    change1day = after1day - float(stockStartValue)
    change3day = after3day - float(stockStartValue)
    change1week = after1week - float(stockStartValue)

    if got_color:
        print(
            Back.WHITE + Fore.BLACK + title, 
            Back.BLACK + Fore.RED + "::", 
            Fore.WHITE + description, 
            Fore.RED + "::", 
            Back.WHITE + Fore.BLUE + date.strftime("%Y-%m-%d %H:%M:%S"),
            Back.BLACK + Fore.RED + "::", 
            "\n",
            stockColor(change1day) + "1D: " + str(change1day),
            Fore.RED + "::", 
            stockColor(change3day) + "3D: " + str(change3day),
            Fore.RED + "::", 
            stockColor(change1week) + "1W: " + str(change1week),
        )
    else:
        print(
            title, 
            "::", 
            description, 
            "::", 
            date.strftime("%Y-%m-%d %H:%M:%S"),
            "::", 
            "\n",
            "1D: " + str(change1day),
            "::", 
            "3D: " + str(change3day),
            "::", 
            "1W: " + str(change1week),
        )
    
    
if not got_color:
    print("Use 'pip install colorama' in order to get pretty colors.")
print("If you see strange symbols and no colors, then use a different terminal - i.e. VS Code doesn't support these colors.")

browser.quit()