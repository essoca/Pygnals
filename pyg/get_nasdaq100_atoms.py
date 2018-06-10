
from urllib.request import urlopen
from bs4 import BeautifulSoup
from os import mkdir, getcwd
from os.path import exists, join
import pandas as pd

site_wiki = "https://en.wikipedia.org/wiki/NASDAQ-100"
data_dir = join(getcwd(),'data/')

if not exists(data_dir):
    mkdir(data_dir)
    
source_page = urlopen(site_wiki).read()
soup = BeautifulSoup(source_page, 'html.parser')
olist = soup.find("div", { "class" : "div-col columns column-count column-count-3" })
    
# Retreive the symbols in the ordered list
tickers = []
atoms = olist.findAll('li')
for atom in atoms:
    comp = atom.getText()
    if comp:        
        tickers += [str(comp[comp.index("(") + 1:comp.rindex(")")])]

# Retrieve all companies from Nasdaq webpage
site_nasdaq = "http://www.nasdaq.com/screening/companies-by-industry." +\
              "aspx?exchange=NASDAQ&render=download"
companies = urlopen(site_nasdaq)              
all_comps = pd.read_csv(companies,\
            usecols=['Symbol','Name','Sector','Industry'],index_col='Symbol')         
# Select only the companies in the nasdaq100 index
nasdaq100_comps = all_comps.loc[tickers].dropna()
nasdaq100_comps.index.names = ['Ticker']      
nasdaq100_comps.to_csv(data_dir+'nasdaq100/nasdaq100_atoms.csv')
