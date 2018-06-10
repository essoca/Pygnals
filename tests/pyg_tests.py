# -*- coding: utf-8 -*-

#from nose.tools import *
import os
from os.path import exists, join
from os import mkdir, getcwd
import pandas as pd
from datetime import datetime
from pytz import timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from time import sleep

#=============================================================================
pyg_dir = join(getcwd(),'pyg/')

def load_imports(path):
    """
        Import all modules from pyg_main
    """
    files = os.listdir(path)
    imps = []

    for i in range(len(files)):
        name = files[i].split('.')
        if len(name) > 1:
            if name[1] == 'py' and name[0] != '__init__':
               name = name[0]
               imps.append(name)
               
    file = open(path+'__init__.py','w')
    toWrite = '__all__ = ' + str(imps)
    file.write(toWrite)
    file.close()

load_imports(pyg_dir)    
#from pyg import *
from pyg import order_book as ob
from pyg import vol_processor as vp
from pyg import ret_vol_statistics as vs
from pyg import stock_fundamentals as sf
#=============================================================================

stock_index = 'nasdaq100'      
date = sf.todays_date_mmddyy()
#date = '062917'

# running_time_mins = 5
# now_yhoof = datetime.now(timezone('US/Eastern'))-pd.Timedelta(minutes=15)
# t_max = now_yhoof + pd.Timedelta(minutes=running_time_mins)
#ob.request_vols_and_prices(stock_index,(t_max.hour,t_max.minute))

ob.request_vols_and_prices(stock_index,(16,0))
vp.plot_intraday_vols(stock_index,date)
vs.plot_return_vs_volspread(stock_index,date)
vp.buy_sell_heatmap(stock_index,date)

# for k in [4,5,6,7,8]:
#     date = '042' + str(k) + '17'
#     print("======= Processing data for date {} ========".format(date))
#     # vp.plot_intraday_vols(stock_index,date)
#     # vs.plot_return_vs_volspread(stock_index,date) 
#     vp.buy_sell_heatmap(stock_index,date)

# for k in [6,7,8,9]:
#     date = '060' + str(k) + '17'
#     print("======= Processing data for date {} ========".format(date))
#     # vp.plot_intraday_vols(stock_index,date)
#     # vs.plot_return_vs_volspread(stock_index,date)   
#     vp.buy_sell_heatmap(stock_index,date)

# for k in [14,15,16,19,20,26,27,28,29]:
#     date = '06' + str(k) + '17'
#     print("======= Processing data for date {} ========".format(date))
#     # vp.plot_intraday_vols(stock_index,date)
#     # vs.plot_return_vs_volspread(stock_index,date)   
#     vp.buy_sell_heatmap(stock_index,date)    
