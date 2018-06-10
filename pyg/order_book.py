# -*- coding: utf-8 -*-

from urllib.request import urlopen
import pandas as pd
import numpy as np
from datetime import datetime
from pytz import timezone
import time
from os import mkdir, getcwd
from os.path import exists, join
#from pandas.io.data import DataReader
import stock_fundamentals as sf    

data_dir = join(getcwd(),'data/')
    
def parse_data(last_data):
    """
        Parse values of requested intraday data
    """
    # Parsing date and time
    date = list(last_data[0])[1:-1]
    time = list(last_data[1])[1:-1]
    datetime_str = "".join(date + [' '] + time)
    try:
        date_time = datetime.strptime(datetime_str,"%m/%d/%Y %I:%M%p")
        time = pd.to_datetime(date_time).time()
    except ValueError:
        # Some stock has no data today
        time = pd.to_datetime('today').time()
    # Parsing other values
    str2num = lambda x: float(x) if '.' in x else int(x)
    for k in range(len(last_data[2:])):
        if last_data[k+2] == 'N/A':
            last_data[k+2] = float('NaN')
        else:
            last_data[k+2] = str2num(last_data[k+2])
    return [time] + last_data[2:]    
                                    
                                        
def request_vols_and_prices(stock_index,time_max=(16,0)):
    """ Run intraday requests of last bid/ask volumes and prices together with
        the last prices/volumes which were executed. Do this until end of 
        trading by default.
    """
    # Relevant items from order book
    items = [
            ['d1','Date'],
            ['t1','Time'],
            ['b', 'Bid'],
            ['b6', 'Bid Size'],
            ['a', 'Ask'],
            ['a5', 'Ask Size'],
            ['l1', 'Last Price'],
            ['k3', 'Last Size']
            ]
    params = ''.join([ x[0] for x in items ])    
    url = 'http://download.finance.yahoo.com/d/quotes.csv?'    
    
    # Build table headers
    master_dir = data_dir + stock_index
    output_dir = master_dir + '/' + sf.todays_date_mmddyy() + '/'   
    tickers = pd.read_csv(master_dir +'/'+ stock_index + '_atoms.csv',usecols=['Ticker'])        
    tickers = tickers['Ticker'].values.tolist()    
    query = url + "s=" + ",".join(tickers) + "&f=" + params
    if not exists(output_dir):
        mkdir(output_dir)
        obook_dir = output_dir + 'order_book/'
        mkdir(obook_dir)
        cols = [ item[1] for item in items ]
        cols[0] = 'Request Delay'
        cols = ['Total Delay'] + cols
        for ticker in tickers:
            pd.DataFrame(columns=cols).to_csv(obook_dir + ticker +'.csv')
                
    # Append requested last_data to files 'ticker.csv' row by row
    t = 0
    last_time = datetime.now(timezone('US/Eastern'))
    saving_delay = []    
    
    while last_time.hour != time_max[0] or last_time.minute != time_max[1]:        
        start = time.time()  
        # Request of the params in items        
        try:
            page = urlopen(query) 
        except IOError:
            continue
        # Record the request time   
        request_delay = round(time.time()-start,2)
            
        start = time.time()
        last_data = page.read().decode().splitlines()
        last_data = [[request_delay] + parse_data(item.split(",")) \
                            for item in last_data]            
        for k, ticker in enumerate(tickers):     
            #pd.DataFrame([ [t] + last_data[k] ]).set_index(0).\
            pd.DataFrame([ [t] + last_data[k] ]).\
                to_csv(obook_dir + ticker +'.csv',mode='a',header=False) 
            last_time = last_data[0][1]
            print("Successful request at {}".format(str(last_time)[:-3]))                            

        # Record the time taken to save data to disk            
        saving_delay += [ round(time.time()-start,2) ]  
        t += 1 
    # Due to the applied sampling frequency, data will be repeated. Keep only
    # the data representing changes (in last price: iceberg orders?).  
    def cumsum_total_delay(df):
        """Calculate cumulative sum of total delay time (secs) until there is 
           a change of minute in request time. Reset sum when this happens.
        """              
        last_value= 0
        last_min = int(df['Time'].ix[0][3:5])
        newcum = []
        for row in df.iterrows():
            this_value = row[1]['Total Delay'] + last_value
            this_min = int(row[1]['Time'][3:5])
            if this_min != last_min: this_value = 0
            newcum.append(this_value)    
            last_value = this_value
            last_min = this_min
        df.insert(3,'Arrival Time',newcum) 
    
    print('Calculating timestamps of trading events ...')        
    for ticker in tickers:
        df = pd.read_csv(obook_dir + ticker +'.csv')            
        df.insert(3,'Saving Delay',saving_delay)            
        del df['Unnamed: 0']
        df['Total Delay'] = df['Saving Delay'] + df['Request Delay']
        cumsum_total_delay(df)
        df['Time'] = pd.to_datetime(df['Time']) + \
                     pd.to_timedelta(df['Arrival Time'].astype(int),unit='s')
        df['Time'] = df['Time'].dt.time             
        df.drop_duplicates(subset=['Last Price'],inplace=True)
        df.to_csv(obook_dir + ticker +'.csv',mode='w')    
    print('Done.')             

