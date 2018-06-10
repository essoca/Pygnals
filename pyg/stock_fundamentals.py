
from urllib.request import urlopen
import csv
from datetime import datetime
from pytz import timezone
from bs4 import BeautifulSoup
import pandas as pd
from os import getcwd
from os.path import join

data_dir = join(getcwd(),'data/')

def correctToBillions(item):
    """Remove M/B from data when necessary"""
    if item.endswith('M'):
        return float(item[:-1]) / 1000
    elif item.endswith('B'):
        return item[:-1]
    else:
        return item.replace('N/A','')
        
def todays_date_mmddyy():
    """Returns string mmddyy for today's date"""        
    now = datetime.now(timezone('US/Eastern'))
    yy = str(now.year)[2:4]
    mm = '0'+ str(now.month) if now.month < 10 else str(now.month)
    dd = '0'+ str(now.day) if now.day < 10 else str(now.day)      
    return mm + dd + yy    

def request_fundamentals(stock_index):
    """Get today's stock fundamentals and write them on file
       index = {'sp500','nasdaq100',etc}
    """
    items = [
    ['l1', 'Last Price'],
    ['y', 'Dividend Yield'],
    ['r', 'Price/Earnings'],
    ['e', 'Earnings/Share'],
    ['b4', 'Book Value'],
    ['j', '52 week low'],
    ['k', '52 week high'],
    ['j1', 'Market Cap'],
    ['j4', 'EBITDA'],
    ['p5', 'Price/Sales'],
    ['p6', 'Price/Book'],
    ['f6','Float']
    ]                
    params = ''.join([ x[0] for x in items ])
    url = 'http://download.finance.yahoo.com/d/quotes.csv?'
    #edgar = 'http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK='

    reader = csv.reader(open(data_dir + stock_index +'/'+ stock_index +'_atoms.csv'))
    outrows = [ row for row in reader ]
    symbols = [ row[0] for row in outrows[1:] ]

    #outrows[0] += [ item[1] for item in items ] + ['SEC Filings']
    outrows[0] += [ item[1] for item in items ]
    
    print('Getting fundamentals of stocks in {}'.format(stock_index))
    for idx in range(0,len(symbols),20):
        query = url + 's=' + '+'.join(symbols[idx:idx+20]) + '&f=' + params
        fo = urlopen(query)
        tmpcsv  = csv.reader(fo)
        rows = [ row for row in tmpcsv ]
        for count, row in enumerate(rows):
            realidx = idx + count + 1
            # change n/a to empty cell
            row = [ x.replace('N/A', '') for x in row ]
            # market cap and ebitda have 'B' or 'M' in them sometimes
            row[7] = correctToBillions(row[7])
            row[8] = correctToBillions(row[8])
            # add the edgar link
            #row.append(edgar + symbols[realidx-1])
            outrows[realidx] = outrows[realidx] + row
        #print('Processed: %s rows' % (idx + 20))

    output_dir = data_dir + stock_index + '/' + todays_date_mmddyy() + '/'
    fo = open(output_dir + 'fundm_'+ todays_date_mmddyy() +'.csv', 'w')
    writer = csv.writer(fo, lineterminator='\n')
    writer.writerows(outrows)
    fo.close()

def yahoof_key_statistics_atom(ticker,items_wanted):
    """Scrape items_wanted not in the Yahoo Finance API"""
    
    url = 'https://finance.yahoo.com/quote/'+ticker+'/key-statistics?p='+ticker
    source_page = urlopen(url).read().decode()
    soup = BeautifulSoup(source_page, 'html.parser')
    tables = soup.findAll("table", { "class" : "table-qsp-stats Mt(10px)" })
    
    record = []
    for table in tables:
        rows = table.findAll('tr')
        for row in rows:
            value = row.findAll('td')
            item = row.findAll('span')            
            if item[0].string in items_wanted:
                record.append(correctToBillions(value[1].string))                 
    return record            

def yahoof_key_statistics(stock_index):
    """Get today's fundamentals from Yahoo Finance Key Statistics"""
    
    tickers = pd.read_csv(data_dir + stock_index +'/'+ stock_index +'_atoms.csv',\
                          usecols=['Ticker'])
    tickers = tickers['Ticker'].values.tolist()
    
    tags_items_wanted = [
                         'vm1',
                         'vm3',
                         'vm4',
                         'vm5',
                         'vm6',
                         'vm7',
                         'me1',
                         'me2',
                         'is5',
                         'bs4',
                         'bs6',
                         'ph1',
                         'ph4',
                         'ph5',
                         'ph6',
                         'ss4',
                         'ds6',
                         'ds7',
                         'ds8',
                         'ds9',
                         'ds10'
                        ]
    from yahoof_api_items import items_key_stat
    items_wanted = [items_key_stat[x] for x in tags_items_wanted]
    date = todays_date_mmddyy()
    output_dir = data_dir + stock_index +'/'+ date +'/'
    pd.DataFrame(columns= ['Ticker'] + items_wanted).\
                    to_csv(output_dir+'fundm_'+date+'.csv')
    for k, ticker in enumerate(tickers):
        print('Getting fundamentals for {}'.format(ticker))
        row = yahoof_key_statistics_atom(ticker,items_wanted)    
        pd.DataFrame([ [k] + [ticker] + row ]).set_index(0).\
                    to_csv(output_dir+'fundm_'+date+'.csv',mode='a',header=False)
    
#yahoof_key_statistics('nasdaq100')
    
    
    
    