# importing the required libraries

from bs4 import BeautifulSoup as bs
import requests
import asyncio
import aiohttp
import time
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator
import matplotlib.ticker as mticker
from datetime import datetime

# creating a list of URLs for the program to scrape
urls = []
for page_number in range(1, 150):
    url_start = 'https://www.centralcharts.com/en/price-list-ranking/'
    url_end = 'ALL/asc/ts_19-us-nasdaq-stocks--qc_1-alphabetical-order?p='
    url = url_start + url_end + str(page_number)
    urls.append(url)
print('Collected all urls!')

# creating a couple asynchronous functions to help speed up our request process
async def fetch_page(session, url):
    print('I sent a request to the server')
    async with session.get(url) as response:
        print('I received a response from the server!')
        return await response.text()
        # Return the response to the calling function below

async def scrape_multiple_pages(urls):
    async with aiohttp.ClientSession() as session:

        print('Now that I have all the urls, I will create a list of tasks')
        tasks = [asyncio.create_task(fetch_page(session, url)) for url in urls]
        # Sends the task list to the 'fetch_page' function
        print('I created my list of tasks')

        # Returns a list of the results of each task and saves it as 'pages'
        pages = await asyncio.gather(*tasks)
        print("I received all the results from the 'fetch_page' function")
        # Take the results and exit this function
        return pages

# For performance analysis purposes
start_time = time.time()

pages = asyncio.run(scrape_multiple_pages(urls))

# parsing the HTML data that was returned from the server. Making a list of the headers for the stock table
new_list = ''.join(pages)
soup = bs(new_list, 'html.parser')
tables = soup.find_all('table')

header_tag_list = tables[0].find_all('th')
header_list = []
for tag in header_tag_list[0:7]:
    title = tag.text
    header_list.append(title)

top_list = []
for table in tables:
    rows = table.find_all('tr')

    # for each row except the header row
    for row in rows[1:]:
        row_list = []
        cells = row.find_all('td')
        # one list per row, each list containing the td tags for that row

        for cell in cells[0:7]:
            new_value = cell.text.strip()
            row_list.append(new_value)
        top_list.append(row_list)

# Data Frames and Data Cleanup

# Convert the lists into a dataframe
stock_df = pd.DataFrame(top_list, columns=(header_list))

# Change the data type to string
stock_df[['Financial instrument', 'Current price', 'Change(%)', 'Open','High', 'Low']] = \
    stock_df[['Financial instrument', 'Current price', 'Change(%)', 'Open', 'High', 'Low']] \
    .astype(str)

# Clean up the data
stock_df.replace({'Current price': {',':'', '-':'1'},
                  'Change(%)': {',':'', '-':'1', '%':''},
                  'Open': {',':'', '-':'1'},
                  'High': {',':'', '-':'1'},
                  'Low': {',':'', '-':'1'},
                  'Volume': {',':'', '-':'1'}
}, regex=True, inplace=True)

# Convert the data type back to numeric
stock_df[['Current price', 'Change(%)', 'Open', 'High', 'Low', 'Volume']] = \
    stock_df[['Current price', 'Change(%)', 'Open', 'High', 'Low', 'Volume']]. \
    apply(pd.to_numeric)

# Export the dataframe to a csv file.
stock_df.to_csv('stock_data.csv', index=False)

# Plotting

# Now, we will sort the data by volume and create a bar plot using the Matplotlib library.
stock_df = stock_df.sort_values(by=['Volume'], ascending=False)
top_10_stock_df = stock_df.head(10)
names = top_10_stock_df['Financial instrument']
volumes = top_10_stock_df['Volume']

fig = plt.figure()
ax = plt.subplot()
bar_plot = ax.barh(names, volumes, color='green')
container = ax.containers[0]
ax.bar_label(container, labels=[f'{x:,.0f}' for x in container.datavalues],
    fontsize=6, padding=3)
current_volumes = plt.gca().get_xticks()
ax.xaxis.set_major_locator(mticker.FixedLocator(current_volumes))
plt.gca().set_xticklabels([f'{x:,.0f}' for x in current_volumes], rotation=45)

ax.set_xlabel('Trading Volume')
ax.set_ylabel('Company Name')
now = datetime.now()
todays_date = now.strftime('%m/%d/%y')
ax.set_title('10 Top NASDAQ Stocks by Volume for ' + todays_date)
plt.tight_layout()
ax.set_xmargin(0.2)
ax.xaxis.set_minor_locator(MultipleLocator(2500000))
ax.grid(which='major', axis='x', color='lightgrey', linestyle='-', linewidth='1')

print("--- %s seconds ---" % (time.time() - start_time))

plt.show()