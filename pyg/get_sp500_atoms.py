
from urllib.request import urlopen
from bs4 import BeautifulSoup
import csv
from os import mkdir, getcwd
from os.path import exists, join

site = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
data_dir = join(getcwd(),'data/')

if not exists(data_dir):
    mkdir(data_dir)
    
source_page = urlopen(site).read()
soup = BeautifulSoup(source_page, 'html.parser')
table = soup.find("table", { "class" : "wikitable sortable" })

# Fail now if we haven't found the right table
header = table.findAll('th')
if header[0].string != "Ticker symbol" or header[1].string != "Security":
    raise Exception("Can't parse wikipedia's table!")

# Retreive the values in the table
records = []
rows = table.findAll('tr')
for row in rows:
    fields = row.findAll('td')
    if fields:
        ticker = fields[0].string
        name = fields[1].string
        sector = fields[3].string
        subsector = fields[4].string
        records.append([ticker, name, sector, subsector])

header = ['Ticker', 'Name', 'Sector', 'Subsector']
writer = csv.writer(open(data_dir+'sp500/sp500_atoms.csv', 'w'), lineterminator='\n')
writer.writerow(header)
# Sorting ensure easy tracking of modifications
records.sort(key=lambda s: s[1].lower())
writer.writerows(records)    
