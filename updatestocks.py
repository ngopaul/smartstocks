from utils import *

curr_date = datetimeToSimpleDate(date.today())
print('Current Date:', curr_date)

if __name__ == '__main__':
    try:
        symbol = sys.argv[1]
        timeframe = sys.argv[2]
    except:
        symbol = 'GOOG'
        timeframe = '5y'

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

# navigate to site for stocks
print("Getting information of:", symbol)
url = "https://www.nasdaq.com/symbol/" + symbol.lower() + "/historical"
error = True
browser.get(url)

# select one of these timeframes. If the first takes to long to load, select the next, and on.
timeframes = [timeframe, '4y', '5y']
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
except:
    print("There was no data for this stock. Did not save any file.")
    exit()

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
now = datetime.now()
print("Saved information to:",'collect-stocks/' + filename[0] + '/' + filename, "at", now.strftime("%Y-%m-%d %H:%M"))
# if there is no data on the website, the table will not exist and an error will be thrown

browser.quit()