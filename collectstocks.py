import pandas as pd
from bs4 import BeautifulSoup
from tabulate import tabulate
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support import expected_conditions as EC
import time
import sys
import datetime

ticker_info = pd.read_csv('company-symbol/ALL.csv')


# Code taken from https://intoli.com/blog/clear-the-firefox-browser-cache/. Modified a bit to work

# def get_clear_site_data_button(driver):
#     return driver.find_element_by_css_selector('#clearSiteDataButton')


# def get_clear_site_data_confirmation_button(driver):
#     return driver.find_element_by_css_selector('#clearButton')

# def clear_firefox_cache(driver, timeout=10):
#     driver.get('about:preferences#privacy')
#     wait = WebDriverWait(driver, timeout)
#     # Click the "Clear Data..." button under "Cookies and Site Data".
#     wait.until(get_clear_site_data_button)
#     get_clear_site_data_button(driver).click()
#     # Click the confirmation button
#     wait.until(get_clear_site_data_confirmation_button)
#     driver.find_element_by_css_selector('#clearButton').click()
#     # driver.find_element_by_id('clearButton').click()
#     # Accept the confirmation alert.
#     wait.until(EC.alert_is_present())
#     alert = Alert(driver)
#     alert.accept()

################################################################################

""" Converts a DateTime object to a MM/DD/YYYY form. """
def datetimeToSimpleDate(dt):
    return dt.strftime("%m/%d/%Y")

""" Returns if string is of the form XX:XX. """
def matches_time(text):
    if len(text) == 5 and text[2] == ':':
        return True
    return False

def wait_to_load(browser, max_time):
    count = 0
    while 'style="opacity: 0.5;"' in browser.page_source:
        time.sleep(0.5)
        count += 0.5
        if count >= max_time:
            return False
    return True

curr_date = datetimeToSimpleDate(datetime.date.today())

print('Current Date:', curr_date)

# print( tabulate(ticker_info, headers='keys', tablefmt='psql') )

# executable included
geckodriver = "browser/geckodriver.exe"
options = webdriver.FirefoxOptions()
# options.add_argument('-headless')
ffprofile = webdriver.FirefoxProfile("browser/profile")
ffprofile.set_preference('browser.cache.disk.enable', False)
ffprofile.set_preference('browser.cache.memory.enable', False)
ffprofile.set_preference('browser.cache.offline.enable', False)
ffprofile.set_preference('network.cookie.cookieBehavior', 2)
browser = webdriver.Firefox(ffprofile, executable_path=geckodriver, firefox_options=options)

start_index = 0
if __name__ == '__main__':
    try:
        start_index = int(sys.argv[1])
    except:
        pass

for row in ticker_info.itertuples(index=True, name='Pandas'):
    # start at the place where you want to start in the csv
    if getattr(row, "Index") >= start_index:
        # get all the data
        symbol = getattr(row, "Symbol").replace('^', '.').strip()
        name = getattr(row, "Name")
        print("Getting information of:", symbol, ":", name, ": #" + str(getattr(row, "Index")))

        # navigate to site
        url = "https://www.nasdaq.com/symbol/" + symbol.lower() + "/historical"
        error = True
        browser.get(url)

        # select one of these timeframes. If the first takes to long to load, select the next, and on.
        timeframes = ['4y', '5y']
        index = 0
        loaded = False
        while not loaded:
            WebDriverWait(browser, 10).until(lambda s: s.find_element_by_id("ddlTimeFrame").is_displayed())
            select = Select(browser.find_element_by_id('ddlTimeFrame'))
            select.select_by_value(timeframes[index])
            loaded = wait_to_load(browser, 10)
            index = (index + 1) % len(timeframes)
        
        # get the data
        browser_data = browser.page_source
        soup = BeautifulSoup(browser_data, 'html.parser')
        tablecontainer = soup.find_all('div', {'id' : 'historicalContainer'})[0]

        # only if there is a table full of data will this try work
        try:
            table = tablecontainer.find_all('table')[0]

            # read the table into a dataframe
            df = pd.read_html(str(table))[0]

            # Fixing some unreadable column names
            df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']

            # Dropping a NAN row
            df = df.drop([0], axis=0)

            # simplify the data for less storage cost
            simplifieddf = pd.DataFrame([],[],['Date','Avg'])
            simplifieddf['Date'] = df['Date']
            simplifieddf['Avg'] = df[['High','Low']].mean(axis=1)
            filename = symbol + '.csv'

            # if the data has a time value for one of the dates, replace with today's date instead
            if matches_time(simplifieddf.iloc[0, 0]):
                simplifieddf.at['Date', '1'] = curr_date

            simplifieddf.to_csv('collect-stocks/' + filename[0] + '/' + filename)
            now = datetime.datetime.now()
            print("Saved information to:",'collect-stocks/' + filename[0] + '/' + filename, "at", now.strftime("%Y-%m-%d %H:%M"))
        # if there is no data on the website, the table will not exist and an error will be thrown
        except:
            print("There was no data for this stock. Did not save any file.")
